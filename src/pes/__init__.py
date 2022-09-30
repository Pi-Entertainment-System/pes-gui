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

# pylint: disable=invalid-name,line-too-long

"""
PES provides an interactive GUI for games console emulators
and is designed to work on the Raspberry Pi.
"""

# standard imports
import os

VERSION_NUMBER = '3.0'
VERSION_DATE = '2022-09-27'
VERSION_AUTHOR = 'Neil Munday'
VERSION_ARCH = 'any'

romScrapers = ['theGamesDb.net'] # list of ROM scrapers, default scraper is assumed to be at index 0

moduleDir = os.path.dirname(os.path.realpath(__file__))
baseDir = os.path.abspath(f'{moduleDir}/../../')
binDir = os.path.join(baseDir, 'bin')
confDir = os.path.join(baseDir, 'conf.d')
qmlDir = os.path.join(moduleDir, 'qml')
qmlMain = os.path.join(qmlDir, 'main.qml')
webDir = os.path.join(moduleDir, 'web')
dataDir = os.path.join(baseDir, 'data')
primaryDb = os.path.join(dataDir, 'pes.db')
resourcesDir = os.path.join(baseDir, 'resources')
userHomeDir = os.path.expanduser('~')
userDir = os.path.join(userHomeDir, 'pes')
userDb = os.path.join(userDir, 'pes.db')
userBiosDir = os.path.join(userDir, 'BIOS')
userLogDir = os.path.join(userDir, 'log')
userConfDir = os.path.join(userDir, 'conf.d')
userBadgeDir = os.path.join(userDir, 'badges')
userCoverartDir = os.path.join(userDir, 'coverart')
userScreenshotDir = os.path.join(userDir, 'screenshots')
userRomDir = os.path.join(userDir, 'roms')
userRetroArchConfDir = os.path.join(userConfDir, 'retroarch')
userRetroArchJoysticksConfDir = os.path.join(userRetroArchConfDir, 'joysticks')
userRetroArchRguiConfDir = os.path.join(userRetroArchConfDir, 'config')
userRetroArchCheevosConfFile = os.path.join(userRetroArchConfDir, 'cheevos.cfg')
userPesConfDir = os.path.join(userConfDir, 'pes')
userPesConfigFile = os.path.join(userPesConfDir, 'pes.ini')
userConsolesConfigFile = os.path.join(userPesConfDir, 'consoles.ini')
userGameControllerFile = os.path.join(userPesConfDir, 'gamecontrollerdb.txt')
userScriptFile = os.path.join(userDir, 'commands.sh')
cecEnabled = False
screenSaverTimeout = 0
