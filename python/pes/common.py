#
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

from pes import *
import configparser
import csv
import fcntl
import logging
import shlex
import socket
import subprocess
import struct

def checkDir(d):
	logging.debug("checking for: %s" % d)
	if not os.path.exists(d):
		pesExit("Error: %s does not exist!" % d, True)
	if not os.path.isdir(d):
		pesExit("Error: %s is not a directory!" % d, True)

def checkFile(f):
	if not os.path.exists(f):
		pesExit("Error: %s does not exist!" % f, True)
	if not os.path.isfile(f):
		pesExit("Error: %s is not a file!" % f, True)

def getDefaultInterface():
	with open('/proc/net/route', 'r') as f:
		for i in csv.DictReader(f, delimiter="\t"):
			if int(i['Destination'], 16) == 0:
				return i['Iface']
	return None

def getIpAddress(ifname=None):
	if not ifname:
		ifname = getDefaultInterface()
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15].encode()))[20:24])

def initConfig():
	logging.debug("initialising config...")
	checkDir(userConfDir)
	for root, dirs, files in os.walk(confDir):
		userRoot = root.replace(baseDir, userDir)
		for d in dirs:
			dest = os.path.join(userRoot, d)
			if not os.path.exists(dest):
				mkdir(dest)

		for f in files:
			dest = os.path.join(userRoot, f)
			source = os.path.join(root, f)
			if not os.path.exists(dest):
				logging.debug("copying %s to %s" % (source, dest))
				shutil.copy(source, dest)

def initDb():
	checkFile(masterDb)
	if not os.path.exists(userDb):
		logging.debug("initialising %s from %s..." % (userDb, masterDb))
		shutil.copy(masterDb, userDb)

def mkdir(path):
	if not os.path.exists(path):
		logging.debug("mkdir: directory: %s" % path)
		os.mkdir(path)
		return True
	elif not os.path.isdir(path):
		pesExit("Error: %s is not a directory!" % path, True)
	elif not os.access(path, os.W_OK):
		pesExit("Error: %s is not writeable!" % path, True)
	# did not have to make directory so return false
	logging.debug("mkdir: %s already exists" % path)
	return False

def pesExit(msg = None, error = False):
	if error:
		if msg:
			logging.error(msg)
		else:
			logging.error("Unrecoverable error occurred, exiting!")
		sys.exit(1)
	if msg:
		logging.info(msg)
	else:
		logging.info("Exiting...")
	sys.exit(0)

def runCommand(cmd):
	'''
	Execute the given command and return a tuple that contains the
	return code, std out and std err output.
	'''
	logging.debug('running %s' % cmd)
	process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	return (process.returncode, stdout.decode(), stderr.decode())

def scaleImage(ix, iy, bx, by):
	"""
	Original author: Frank Raiser (crashchaos@gmx.net)
	URL: http://www.pygame.org/pcr/transform_scale
	Modified by Neil Munday
	"""
	if ix > iy:
		# fit to width
		scale_factor = bx/float(ix)
		sy = scale_factor * iy
		if sy > by:
			scale_factor = by/float(iy)
			sx = scale_factor * ix
			sy = by
		else:
			sx = bx
	else:
		# fit to height
		scale_factor = by/float(iy)
		sx = scale_factor * ix
		if sx > bx:
			scale_factor = bx/float(ix)
			sx = bx
			sy = scale_factor * iy
		else:
			sy = by
	return (int(sx),int(sy))

class Settings(object):

	STR_PROP = 1
	BOOL_PROP = 2
	INT_PROP = 3
	LIST_PROP = 4
	PATH_PROP = 5

	def __init__(self, f, props=None):
		logging.debug("Settings.__init__: created using %s" % f)
		self._configparser = configparser.RawConfigParser()
		self._configparser.read(f)
		self._path = f
		self._props = None
		if props:
			self._props = props

	def get(self, section, prop):
		logging.debug("Settings.get: section = %s, prop = %s" % (section, prop))
		if not self._configparser.has_section(section):
			logging.warning("No section \"%s\" in \"%s\"" % (section, self._path))
			return None
		if not self._configparser.has_option(section, prop):
			logging.warning("No property \"[%s]:%s\" in \"%s\"" % (section, prop, self._path))
			return None
		if section in self._props and prop in self._props[section]:
			if self._props[section][prop] == Settings.BOOL_PROP:
				logging.debug("Settings.get: returning boolean for [%s]:%s" % (section, prop))
				return self._configparser.getboolean(section, prop)
			if self._props[section][prop] == Settings.INT_PROP:
				logging.debug("Settings.get: returning int for [%s]:%s" % (section, prop))
				return self._configparser.getint(section, prop)
		# assume string
		logging.debug("Settings.get: returning string for [%s]:%s" % (section, prop))
		rslt = self._configparser.get(section, prop)
		if rslt == None or len(rslt) == 0:
			return None
		return rslt

	def getSections(self):
		return self._configparser.sections()

	def getType(self, section, prop):
		if section in self._props and prop in self._props[section]:
			return self._props[section][prop]
		return None

	def save(self, path):
		logging.debug("Settings.save: saving to %s" % path)
		with open(path, "w") as f:
			self._configparser.write(f)

	def set(self, section, prop, value):
		logging.debug("Settings.set: setting %s.%s = %s" % (section, prop, value))
		self._configparser.set(section, prop, str(value))

class UserSettings(Settings):

	def __init__(self):
		props = {
			"RetroAchievements": {
				"apiKey": Settings.STR_PROP,
				"hardcore": Settings.BOOL_PROP,
				"username": Settings.STR_PROP,
				"password": Settings.STR_PROP
			},
			"settings": {
				"hdmi-cec": Settings.BOOL_PROP,
				"romScraper": Settings.STR_PROP,
				"screenSaverTimeout": Settings.INT_PROP
			},
			"webServer": {
				"enabled": Settings.BOOL_PROP,
				"port": Settings.INT_PROP
			}
		}
		super(UserSettings, self).__init__(userPesConfigFile, props)

	def get(self, section, prop):
		rslt = super(UserSettings, self).get(section, prop)
		if self.getType(section, prop) == Settings.STR_PROP:
			if rslt == None or len(rslt) == 0:
				return None
			return rslt.replace("%%USERDIR%%", userDir)
		return rslt

class ConsoleSettings(Settings):

	def __init__(self):
		super(ConsoleSettings, self).__init__(userConsolesConfigFile)
		self.__props = {
			"emulator": Settings.STR_PROP,
			"ignore_roms": Settings.LIST_PROP,
			"extensions": Settings.LIST_PROP,
			"command": Settings.PATH_PROP,
			"require": Settings.LIST_PROP
		}

		self.__optionalProps = ["ignore_roms", "require"]
		self.__cache = {}

	def get(self, c, prop):
		if not self._configparser.has_option(c, prop):
			if prop in self.__optionalProps:
				return None
			raise Exception("%s has no option \"%s\" in %s" % (c, prop, self._path))
		if not prop in self.__props:
			raise Exception("%s is not in props dictionary" % prop)
		if c not in self.__cache:
			self.__cache[c] = {}
		if not prop in self.__cache[c]:
			if self.__props[prop] == Settings.INT_PROP:
				self.__cache[c][prop] = self._configparser.getint(c, prop)
			elif self.__props[prop] == Settings.PATH_PROP:
				self.__cache[c][prop] = self.__parseStr(self._configparser.get(c, prop))
			elif self.__props[prop] == Settings.LIST_PROP:
				l = []
				for i in self._configparser.get(c, prop).split(","):
					l.append(self.__parseStr(i))
				self.__cache[c][prop] = l
			else:
				self.__cache[c][prop] = self._configparser.get(c, prop)
		return self.__cache[c][prop]

	@staticmethod
	def __parseStr(s):
		return s.replace("%%USERDIR%%", userDir).replace("%%BASE%%", baseDir).replace("%%USERBIOSDIR%%", userBiosDir).replace("%%USERCONFDIR%%", userConfDir)