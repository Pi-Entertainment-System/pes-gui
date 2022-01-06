
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020-2022 Neil Munday (neil@mundayweb.com)
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
import datetime
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
import sqlalchemy
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
	STATE_SKIPPED = 4

	def __init__(self, state, name):
		self.state = state
		self.name = name
		self.coverart = None

	@property
	def coverart(self) -> str:
		return self.__coverart

	@coverart.setter
	def coverart(self, path: str):
		self.__coverart = path

	@property
	def name(self) -> str:
		return self.__name

	@name.setter
	def name(self, name: str):
		self.__name = name

	@property
	def state(self) -> int:
		return self.__state

	@state.setter
	def state(self, state: int):
		if state == RomTaskResult.STATE_ADDED or state == RomTaskResult.STATE_UPDATED or state == RomTaskResult.STATE_FAILED or state == RomTaskResult.STATE_SKIPPED:
			self.__state = state
		else:
			raise ValueError("Invalid state: %s" % state)

	def __repr__(self):
		return "<RomTaskResult state=%d >" % self.state

class RomProcessResult(object):

	def __init__(self):
		self.__added = 0
		self.__skipped = 0
		self.__updated = 0
		self.__failed = 0

	@property
	def added(self) -> int:
		return self.__added

	def addRomTaskResult(self, result: RomTaskResult):
		if result.state == RomTaskResult.STATE_UPDATED:
			self.__updated += 1
		elif result.state == RomTaskResult.STATE_ADDED:
			self.__added += 1
		elif result.state == RomTaskResult.STATE_FAILED:
			self.__failed += 1
		elif result.state == RomTaskResult.STATE_SKIPPED:
			self.__skipped += 1
		else:
			raise ValueError("Invalid state for RomTaskResult: %s" % result)

	@property
	def failed(self) -> int:
		return self.__failed

	@property
	def skipped(self) -> int:
		return self.__skipped

	@property
	def updated(self) -> int:
		return self.__updated


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

		romProcessResult = RomProcessResult()
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
					romTaskResult = task.run(self.__processNumber)
					romProcessResult.addRomTaskResult(romTaskResult)
					if not self.__exitEvent.is_set():
						self.__romList.append({ "name": romTaskResult.name, "coverart": romTaskResult.coverart })
				except Exception as e:
					logging.exception("%s: Failed to process task due to the following error:" % self.name)
					self.__resultQueue.put(RomTaskResult(RomTaskResult.STATE_FAILED, ""))
				self.__taskQueue.task_done()
		self.__resultQueue.put(romProcessResult)
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
		self._romFileSize = os.path.getsize(rom)

	@abc.abstractmethod
	def run(self, processNumber: int) -> RomTaskResult:
		"""
		Retrieves meta data for the given ROM.

		@param	processNumber process number
		@returns a RomTaskResult object
		"""

	def _getNocoverart(self) -> str:
		return os.path.join(pes.resourcesDir, self._console.nocoverart)

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
		filename = os.path.split(self._rom)[1]
		romName = os.path.splitext(os.path.basename(self._rom))[0]
		romTaskResult = RomTaskResult(RomTaskResult.STATE_FAILED, romName)
		logging.debug("%s processing -> %s" % (logPrefix, filename))

		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()

		# have we already saved this game?
		with self._lock:
			result = session.query(pes.sql.Game).filter(pes.sql.Game.path == self._rom).first()
		game = None
		newGame = True
		rasum = None
		retroGame = None
		if result:
			logging.debug("%s already in database" % logPrefix)
			game = result
			game.found = True
			with self._lock:
				session.add(game)
				session.commit()
			newGame = False
			romTaskResult.state = RomTaskResult.STATE_SKIPPED
			romTaskResult.name = game.name
			romTaskResult.coverart = game.coverartFront
		else:
			logging.debug("%s new game" % logPrefix)
			if self._console.retroId:
				# find a game with matching rasum
				rasum = pes.retroachievement.getRasum(self._rom, self._console.retroId)
				logging.debug("%s rasum for %s is %s" % (logPrefix, self._rom, rasum))
				with self._lock:
					retroGame = session.query(pes.sql.RetroAchievementGame).join(pes.sql.RetroAchievementGameHash).filter(pes.sql.RetroAchievementGame.retroConsoleId == self._console.retroId).filter(pes.sql.RetroAchievementGameHash.rasum == rasum).first()
				if retroGame:
					logging.debug("%s found match for RetroAchievement game %d, rasum: %s" % (logPrefix, retroGame.id, rasum))
					# now is there a GamesDbGame match?
					if retroGame.gamesDbGame and len(retroGame.gamesDbGame) > 0:
						gamesDbGame = retroGame.gamesDbGame[0]
						with self._lock:
							game = pes.sql.Game(
								consoleId=self._console.id,
								added=datetime.datetime.now(),
								name=gamesDbGame.name,
								rasum=rasum,
								gamesDbId=gamesDbGame.id,
								retroId=gamesDbGame.retroId,
								path=self._rom,
								fileSize=self._romFileSize,
								found=True
							)
							session.add(game)
							session.commit()
						logging.debug("%s saved new record" % logPrefix)
						romTaskResult.state = RomTaskResult.STATE_ADDED
					else:
						logging.debug("%s no GamesDbGame associated with RetroAchievementGame %d" % (logPrefix, retroGame.id))
			else:
				logging.debug("%s %s has no retroId" % (logPrefix, self._console.name))

			if game == None:
				# try searching by name
				if rasum:
					logging.debug("%s no match for rasum: %s, trying name match" % (logPrefix, rasum))
				else:
					logging.debug("%s trying name match" % logPrefix)
				with self._lock:
					gamesDbGame = session.query(pes.sql.GamesDbGame).filter(sqlalchemy.func.lower(sqlalchemy.func.replace(pes.sql.GamesDbGame.name, " ", "")) == romName.replace(" ", "").lower()).first()
				if gamesDbGame:
					logging.debug("%s found match for name: \"%s\"" % (logPrefix, romName))
					retroId = gamesDbGame.retroId
					if (retroId == None or retroId == 0) and retroGame:
						retroId = retroGame.id
					game = pes.sql.Game(
						consoleId=self._console.id,
						added=datetime.datetime.now(),
						name=gamesDbGame.name,
						rasum=rasum,
						gamesDbId=gamesDbGame.id,
						retroId=retroId,
						path=self._rom,
						fileSize=self._romFileSize,
						coverartFront=self._getNocoverart(),
						found=True
					)
				else:
					logging.warning("%s could not find any match for %s" % (logPrefix, self._rom))
					game = pes.sql.Game(
						consoleId=self._console.id,
						added=datetime.datetime.now(),
						name=romName,
						rasum=rasum,
						path=self._rom,
						fileSize=self._romFileSize,
						coverartFront=self._getNocoverart(),
						found=True
					)
				with self._lock:
					session.add(game)
					session.commit()
				logging.debug("%s saved new record" % logPrefix)
				romTaskResult.state = RomTaskResult.STATE_ADDED

		if game and (newGame or self._fullscan):
			logging.debug("%s downloading cover art" % logPrefix)
			romTaskResult.name = game.name

			url = None
			if game.gamesDbGame:
				# create list of URLs to try for front coverart
				urls = []
				if game.gamesDbGame.boxArtFrontLarge:
					urls.append(game.gamesDbGame.boxArtFrontLarge)
				if game.gamesDbGame.boxArtFrontMedium:
					urls.append(game.gamesDbGame.boxArtFrontMedium)
				if game.gamesDbGame.boxArtFrontOriginal:
					urls.append(game.gamesDbGame.boxArtFrontOriginal)

				logging.debug("%s URLs to try: %s" % (logPrefix, urls))

				if len(urls) > 0:
					i = 0
					imgSaved = False
					for url in urls:
						logging.debug("%s URL attempt %d for %s (front) is %s" % (logPrefix, (i + 1), self._rom, url))
						extension = url[url.rfind('.'):]
						path = os.path.join(pes.userCoverartDir, self._console.name, "%s-front%s" % (romName, extension))
						if self._fullscan or not os.path.exists(path):
							try:
								response = requests.get(
									url,
									headers=self.HEADERS,
									timeout=self.URL_TIMEOUT
								)
								if response.status_code == requests.codes.ok:
									logging.debug("%s saving to %s" % (logPrefix, path))
									with open(path, "wb") as f:
										f.write(response.content)
									self._scaleImage(path)
									imgSaved = True
									if not newGame:
										romTaskResult.state = RomTaskResult.STATE_UPDATED
									break
								else:
									if newGame:
										logging.warning("%s unable to download %s" % (logPrefix, url))
							except Exception as e:
								logging.error("%s failed to download %s due to %s" % (logPrefix, url, e))
						else:
							logging.debug("%s using existing front cover art: %s" % (logPrefix, path))
							imgSaved = True
							break
						i += 1
					if newGame:
						if imgSaved:
							game.coverartFront = path
							romTaskResult.coverart = game.coverartFront
						else:
							game.coverartFront = self._getNocoverart()
						with self._lock:
							session.add(game)
							session.commit()
					# get rear cover art
					urls = []
					if game.gamesDbGame.boxArtBackLarge:
						urls.append(game.gamesDbGame.boxArtBackLarge)
					if game.gamesDbGame.boxArtBackMedium:
						urls.append(game.gamesDbGame.boxArtBackMedium)
					if game.gamesDbGame.boxArtBackOriginal:
						urls.append(game.gamesDbGame.boxArtBackOriginal)
					i = 0
					imgSaved = False
					for url in urls:
						extension = url[url.rfind('.'):]
						path = os.path.join(pes.userCoverartDir, self._console.name, "%s-back%s" % (romName, extension))
						if self._fullscan or not os.path.exists(path):
							logging.debug("%s URL attempt %d for %s (back) is %s" % (logPrefix, (i + 1), self._rom, url))
							try:
								response = requests.get(
									url,
									headers=self.HEADERS,
									timeout=self.URL_TIMEOUT
								)
								if response.status_code == requests.codes.ok:
									logging.debug("%s saving to %s" % (logPrefix, path))
									with open(path, "wb") as f:
										f.write(response.content)
									self._scaleImage(path)
									imgSaved = True
							except Exception as e:
								logging.error("%s failed to download %s due to %s" % (logPrefix, url, e))
						else:
							logging.debug("%s using existing rear cover art: %s" % (logPrefix, path))
							imgSaved = True
						if imgSaved and newGame:
							game.coverartBack = path
							with self._lock:
								session.add(game)
								session.commit()
							break
						i += 1
					# get screen shots
					count = 0
					screenshots = []
					for screenshot in game.gamesDbGame.screenshots:
						urls = []
						if screenshot.large:
							urls.append(screenshot.large)
						if screenshot.medium:
							urls.append(screenshot.medium)
						if screenshot.original:
							urls.append(screenshot.original)

						i = 0
						for url in urls:
							logging.debug("%s screen shot url: %s" % (logPrefix, url))
							extension = url[url.rfind('.'):]
							path = os.path.join(pes.userScreenshotDir, self._console.name, "%s-%d%s" % (romName, (count + 1), extension))
							if self._fullscan or not os.path.exists(path):
								logging.debug("%s URL attempt %d for %s (screenshot) is %s" % (logPrefix, (i + 1), self._rom, url))
								try:
									response = requests.get(
										url,
										headers=self.HEADERS,
										timeout=self.URL_TIMEOUT
									)
									if response.status_code == requests.codes.ok:
										logging.debug("%s saving to %s" % (logPrefix, path))
										with open(path, "wb") as f:
											f.write(response.content)
										self._scaleImage(path)
										mustSave = True
										if not newGame:
											# does the DB entry already exist?
											if session.query(pes.sql.GameScreenshot).filter(pes.sql.GameScreenshot.path == path):
												mustSave = False
										if mustSave:
											screenshots.append(pes.sql.GameScreenshot(path=path))
										count += 1
										break
								except Exception as e:
									logging.error("%s failed to download %s due to %s" % (logPrefix, url, e))
							else:
								count += 1
								logging.debug("%s already dowloaded %s" % (logPrefix, path))
								mustSave = True
								if not newGame:
									# does the DB entry already exist?
									if session.query(pes.sql.GameScreenshot).filter(pes.sql.GameScreenshot.path == path):
										mustSave = False
								if mustSave:
									screenshots.append(pes.sql.GameScreenshot(path=path))
								break
							i += 1
						# only save a max of three screen shots per game
						if count > 3:
							break
					if len(screenshots) > 0:
						game.screenshots = screenshots
						with self._lock:
							session.add(game)
							session.commit()
				else:
					logging.warning("%s no cover art URL for %s (%d)" % (logPrefix, self._rom, game.gamesDbId))

		return romTaskResult

class RomScanMonitorThread(QThread):

	progressSignal = pyqtSignal(float, str, str, arguments=['progress', 'name', 'coverart'])
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

	@pyqtProperty(int)
	def added(self) -> int:
		return self.__scanThread.getAdded()

	@pyqtProperty(int)
	def deleted(self) -> int:
		return self.__scanThread.getDeleted()

	@pyqtProperty(int)
	def failed(self) -> int:
		return self.__scanThread.getFailed()

	@pyqtProperty(bool)
	def fullscan(self) -> bool:
		return self.__fullscan

	@fullscan.setter
	def fullscan(self, fullscan: bool):
		self.__fullscan = fullscan

	@pyqtProperty(bool)
	def interrupted(self) -> bool:
		return self.__scanThread.getInterrupted()

	@pyqtProperty(int)
	def skipped(self) -> int:
		return self.__scanThread.getSkipped()

	@pyqtProperty(int)
	def timeTaken(self) -> int:
		return int(self.__scanThread.getTimeTaken())

	@pyqtProperty(int)
	def updated(self) -> int:
		return self.__scanThread.getUpdated()

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
			lastRom = self.__scanThread.getLastRom()
			if lastRom:
				self.progressSignal.emit(self.__scanThread.getProgress(), lastRom["name"], lastRom["coverart"])
			time.sleep(1)

	@pyqtSlot()
	def stop(self):
		if self.__scanThread:
			logging.debug("RomScanMonitorThread.stop: stopping RomScanThread...")
			self.__scanThread.stop()

class RomScanThread(QThread):

	progressMessageSignal = pyqtSignal(str, arguments=['message'])
	stateChangeSignal = pyqtSignal(str, arguments=['state'])

	def __init__(self, parent=None):
		super(RomScanThread, self).__init__(parent)
		logging.debug("RomScanThread.__init__")
		self.__fullscan = False
		self.__done = False
		self.__started = False
		self.__interrupted = False
		self.__processStarted = False
		self.__startTime = None
		self.__timeTaken = 0
		self.__romTotal = 0
		self.__added = 0
		self.__failed = 0
		self.__skipped = 0
		self.__updated = 0
		self.__deleted = 0
		self.__consoleSettings = pes.common.ConsoleSettings()
		self.__userSettings = pes.common.UserSettings()
		self.__romScraper = self.__userSettings.get("settings", "romScraper")
		self.__romsDir = pes.userRomDir
		self.__tasks = None
		self.__romList = None
		self.__exitEvent = None
		self.__romProcessTotal = multiprocessing.cpu_count() * 2

	@staticmethod
	def __extensionOk(extensions: list, filename: str) -> bool:
		for e in extensions:
			e = e.strip()
			if filename.endswith(e) or filename.endswith(e.upper()):
				name = os.path.split(filename)[1]
				return True
		return False

	@pyqtProperty(bool)
	def fullscan(self) -> bool:
		return self.__fullscan

	@fullscan.setter
	def fullscan(self, fullscan: bool):
		self.__fullscan = fullscan

	def getAdded(self) -> int:
		return self.__added

	def getDeleted(self) -> int:
		return self.__deleted

	def getFailed(self) -> int:
		return self.__failed

	def getInterrupted(self) -> bool:
		return self.__interrupted

	def getLastRom(self) -> dict:
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
		# but qsize could go negative if we only
		# have poison pills left!
		if qsize <= self.__romProcessTotal:
			# we're processing poison pills now
			# so we're done
			return 1
		qsize -= self.__romProcessTotal
		progress = float(self.__romTotal - qsize) / float(self.__romTotal)
		return progress

	def getSkipped(self) -> int:
		return self.__skipped

	def getTimeTaken(self) -> int:
		return self.__timeTaken

	def getUpdated(self) -> int:
		return self.__updated

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
		self.__interrupted = False
		self.__startTime = time.time()
		self.__timeTaken = 0
		self.__romTotal = 0
		self.__added = 0
		self.__failed = 0
		self.__deleted = 0
		self.__skipped = 0
		self.__updated = 0

		lock = multiprocessing.Lock()
		self.__tasks = multiprocessing.JoinableQueue()
		manager = multiprocessing.Manager()
		self.__romList = manager.list()
		self.__exitEvent = multiprocessing.Event()
		results = multiprocessing.Queue()
		logging.debug("RomScanThread.run: will use %d ROM processes" % self.__romProcessTotal)
		romProcesses = [RomProcess(i, self.__tasks, results, self.__exitEvent, lock, self.__romList) for i in range(self.__romProcessTotal)]

		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()
		# set all game records' found coumn to false
		session.query(pes.sql.Game).update({pes.sql.Game.found: False})
		# loop over all consoles
		consoles = session.query(pes.sql.Console).all()
		for console in consoles:
			if self.__consoleSettings.hasSection(console.name):
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

		self.progressMessageSignal.emit("Found %d ROMs, update in progress" % self.__romTotal)

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
		count = 0
		while not results.empty():
			romProcessResult = results.get()
			self.__added += romProcessResult.added
			self.__updated += romProcessResult.updated
			self.__failed += romProcessResult.failed
			self.__skipped += romProcessResult.skipped
			count += 1
		logging.debug("RomScanThread.run: finished processing %d result(s) from queue. Added: %d, Updated: %d, Skipped: %d, Failed: %d." % (count, self.__added, self.__updated, self.__skipped, self.__failed))
		session = sqlalchemy.orm.sessionmaker(bind=engine)()
		if self.__interrupted:
			# reset found status
			session.query(pes.sql.Game).filter(not pes.sql.Game.found).update({pes.sql.Game.found: True})
		else:
			self.__deleted = session.query(pes.sql.Game).filter(pes.sql.Game.found == False).count()
			if self.__deleted > 0:
				logging.warning("RomScanThread.run: deleted %d games from database" % self.__deleted)
				session.query(pes.sql.Game).filter(pes.sql.Game.found == False).delete()
		session.commit()
		session.close()
		self.__timeTaken = time.time() - self.__startTime
		self.__done = True
		self.stateChangeSignal.emit("done")
		logging.debug("RomScanThread.run: complete")

	def stop(self):
		if self.__started and not self.__done:
			self.__interrupted = True
			logging.debug("RomScanThread.stop: stopping processes...")
			self.__exitEvent.set()
		else:
			self.__done = True
		self.stateChangeSignal.emit("stopped")
