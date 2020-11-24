
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020 Neil Munday (neil@mundayweb.com)
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

import glob
import logging
import multiprocessing
import os
import pes
import pes.common
import pes.sql
import sqlalchemy.orm
import time

from PIL import Image

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread

logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class RomTask(object):

	SCALE_WIDTH = 400.0
	IMG_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']

	def __init__(self, rom):
		"""
			@param	rom		path to ROM
		"""
		self._rom = rom

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

	def __init__(self, rom):
		super(GamesDbRomTask, self).__init__(rom)

	def run(self):
		filename = os.path.split(self._rom)[1]
		logging.debug("GamesDbRomTask.run: processing -> %s" % filename)

class RomScanThread(QThread):

	progressSignal = pyqtSignal(float, arguments=['progress'])
	progressMessage = pyqtSignal(str, arguments=['message'])
	stateChange = pyqtSignal(str, arguments=['state'])

	def __init__(self, parent=None):
		super(RomScanThread, self).__init__(parent)
		logging.debug("RomScanThread.__init__")
		self.__done = False
		self.__started = False
		self.__startTime = None
		self.__romTotal = 0
		self.__consoleSettings = pes.common.ConsoleSettings(pes.userConsolesConfigFile)
		self.__userSettings = pes.common.UserSettings(pes.userPesConfigFile)
		self.__romsDir = self.__userSettings.get("settings", "romsDir")

	@staticmethod
	def __extensionOk(extensions, filename):
		for e in extensions:
			if filename.endswith(e):
				return True
		return Fals

	def run(self):
		self.stateChange.emit("started")
		logging.debug("RomScanThread.run: rom scan thread started")

		self.__done = False
		self.__started = True
		self.__startTime = time.time()
		self.__romTotal = 0

		lock = multiprocessing.Lock()
		tasks = multiprocessing.JoinableQueue()
		exitEvent = multiprocessing.Event()
		results = multiprocessing.Queue()
		processTotal = multiprocessing.cpu_count() * 2
		logging.debug("RomScanThread.run: will use %d ROM processes" % romProcessTotal)
		#romProcesses = [RomProcess(i, tasks, results, exitEvent, lock) for i in range(romProcessTotal)]

		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()
		consoles = session.query(pes.sql.Console).all()
		for console in consoles:
			logging.info("RomScanThread.run: processing console %s" % console.name)
			extensions = self.__consoleSettings.get(console.name, "extensions").split(' ')
			logging.debug("RomScanThread.run: extensions for %s are: %s" % (console.name, ','.join(extensions)))
			romFiles = []
			for f in glob.glob(os.path.join(self.__romsDir, console.name, "*")):
				if os.path.isfile(f) and self.__extensionOk(extensions, f):
					romFiles.append(f)

			consoleRomTotal = len(romFiles)
			self.__romTotal += consoleRomTotal
			logging.info("RomScanThread.run: found %d ROMs for %s" % (consoleRomTotal, console.name))
			self.progressMessage.emit("Processing %s: %d ROMs found" % (console.name, consoleRomTotal))

		if self.__romTotal == 0:
			self.progressMessage.emit("No ROMs found")
			self.__done = True
			self.stateChange.emit("done")
			return

		self.progressMessage.emit("Found %d ROMs, updating database..." % self.__romTotal)

		self.__done = True
		self.stateChange.emit("done")
