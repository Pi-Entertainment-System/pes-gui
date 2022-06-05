#!/usr/bin/env python3

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

# pylint: disable=broad-except,invalid-name,line-too-long,missing-class-docstring,missing-function-docstring

"""
This module is the entry point for the PES application.
It bootstraps the GUI and loads it.
"""

import argparse
import logging
import os
import shutil
import sys

import pes
import pes.retroachievement
import pes.sql
import pes.web
import sdl2

from pes.common import checkDir, checkFile, mkdir, initConfig, initDb, pesExit, UserSettings
from pes.gui import Backend, PESGuiApplication
from sqlalchemy.orm import sessionmaker

coloredlogsImported = False
try:
    import coloredlogs
    coloredlogsImported = True
except ImportError as e:
    pass

cecImported = False
try:
    import cec
    cecImported = True
except ImportError as e:
    pass

def cecEvent(button, dur):
    """
    Wrapper function to work around segmentation fault
    when adding Qt app as the callback.
    """
    # pylint: disable=global-statement
    global app
    if app:
        app.processCecEvent(button, dur)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Launch the Pi Entertainment System (PES)', add_help=True)
    parser.add_argument('-v', '--verbose', help='Turn on debug messages', dest='verbose', action='store_true')
    parser.add_argument('-l', '--log', help='File to log messages to', type=str, dest='logfile')
    args = parser.parse_args()

    logLevel = logging.INFO
    logFormat = "%(asctime)s:%(levelname)s: %(message)s"
    logDateFormat = "%Y/%m/%d %H:%M:%S"
    if args.verbose:
        logLevel = logging.DEBUG

    if args.logfile:
        logging.basicConfig(format=logFormat, datefmt=logDateFormat, level=logLevel, filename=args.logfile)
    else:
        logging.basicConfig(format=logFormat, datefmt=logDateFormat, level=logLevel)

    if coloredlogsImported:
        logger = logging.getLogger(__name__)
        coloredlogs.install(fmt=logFormat, datefmt=logDateFormat, level=logLevel, logger=logger)

    logging.debug("PES %s, date: %s, author: %s", pes.VERSION_NUMBER, pes.VERSION_DATE, pes.VERSION_AUTHOR)
    logging.debug("base dir: %s", pes.baseDir)

    checkDir(pes.baseDir)
    checkFile(pes.qmlMain)
    checkDir(pes.qmlDir)
    checkDir(pes.webDir)
    logging.debug("config dir: %s", pes.confDir)
    checkDir(pes.confDir)
    logging.debug("user dir: %s", pes.userDir)
    mkdir(pes.userDir)
    mkdir(pes.userBadgeDir)
    mkdir(pes.userBiosDir)
    mkdir(pes.userConfDir)
    mkdir(pes.userCoverartDir)
    mkdir(pes.userScreenshotDir)
    mkdir(pes.userRetroArchConfDir)
    mkdir(pes.userRetroArchJoysticksConfDir)
    mkdir(pes.userRetroArchRguiConfDir)
    mkdir(pes.userRomDir)
    initConfig()
    initDb()

    checkFile(pes.userPesConfigFile)
    checkFile(pes.userDb)
    checkFile(pes.userConsolesConfigFile)
    checkFile(pes.userGameControllerFile)
    # look for rasum in $PATH
    if shutil.which("rasum") is None:
        pesExit("Error: could not find rasum executable in $PATH", True)

    logging.info("loading settings...")
    checkFile(pes.userPesConfigFile)
    userSettings = UserSettings()

    # make directory for each support console
    logging.debug("connecting to database: %s", pes.userDb)
    engine = pes.sql.connect(pes.userDb)
    session = sessionmaker(bind=engine)()
    pes.sql.createAll(engine)
    consoles = session.query(pes.sql.Console).all()
    logging.debug("creating ROM directories for user")
    for c in consoles:
        mkdir(os.path.join(pes.userRomDir, c.name))
        mkdir(os.path.join(pes.userCoverartDir, c.name))
        mkdir(os.path.join(pes.userScreenshotDir, c.name))

    romScraper = userSettings.get("settings", "romScraper")
    if romScraper is None:
        logging.warning("Could not find \"romScraper\" parameter in \"settings\" section in %s. Adding default setting: %s.", pes.userPesConfigFile, pes.romScrapers[0])
        userSettings.set("settings", "romScraper", pes.romScrapers[0])
        userSettings.save()
    elif romScraper not in pes.romScrapers:
        pesExit("Unknown romScraper value: \"%s\" in \"settings\" section in %s" % (romScraper, pes.userPesConfigFile))

    backend = Backend()

    # enable web server?
    if userSettings.get("webServer", "enabled"):
        try:
            webPort = int(userSettings.get("webServer", "port"))
        except Exception as e:
            logging.error("Could not determine web port from %s", pes.userPesConfigFile)
        try:
            webThread = pes.web.WebThread(webPort, backend)
            webThread.start()
        except Exception as e:
            logging.error("Failed to start web server: %s", e)
    else:
        logging.info("web server disabled")

    if sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER) != 0:
        pesExit("Failed to initialise SDL")

    logging.debug("loading SDL2 control pad mappings from: %s", pes.userGameControllerFile)
    mappingsLoaded = sdl2.SDL_GameControllerAddMappingsFromFile(pes.userGameControllerFile.encode())
    if mappingsLoaded == -1:
        pes.common.pesExit("failed to load SDL2 control pad mappings from: %s" % pes.userGameControllerFile)
    logging.debug("loaded %d control pad mappings", mappingsLoaded)

    app = PESGuiApplication(sys.argv, backend)

    userCecEnabled = userSettings.get("settings", "hdmi-cec")
    if cecImported and (userCecEnabled or userCecEnabled is None):
        logging.debug("creating CEC config...")
        cecconfig = cec.libcec_configuration()
        cecconfig.strDeviceName   = "PES"
        cecconfig.bActivateSource = 0
        cecconfig.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
        cecconfig.clientVersion = cec.LIBCEC_VERSION_CURRENT
        logging.debug("adding CEC callback...")
        cecconfig.SetKeyPressCallback(cecEvent)
        lib = cec.ICECAdapter.Create(cecconfig)
        logging.debug("looking for CEC adapters...")
        adapters = lib.DetectAdapters()
        adapterCount = len(adapters)
        if adapterCount == 0:
            logging.warning("could not find any CEC adapters!")
        else:
            logging.debug("found %d CEC adapters, attempting to open first adapter...", adapterCount)
            if lib.Open(adapters[0].strComName):
                logging.debug("CEC adapter opened")
            else:
                logging.error("unable to open CEC adapter!")
    else:
        logging.warning("CEC module disabled")

    app.run()

    if cecImported:
        # remove CEC callbacks to prevent segmentation fault issue #6
        logging.debug("removing CEC callbacks...")
        cecconfig.ClearCallbacks()
    logging.info("exiting...")
