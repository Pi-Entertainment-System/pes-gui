#!/usr/bin/env python3

#
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

import argparse
import datetime
import logging
import pes
from pes.common import *
from pes.gui import BackEnd, PESGuiApplication
import pes.sql
import sdl2

from sqlalchemy.orm import sessionmaker

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Launch the Pi Entertainment System (PES)', add_help=True)
	parser.add_argument('-v', '--verbose', help='Turn on debug messages', dest='verbose', action='store_true')
	parser.add_argument('-l', '--log', help='File to log messages to', type=str, dest='logfile')
	args = parser.parse_args()

	logLevel = logging.INFO
	if args.verbose:
		logLevel = logging.DEBUG

	if args.logfile:
		logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel, filename=args.logfile)
	else:
		logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

	logging.debug("PES %s, date: %s, author: %s" % (pes.VERSION_NUMBER, pes.VERSION_DATE, pes.VERSION_AUTHOR))
	logging.debug("base dir: %s" % pes.baseDir)

	checkDir(pes.baseDir)
	checkFile(pes.qmlMain)
	checkDir(pes.qmlDir)
	logging.debug("config dir: %s" % pes.confDir)
	checkDir(pes.confDir)
	logging.debug("user dir: %s" % pes.userDir)
	mkdir(pes.userDir)
	mkdir(pes.userBiosDir)
	mkdir(pes.userConfDir)
	mkdir(pes.userRetroArchConfDir)
	mkdir(pes.userRetroArchJoysticksConfDir)
	mkdir(pes.userViceConfDir)
	initConfig()
	initDb()

	checkFile(pes.userPesConfigFile)
	checkFile(pes.userDb)
	checkFile(pes.userConsolesConfigFile)
	checkFile(pes.userGameControllerFile)
	#checkFile(pes.rasumExe)

	logging.info("loading settings...")
	checkFile(pes.userPesConfigFile)
	userSettings = UserSettings(pes.userPesConfigFile)
	covertArtDir = userSettings.get("settings", "coverartDir")
	if covertArtDir == None:
		pesExit("Could not find \"coverartDir\" parameter in \"settings\" section in %s" % pes.userPesConfigFile)
	logging.debug("cover art dir: %s" % covertArtDir)
	mkdir(covertArtDir)
	badgeDir = userSettings.get("settings", "badgeDir")
	if badgeDir == None:
		pesExit("Could not find \"badgeDir\" parameter in \"settings\" section in %s" % pes.userPesConfigFile)
	logging.debug("badge dir: %s" % badgeDir)
	mkdir(badgeDir)
	romsDir = userSettings.get("settings", "romsDir")
	if romsDir == None:
		pesExit("Could not find \"romsDir\" parameter in \"settings\" section in %s" % pes.userPesConfigFile)
	logging.debug("ROMs dir: %s" % romsDir)
	mkdir(romsDir)

	# make directory for each support console
	logging.debug("connecting to database: %s" % userDb)
	engine = pes.sql.connect(userDb)
	session = sessionmaker(bind=engine)()
	consoles = session.query(pes.sql.Console).all()
	logging.debug("creating ROM directories for user")
	for c in consoles:
		mkdir(os.path.join(romsDir, c.name))

	romScraper = userSettings.get("settings", "romScraper")
	if romScraper == None:
		logging.warning("Could not find \"romScraper\" parameter in \"settings\" section in %s. Adding default setting: %s." % (userPesConfigFile, romScrapers[0]))
		userSettings.set("settings", "romScraper", romScrapers[0])
		userSettings.save(userPesConfigFile)
	elif romScraper not in pes.romScrapers:
		pesExit("Unknown romScraper value: \"%s\" in \"settings\" section in %s" % (romScraper, userPesConfigFile, romScrapers[0]))

	if sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER) != 0:
		pesExit("Failed to initialise SDL")

	logging.debug("loading SDL2 control pad mappings from: %s" % pes.userGameControllerFile)
	mappingsLoaded = sdl2.SDL_GameControllerAddMappingsFromFile(pes.userGameControllerFile.encode())
	if mappingsLoaded == -1:
		pes.common.pesExit("failed to load SDL2 control pad mappings from: %s" % pes.userGameControllerFile)
	logging.debug("loaded %d control pad mappings" % mappingsLoaded)

	app = PESGuiApplication(sys.argv)
	app.run()
