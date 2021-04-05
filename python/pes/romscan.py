
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2021 Neil Munday (neil@mundayweb.com)
#
#    PES is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PES is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PES.  If not, see <http://www.gnu.org/licenses/>.
#

import abc
import glob
import json
import logging
import multiprocessing
import os
import pes
import pes.common
import pes.retroachievement
import pes.sql
import PIL
import requests
import sqlalchemy.orm
import time

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QThread

logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class RomTaskResult(object):

	STATE_ADDED = 1
	STATE_UPDATED = 2
	STATE_FAILED = 3

	def __init__(self):
		self.__state = None

	@property
	def state(self) -> int:
		return self.__state

	@state.setter
	def state(self, state: int):
		if state == RomTaskResult.STATE_ADDED or state == RomTaskResult.STATE_UPDATED or state == RomTaskResult.STATE_FAILED:
			self.__state = state
		else:
			raise ValueError("Invalid state: %s" % state)

	def __repr__(self):
		return "<RomTaskResult state=%d >" % self.state

class RomProcess(multiprocessing.Process):

	def __init__(self, processNumber, taskQueue, resultQueue, exitEvent, lock, romList):
		super(RomProcess, self).__init__()
		self.__processNumber = processNumber
		self.__taskQueue = taskQueue
		self.__resultQueue = resultQueue
		self.__exitEvent = exitEvent
		self.__lock = lock
		self.__romList = romList

	def run(self):

		result = None
		while True:
			task = self.__taskQueue.get()
			if task is None:
				logging.debug("%s: exiting..." % self.name)
				self.__taskQueue.task_done()
				break
			if self.__exitEvent.is_set():
				self.__taskQueue.task_done()
			else:
				task.setLock(self.__lock)
				try:
					result = task.run(self.__processNumber)
					#if not self.__exitEvent.is_set():
					#	self.__romList.append((result[2], result[3]))
					#	self.__romList.append(result)
				except Exception as e:
					logging.error("%s: Failed to process task due to the following error:" % self.name)
					logging.error(e)
				self.__taskQueue.task_done()
		if result:
			self.__resultQueue.put(result)
		self.__resultQueue.close()

class RomTask(abc.ABC):

	SCALE_WIDTH = 400.0
	IMG_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
	URL_TIMEOUT = 30
	HEADERS = { "accept": "application/json", 'User-Agent': 'PES Scraper'}

	def __init__(self, console: pes.sql.Console, rom: str, fullscan: bool = False):
		"""
		@param	console		console
		@param	rom			path to ROM
		@param fullScan		set to True to force an update of all meta data and coverart
		"""
		self._console = console
		self._rom = rom
		self._fullscan = fullscan

	@abc.abstractmethod
	def run(self, processNumber: int) -> RomTaskResult:
		"""
		Retrieves meta data for the given ROM.

		@param	processNumber process number
		@returns a RomTaskResult object
		"""

	@staticmethod
	def _scaleImage(path: str) -> str:
		img = PIL.Image.open(path)
		imgFormat = img.format
		filename, extension = os.path.splitext(path)
		logging.debug("RomTask._scaleImage: %s format is %s" % (path, imgFormat))
		width, height = img.size
		scaleWidth = RomTask.SCALE_WIDTH
		ratio = min(float(scaleWidth / width), float(scaleWidth / height))
		newWidth = width * ratio
		newHeight = height * ratio
		if width > newWidth or height > newHeight:
			# scale image
			img.thumbnail((newWidth, newHeight), PIL.Image.ANTIALIAS)
		if imgFormat == "JPEG":
			extension = ".jpg"
		elif imgFormat == "PNG":
			extension = ".png"
		elif imgFormat == "GIF":
			extension = ".gif"
		else:
			imgFormat = "PNG"
			extension = ".png"
		newPath = "%s%s" % (filename, extension)
		if newPath != path:
			logging.warning("RomTask._scaleImage: %s will be deleted and saved as %s due to incorrect image format" % (path, newPath))
			os.remove(path)
		img.save(newPath, imgFormat)
		img.close()
		return newPath

	def setLock(self, lock):
		self._lock = lock

class GamesDbRomTask(RomTask):

	def __init__(self, console: pes.sql.Console, rom: str, fullscan: bool = False):
		super(GamesDbRomTask, self).__init__(console, rom, fullscan)

	def run(self, processNumber: int) -> RomTaskResult:
		logPrefix = "GamesDbRomTask(%d).run:" % processNumber
		romTaskResult = RomTaskResult()
		filename = os.path.split(self._rom)[1]
		logging.debug("%s processing -> %s" % (logPrefix, filename))

		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()

		rasum = pes.retroachievement.getRasum(self._rom, self._console.retroId)
		logging.debug("%s rasum for %s is %s" % (logPrefix, self._rom, rasum))

		# have we already saved this game?
		result = session.query(pes.sql.Game).filter(pes.sql.Game.path == self._rom).first()
		game = None
		newGame = True
		if result:
			logging.debug("%s already in database" % logPrefix)
			game = result
			game.found = True
			with self._lock:
				session.add(game)
				session.commit()
			newGame = False
		else:
			logging.debug("%s new game" % logPrefix)
			# find a game with matching rasum
			result = session.query(pes.sql.RetroAchievementGame).join(pes.sql.RetroAchievementGameHash).filter(pes.sql.RetroAchievementGame.retroConsoleId == self._console.retroId).filter(pes.sql.RetroAchievementGameHash.rasum == rasum).first()
			if result:
				logging.debug("%s: found match for rasum: %s" % (logPrefix, rasum))
				# now is there a GamesDbGame match?
				if result.gamesDbGame and len(result.gamesDbGame) > 0:
					gamesDbGame = result.gamesDbGame[0]
					game = pes.sql.Game(consoleId=self._console.id, rasum=rasum, gamesDbId=gamesDbGame.id, retroId=gamesDbGame.retroId, path=self._rom, found=True)
					with self._lock:
						session.add(game)
						session.commit()
					logging.debug("%s saved new record" % logPrefix)
					romTaskResult.state = RomTaskResult.STATE_ADDED

		if newGame or self._fullscan:
			logging.debug("%s downloading cover art" % logPrefix)

			url = None
			if game.gamesDbGame:
				if game.gamesDbGame.boxArtFrontLarge:
					url = game.gamesDbGame.boxArtFrontLarge
				elif game.gamesDbGame.boxArtFrontMedium:
					url = game.gamesDbGame.boxArtFrontMedium
				elif game.gamesDbGame.boxArtFrontOriginal:
					url = game.gamesDbGame.boxArtFrontOriginal

			if url:
				logging.debug("%s URL for %s is %s" % (logPrefix, self._rom, url))
				response = requests.get(
					url,
					headers=self.HEADERS,
					timeout=self.URL_TIMEOUT
				)
				if response.status_code == requests.codes.ok:
					extension = url[url.rfind('.'):]
					path = os.path.join(pes.userCoverartDir, self._console.name, "%s%s" % (game.gamesDbGame.name, extension))
					logging.debug("%s saving to %s" % (logPrefix, path))
					with open(path, "wb") as f:
						f.write(response.content)
					self._scaleImage(path)
					if not newGame:
						romTaskResult.state = RomTaskResult.STATE_UPDATED
				else:
					logging.warning("%s unable to download %s" % (logPrefix, url))
					romTaskResult.state = RomTaskResult.STATE_FAILED

			else:
				logging.warning("%s no cover art URL for %s (%d)" % (logPrefix, self._rom, game.gamesDbId))

		# look for best match
		#for result in session.query(pes.sql.GamesDbPlatform).join(pes.sql.GamesDbGame).filter(pes.sql.GamesDbPlatform.id == self.__platformId).filter(pes.sql.GamesDbGame.rasum == rasum):
		#	logging.debug("GamesDbRomTask(%d).run: found match for rasum: %s" % (processNumber, rasum))
		#	break

		return romTaskResult


class RomScanMonitorThread(QThread):

	progressSignal = pyqtSignal(float, arguments=['progress'])
	progressMessageSignal = pyqtSignal(str, arguments=['message'])
	stateChangeSignal = pyqtSignal(str, arguments=['state'])

	def __init__(self, parent=None):
		super(RomScanMonitorThread, self).__init__(parent)
		logging.debug("RomScanMonitorThread.__init__: created")
		self.__scanThread = None
		self.__fullscan = False

	def __handleProgressMessageSignal(self, msg):
		self.progressMessageSignal.emit(msg)

	def __handleStateChangeSignal(self, state):
		self.stateChangeSignal.emit(state)

	def run(self):
		if self.__scanThread:
			self.__scanThread.progressMessageSignal.disconnect(self.__handleProgressMessageSignal)
			self.__scanThread.stateChangeSignal.disconnect(self.__handleStateChangeSignal)
		self.__scanThread = RomScanThread()
		self.__scanThread.fullscan = self.__fullscan
		# connect to signals
		self.__scanThread.progressMessageSignal.connect(self.__handleProgressMessageSignal)
		self.__scanThread.stateChangeSignal.connect(self.__handleStateChangeSignal)
		logging.debug("RomScanMonitorThread.run: starting RomScanThread")
		self.__scanThread.start()
		while (True):
			if not self.__scanThread.hasStarted():
				continue
			if not self.__scanThread.isRunning():
				logging.debug("RomScanMonitorThread.run: RomScanThread finished")
				break
			self.progressSignal.emit(self.__scanThread.getProgress())
			time.sleep(1)

	@pyqtProperty(bool)
	def fullscan(self) -> bool:
		return self.__fullscan

	@fullscan.setter
	def fullscan(self, fullscan: bool):
		self.__fullscan = fullscan

class RomScanThread(QThread):

	progressMessageSignal = pyqtSignal(str, arguments=['message'])
	stateChangeSignal = pyqtSignal(str, arguments=['state'])

	def __init__(self, parent=None):
		super(RomScanThread, self).__init__(parent)
		logging.debug("RomScanThread.__init__")
		self.__fullscan = False
		self.__done = False
		self.__started = False
		self.__processStarted = False
		self.__startTime = None
		self.__romTotal = 0
		self.__added = 0
		self.__updated = 0
		self.__deleted = 0
		self.__consoleSettings = pes.common.ConsoleSettings(pes.userConsolesConfigFile)
		self.__userSettings = pes.common.UserSettings(pes.userPesConfigFile)
		self.__romScraper = self.__userSettings.get("settings", "romScraper")
		self.__romsDir = self.__userSettings.get("settings", "romsDir")
		self.__tasks = None
		self.__romList = None
		self.__romProcessTotal = multiprocessing.cpu_count() * 2

	@staticmethod
	def __extensionOk(extensions: list, filename: str) -> bool:
		for e in extensions:
			if filename.endswith(e) or filename.endswith(e.upper()):
				name = os.path.split(filename)[1]
				return True
		return False

	def getLastRom(self) -> str:
		if self.__romList == None or not self.__started or (self.__exitEvent != None and self.__exitEvent.is_set()) or len(self.__romList) == 0:
			return None
		return self.__romList[-1]

	def getProgress(self) -> float:
		if not self.isRunning() and self.__done:
			return 1
		if not self.__started or self.__tasks == None or self.__romTotal == 0 or not self.__processStarted:
			return 0
		qsize = self.__tasks.qsize()
		if qsize == 0:
			return 1
		# process is running
		# remove posion pills from calculation
		qsize -= self.__romProcessTotal
		return float(self.__romTotal - qsize) / float(self.__romTotal)

	def hasStarted(self) -> bool:
		return self.__started

	def isRunning(self) -> bool:
		if self.__started and not self.__done:
			return True
		return False

	def run(self):
		self.stateChangeSignal.emit("started")
		logging.debug("RomScanThread.run: rom scan thread started")

		self.__done = False
		self.__started = True
		self.__startTime = time.time()
		self.__romTotal = 0
		self.__added = 0
		self.__updated = 0

		lock = multiprocessing.Lock()
		self.__tasks = multiprocessing.JoinableQueue()
		self.__romList = multiprocessing.Manager().list()
		exitEvent = multiprocessing.Event()
		results = multiprocessing.Queue()
		logging.debug("RomScanThread.run: will use %d ROM processes" % self.__romProcessTotal)
		romProcesses = [RomProcess(i, self.__tasks, results, exitEvent, lock, self.__romList) for i in range(self.__romProcessTotal)]

		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()
		# set all game records' found coumn to false
		session.query(pes.sql.Game).update({pes.sql.Game.found: False})
		# loop over all consoles
		consoles = session.query(pes.sql.Console).all()
		for console in consoles:
			logging.debug("RomScanThread.run: processing console %s" % console.name)
			extensions = self.__consoleSettings.get(console.name, "extensions")
			ignoreRoms = self.__consoleSettings.get(console.name, "ignore_roms")
			logging.debug("RomScanThread.run: extensions for %s are: %s" % (console.name, ','.join(extensions)))
			romFiles = []
			for f in glob.glob(os.path.join(self.__romsDir, console.name, "*")):
				if os.path.isfile(f):
					if (ignoreRoms == None or f not in ignoreRoms) and self.__extensionOk(extensions, f):
						romFiles.append(f)
						if self.__romScraper == "theGamesDb.net":
							platform = console.platform
							if platform == None:
								pes.common.pesExit("RomScanThread.run: no platform relationship with console ID: %d" % console.id)
							self.__tasks.put(GamesDbRomTask(console, f, self.__fullscan))

			consoleRomTotal = len(romFiles)
			self.__romTotal += consoleRomTotal
			logging.debug("RomScanThread.run: found %d ROMs for %s" % (consoleRomTotal, console.name))
			self.progressMessageSignal.emit("Processing %s: %d ROMs found" % (console.name, consoleRomTotal))

		# our session must be closed before starting the sub processes
		session.close()

		if self.__romTotal == 0:
			self.progressMessageSignal.emit("No ROMs found")
			self.__done = True
			self.stateChangeSignal.emit("done")
			return

		self.stateChangeSignal.emit("update")

		self.progressMessageSignal.emit("Found %d ROMs, beginning meta data updates..." % self.__romTotal)

		# add poison pills
		for i in range(self.__romProcessTotal):
				self.__tasks.put(None)

		logging.debug("RomScanThread.run: poison pills added to process queue")
		logging.debug("RomScanThread.run: starting ROM processes...")
		self.__processStarted = True
		for p in romProcesses:
			p.start()
		for p in romProcesses:
			p.join()
		logging.debug("RomScanThread.run: ROM processes joined main thread")
		self.__tasks.join()
		logging.debug("RomScanThread.run: ROM tasks joined main thread")
		logging.debug("RomScanThread.run: processing result queue...")
		while not results.empty():
			romTaskResult = results.get()
		logging.debug("RomScanThread.run: finished processing result queue")
		session = sqlalchemy.orm.sessionmaker(bind=engine)()
		self.__deleted = session.query(pes.sql.Game).filter(pes.sql.Game.found == False).count()
		if self.__deleted > 0:
			logging.warning("RomScanThread.run: deleted %d games from database" % self.__deleted)
			session.query(pes.sql.Game).filter(pes.sql.Game.found == False).delete()
		session.commit()
		session.close()
		self.__done = True
		self.stateChangeSignal.emit("done")
		logging.debug("RomScanThread.run: complete")

	@pyqtProperty(bool)
	def fullscan(self) -> bool:
		return self.__fullscan

	@fullscan.setter
	def fullscan(self, fullscan: bool):
		self.__fullscan = fullscan
