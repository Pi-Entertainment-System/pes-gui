
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
import requests
import sqlalchemy.orm
import time

from PIL import Image

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread

logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

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

		added = 0
		updated = 0
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
					added += result[0]
					updated += result[1]
					if not self.__exitEvent.is_set():
						self.__romList.append((result[2], result[3]))
				except Exception as e:
					logging.error("%s: Failed to process task due to the following error:" % self.name)
					logging.error(e)
				self.__taskQueue.task_done()
		self.__resultQueue.put((added, updated))
		self.__resultQueue.close()

class RomTask(abc.ABC):

	SCALE_WIDTH = 400.0
	IMG_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
	URL_TIMEOUT = 30

	def __init__(self, consoleId, rom):
		"""
		@param	consoleId	consoleId
		@param	rom			path to ROM
		"""
		self._consoleId = consoleId
		self._rom = rom

	@abc.abstractmethod
	def run(self, processNumber):
		"""
		Retrieves meta data for the given ROM.

		@param	processNumber process number
		@returns a tuple containing (added, updated, failed, name, thumbPath)
		"""

	@staticmethod
	def _scaleImage(path):
		img = Image.open(path)
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
			img.thumbnail((newWidth, newHeight), Image.ANTIALIAS)
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

	# my theGamesDbApi public key - rate limited per IP per month
	API_KEY = "d12fb5ce1f84c6cb3cec2b89861551905540c0ab564a5a21b3e06e34b2206928"
	API_URL = "https://api.thegamesdb.net/v1"
	HEADERS = { "accept": "application/json", 'User-Agent': 'PES Scraper'}

	def __init__(self, consoleId, rom, name, platformId, retroConsoleId):
		super(GamesDbRomTask, self).__init__(consoleId, rom)
		self.__platformId = platformId
		self.__retroConsoleId = retroConsoleId
		self.__name = name

	def run(self, processNumber):
		added = 0
		updated = 0
		failed = 0
		filename = os.path.split(self._rom)[1]
		thumbPath = None
		logging.debug("GamesDbRomTask(%d).run: processing -> %s" % (processNumber, filename))

		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()

		rasum = pes.retroachievement.getRasum(self._rom, self.__retroConsoleId)
		logging.debug("GamesDbRomTask(%d).run: rasum for %s is %s" % (processNumber, self._rom, rasum))

		# have we already saved this game?
		result = session.query(pes.sql.Game).filter(pes.sql.Game.path == self._rom).first()
		if result:
			logging.debug("GamesDbRomTask(%d).run: already in database", processNumber)
		else:
			logging.debug("GamesDbRomTask(%d).run: new game" % processNumber)
			# find a game with matching rasum
			result = session.query(pes.sql.RetroAchievementGame).join(pes.sql.RetroAchievementGameHash).filter(pes.sql.RetroAchievementGame.retroConsoleId == self.__retroConsoleId).filter(pes.sql.RetroAchievementGameHash.rasum == rasum).first()
			if result:
				logging.debug("GamesDbRomTask(%d).run: found match for rasum: %s" % (processNumber, rasum))
				# now is there a GamesDbGame match?
				if result.gamesDbGame and len(result.gamesDbGame) > 0:
					gamesDbGame = result.gamesDbGame[0]
					game = pes.sql.Game(consoleId=self._consoleId, rasum=rasum, gamesDbId=gamesDbGame.id, retroId=gamesDbGame.retroId, path=self._rom)
					session.add(game)
					session.commit()
					logging.debug("GamesDbRomTask(%d).run: saved new record" % processNumber)

		# look for best match
		#for result in session.query(pes.sql.GamesDbPlatform).join(pes.sql.GamesDbGame).filter(pes.sql.GamesDbPlatform.id == self.__platformId).filter(pes.sql.GamesDbGame.rasum == rasum):
		#	logging.debug("GamesDbRomTask(%d).run: found match for rasum: %s" % (processNumber, rasum))
		#	break

		return (added, updated, failed, self.__name, thumbPath)

class RomScanMonitorThread(QThread):

	progressSignal = pyqtSignal(float, arguments=['progress'])
	progressMessageSignal = pyqtSignal(str, arguments=['message'])
	stateChangeSignal = pyqtSignal(str, arguments=['state'])

	def __init__(self, parent=None):
		super(RomScanMonitorThread, self).__init__(parent)
		logging.debug("RomScanMonitorThread.__init__: created")
		self.__scanThread = None

	def __handleProgressMessageSignal(self, msg):
		self.progressMessageSignal.emit(msg)

	def __handleStateChangeSignal(self, state):
		self.stateChangeSignal.emit(state)

	def run(self):
		if self.__scanThread:
			self.__scanThread.progressMessageSignal.disconnect(self.__handleProgressMessageSignal)
			self.__scanThread.stateChangeSignal.disconnect(self.__handleStateChangeSignal)
		self.__scanThread = RomScanThread()
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

class RomScanThread(QThread):

	progressMessageSignal = pyqtSignal(str, arguments=['message'])
	stateChangeSignal = pyqtSignal(str, arguments=['state'])

	def __init__(self, parent=None):
		super(RomScanThread, self).__init__(parent)
		logging.debug("RomScanThread.__init__")
		self.__done = False
		self.__started = False
		self.__processStarted = False
		self.__startTime = None
		self.__romTotal = 0
		self.__added = 0
		self.__updated = 0
		self.__consoleSettings = pes.common.ConsoleSettings(pes.userConsolesConfigFile)
		self.__userSettings = pes.common.UserSettings(pes.userPesConfigFile)
		self.__romScraper = self.__userSettings.get("settings", "romScraper")
		self.__romsDir = self.__userSettings.get("settings", "romsDir")
		self.__tasks = None
		self.__romList = None
		self.__romProcessTotal = multiprocessing.cpu_count() * 2

	@staticmethod
	def __extensionOk(extensions, filename):
		for e in extensions:
			if filename.endswith(e) or filename.endswith(e.upper()):
				name = os.path.split(filename)[1]
				return name.replace(e, "")
		return None

	def getLastRom(self):
		if self.__romList == None or not self.__started or (self.__exitEvent != None and self.__exitEvent.is_set()) or len(self.__romList) == 0:
			return None
		return self.__romList[-1]

	def getProgress(self):
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

	def hasStarted(self):
		return self.__started

	def isRunning(self):
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
		consoles = session.query(pes.sql.Console).all()
		for console in consoles:
			logging.debug("RomScanThread.run: processing console %s" % console.name)
			extensions = self.__consoleSettings.get(console.name, "extensions")
			ignoreRoms = self.__consoleSettings.get(console.name, "ignore_roms")
			logging.debug("RomScanThread.run: extensions for %s are: %s" % (console.name, ','.join(extensions)))
			romFiles = []
			for f in glob.glob(os.path.join(self.__romsDir, console.name, "*")):
				if os.path.isfile(f):
					romName = self.__extensionOk(extensions, f)
					if (ignoreRoms == None or f not in ignoreRoms) and romName != None:
						romFiles.append(f)
						if self.__romScraper == "theGamesDb.net":
							platform = console.platform
							if platform == None:
								pes.common.pesExit("RomScanThread.run: no platform relationship with console ID: %d" % console.id)
							self.__tasks.put(GamesDbRomTask(console.id, f, romName, platform.id, console.retroId))

			consoleRomTotal = len(romFiles)
			self.__romTotal += consoleRomTotal
			logging.debug("RomScanThread.run: found %d ROMs for %s" % (consoleRomTotal, console.name))
			self.progressMessageSignal.emit("Processing %s: %d ROMs found" % (console.name, consoleRomTotal))

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
			(added, updated) = results.get()
			self.__added += added
			self.__updated += updated
		logging.debug("RomScanThread.run: finished processing result queue")
		self.__done = True
		self.stateChangeSignal.emit("done")
		logging.debug("RomScanThread.run: complete")
