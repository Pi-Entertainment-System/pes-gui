#
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

# pylint: disable=invalid-name,line-too-long,missing-class-docstring,missing-function-docstring

"""
This module provides the "common" functions and classes required by PES.
"""

# standard imports
import configparser
import csv
import fcntl
import logging
import os
import shlex
import shutil
import socket
import subprocess
import sys
import struct

# pes imports
from pes import baseDir, confDir, primaryDb, userBiosDir, userConfDir, userConsolesConfigFile, userDb, userDir, userPesConfigFile

def checkDir(d: str):
    logging.debug("checking for: %s", d)
    if not os.path.exists(d):
        pesExit(f"Error: {d} does not exist!", True)
    if not os.path.isdir(d):
        pesExit(f"Error: {d} is not a directory!", True)

def checkFile(f: str):
    if not os.path.exists(f):
        pesExit(f"Error: {f} does not exist!", True)
    if not os.path.isfile(f):
        pesExit(f"Error: {f} is not a file!", True)

def getDefaultInterface() -> str:
    with open('/proc/net/route', 'r') as f: # pylint: disable=unspecified-encoding
        for i in csv.DictReader(f, delimiter="\t"):
            if int(i['Destination'], 16) == 0:
                return i['Iface']
    return None

def getIpAddress(ifname: str=None) -> str:
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
                logging.debug("copying %s to %s", source, dest)
                shutil.copy(source, dest)

def initDb():
    checkFile(primaryDb)
    if not os.path.exists(userDb):
        logging.debug("initialising %s from %s...", userDb, primaryDb)
        shutil.copy(primaryDb, userDb)

def mkdir(path: str):
    if not os.path.exists(path):
        logging.debug("mkdir: directory: %s", path)
        os.mkdir(path)
        return True
    if not os.path.isdir(path):
        pesExit(f"Error: {path} is not a directory!", True)
    elif not os.access(path, os.W_OK):
        pesExit(f"Error: {path} is not writeable!", True)
    else:
        # did not have to make directory so return false
        logging.debug("mkdir: %s already exists", path)
    return False

def pesExit(msg: str=None, error: bool=False):
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

def runCommand(cmd: str) -> tuple:
    '''
    Execute the given command and return a tuple that contains the
    return code, std out and std err output.
    '''
    logging.debug('running %s', cmd)
    with subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        stdout, stderr = process.communicate()
        return (process.returncode, stdout.decode(), stderr.decode())

def scaleImage(ix: int, iy: int, bx: int, by: int) -> tuple:
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
            scale_factor = by / float(iy)
            sx = scale_factor * ix
            sy = by
        else:
            sx = bx
    else:
        # fit to height
        scale_factor = by / float(iy)
        sx = scale_factor * ix
        if sx > bx:
            scale_factor = bx / float(ix)
            sx = bx
            sy = scale_factor * iy
        else:
            sy = by
    return (int(sx),int(sy))

class Settings:

    STR_PROP = 1
    BOOL_PROP = 2
    INT_PROP = 3
    LIST_PROP = 4
    PATH_PROP = 5

    def __init__(self, f: str, props: dict=None):
        logging.debug("Settings.__init__: created using %s", f)
        self._configparser = configparser.RawConfigParser()
        self._configparser.read(f)
        self._path = f
        self._props = None
        if props:
            self._props = props

    def get(self, section: str, prop: str) -> str:
        logging.debug("Settings.get: section = %s, prop = %s", section, prop)
        if not self._configparser.has_section(section):
            logging.warning("No section \"%s\" in \"%s\"", section, self._path)
            return None
        if not self._configparser.has_option(section, prop):
            logging.warning("No property \"[%s]:%s\" in \"%s\"", section, prop, self._path)
            return None
        if section in self._props and prop in self._props[section]:
            if self._props[section][prop] == Settings.BOOL_PROP:
                logging.debug("Settings.get: returning boolean for [%s]:%s", section, prop)
                return self._configparser.getboolean(section, prop)
            if self._props[section][prop] == Settings.INT_PROP:
                logging.debug("Settings.get: returning int for [%s]:%s", section, prop)
                return self._configparser.getint(section, prop)
        # assume string
        logging.debug("Settings.get: returning string for [%s]:%s", section, prop)
        rslt = self._configparser.get(section, prop)
        if rslt is None or len(rslt) == 0:
            return None
        return rslt

    def getSections(self) -> list:
        return self._configparser.sections()

    def getType(self, section: str, prop: str) -> int:
        if section in self._props and prop in self._props[section]:
            return self._props[section][prop]
        return None

    def hasSection(self, s: str) -> bool:
        return self._configparser.has_section(s)

    def save(self):
        logging.debug("Settings.save: saving to %s", self._path)
        with open(self._path, "w", encoding="utf-8") as f:
            self._configparser.write(f)

    def set(self, section: str, prop: str, value):
        logging.debug("Settings.set: setting %s.%s = %s", section, prop, value)
        self._configparser.set(section, prop, str(value))

class ConsoleSettings(Settings):

    def __init__(self):
        super().__init__(userConsolesConfigFile)
        self.__props = {
            "emulator": Settings.STR_PROP,
            "ignore_roms": Settings.LIST_PROP,
            "extensions": Settings.LIST_PROP,
            "command": Settings.PATH_PROP,
            "require": Settings.LIST_PROP
        }

        self.__optionalProps = ["ignore_roms", "require"]
        self.__cache = {}

    def get(self, section: str, prop: str) -> str:
        if not self._configparser.has_option(section, prop):
            if prop in self.__optionalProps:
                return None
            raise Exception(f"{section} has no option \"{prop}\" in {self._path}")
        if not prop in self.__props:
            raise Exception(f"{prop} is not in props dictionary")
        if section not in self.__cache:
            self.__cache[section] = {}
        if not prop in self.__cache[section]:
            if self.__props[prop] == Settings.INT_PROP:
                self.__cache[section][prop] = self._configparser.getint(section, prop)
            elif self.__props[prop] == Settings.PATH_PROP:
                self.__cache[section][prop] = self.__parseStr(self._configparser.get(section, prop))
            elif self.__props[prop] == Settings.LIST_PROP:
                l = []
                for i in self._configparser.get(section, prop).split(","):
                    l.append(self.__parseStr(i))
                self.__cache[section][prop] = l
            else:
                self.__cache[section][prop] = self._configparser.get(section, prop)
        return self.__cache[section][prop]

    @staticmethod
    def __parseStr(s: str) -> str:
        return s.replace("%%USERDIR%%", userDir).replace("%%BASE%%", baseDir).replace("%%USERBIOSDIR%%", userBiosDir).replace("%%USERCONFDIR%%", userConfDir)

class UserSettings(Settings):

    DATE_FORMATS = {
        "dd/mm/yyyy": "%d/%m/%Y",
        "dd/mm/yy": "%d/%m/%y",
        "mm/dd/yyyy": "%m/%d/%Y",
        "mm/dd/yy": "%m/%d/%y"
    }

    def __init__(self):
        props = {
            "RetroAchievements": {
                "apiKey": Settings.STR_PROP,
                "hardcore": Settings.BOOL_PROP,
                "username": Settings.STR_PROP,
                "password": Settings.STR_PROP
            },
            "settings": {
                "bluetooth": Settings.BOOL_PROP,
                "dateFormat": Settings.STR_PROP,
                "hdmi-cec": Settings.BOOL_PROP,
                "romScraper": Settings.STR_PROP,
                "screenSaverTimeout": Settings.INT_PROP
            },
            "webServer": {
                "enabled": Settings.BOOL_PROP,
                "port": Settings.INT_PROP
            }
        }
        super().__init__(userPesConfigFile, props)

    def get(self, section: str, prop: str) -> str:
        rslt = super().get(section, prop)
        if self.getType(section, prop) == Settings.STR_PROP:
            if rslt is None or len(rslt) == 0:
                return None
            return rslt.replace("%%USERDIR%%", userDir)
        return rslt

    @property
    def bluetooth(self) -> bool:
        value = self.get("settings", "bluetooth")
        if value is None:
            logging.warning("UserSettings.bluetooth: Bluetooth setting is not defined, defaulting to true")
            value = True
        return value

    @bluetooth.setter
    def bluetooth(self, value: bool):
        self.set("settings", "bluetooth", value)

    @property
    def dateFormat(self) -> str:
        value = self.get("settings", "dateFormat")
        if value is None:
            value = next(iter(UserSettings.DATE_FORMATS[0]))
            logging.warning("UserSettings.bluetooth: dateTimeFormat is not defined, defaulting to \"%s\"", value)
        elif value not in UserSettings.DATE_FORMATS:
            logging.error("UserSettings.dateFormat: invalid value: \"%s\", resetting to default", value)
            value = next(iter(UserSettings.DATE_FORMATS[0]))
        return value

    @dateFormat.setter
    def dateFormat(self, value: str):
        if value not in UserSettings.DATE_FORMATS:
            raise ValueError(f"Invalid value for UserSettings.dateFormat: \"{value}\"")
        self.set("settings", "dateFormat", value)

    @property
    def hdmiCec(self) -> bool:
        return self.get("settings", "hdmi-cec")

    @hdmiCec.setter
    def hdmiCec(self, value: bool):
        self.set("settings", "hdmi-cec", value)

    @property
    def kodiCommand(self) -> str:
        return self.get("commands", "kodi")

    @property
    def hardcore(self) -> bool:
        value = self.get("RetroAchievements", "hardcore")
        if value is None:
            logging.warning("UserSettings.hardcore: RetroAchievements hardcore setting is not defined, defaulting to false")
            value = False
        return value

    @hardcore.setter
    def hardcore(self, value: str):
        self.set("RetroAchievements", "hardcore", value)

    @property
    def pythonDateFormat(self) -> str:
        return UserSettings.DATE_FORMATS[self.dateFormat]

    @property
    def rebootCommand(self) -> str:
        return self.get("commands", "reboot")

    @property
    def setTimezoneCommand(self) -> str:
        return self.get("commands", "setTimezone")

    @property
    def shutdownCommand(self) -> str:
        return self.get("commands", "shutdown")
