#
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020-2023 Neil Munday (neil@mundayweb.com)
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

# pylint: disable=broad-exception-raised,invalid-name,line-too-long,missing-class-docstring,missing-function-docstring,too-many-branches,too-many-instance-attributes,too-few-public-methods,too-many-public-methods,too-many-nested-blocks,too-many-return-statements,too-many-statements,wrong-import-position

"""
This module creates the PES GUI.
"""

# standard imports
import datetime
import logging
import os

# third-party imports
import sdl2
import sdl2.ext
import sdl2.joystick
import sqlalchemy.orm

from PyQt5.QtGui import QGuiApplication, QKeyEvent
from PyQt5.QtQml import QQmlApplicationEngine, QJSValue, qmlRegisterType
from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal, pyqtSlot, QObject, QEvent, QVariant

cecImported = False
try:
    import cec
    cecImported = True
except ImportError:
    pass

# pes imports
import pes
import pes.common
import pes.controlpad
import pes.retroachievement
import pes.romscan
import pes.sql
import pes.system

JOYSTICK_AXIS_MIN = -30000
JOYSTICK_AXIS_MAX =  30000

def getLitteEndianFromHex(x):
    return int(f"{x[2:4]}{x[0:2]}", 16)

# workaround for http://bugs.python.org/issue22273
# thanks to https://github.com/GreatFruitOmsk/py-sdl2/commit/e9b13cb5a13b0f5265626d02b0941771e0d1d564
def getJoystickGUIDString(guid):
    s = ''
    for g in guid.data:
        s += "{:x}".format(g >> 4) # pylint: disable=consider-using-f-string
        s += "{:x}".format(g & 0x0F) # pylint: disable=consider-using-f-string
    return s

def getJoystickDeviceInfoFromGUID(guid):
    vendorId = guid[8:12]
    productId = guid[16:20]
    #print("%s\n%s" % (vendorId, productId))
    # swap from big endian to little endian and covert to an int
    vendorId = getLitteEndianFromHex(vendorId)
    productId = getLitteEndianFromHex(productId)
    return (vendorId, productId)

def getRetroArchConfigAxisValue(param, controller, axis, both=False):
    bind = sdl2.SDL_GameControllerGetBindForAxis(controller, axis)
    if bind:
        if bind.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_AXIS:
            if both:
                return f"{param}_plus_axis = \"+{bind.value.axis}\"\n{param}_minus_axis = \"-{bind.value.axis}\"\n"
            return f"{param}_axis = \"+{bind.value.axis}\"\n"
        if bind.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_BUTTON:
            return f"{param}_btn = \"{bind.value.button}\"\n"

    if both:
        return f"{param}_plus_axis = \"nul\"\n{param}_minus_axis = \"nul\"\n"
    return f"{param} = \"nul\"\n"

def getRetroArchConfigButtonValue(param, controller, button):
    bind = sdl2.SDL_GameControllerGetBindForButton(controller, button)
    if bind:
        if bind.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_BUTTON:
            return f"{param}_btn = \"{bind.value.button}\"\n"
        if bind.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_AXIS:
            #return PESApp.getRetroArchConfigAxisValue(param, controller, bind.value.axis)
            if button in [sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT]:
                return f"{param}_axis = \"-{bind.value.axis}\"\n"
            return f"{param}_axis = \"+{bind.value.axis}\"\n"
        if bind.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT:
            if button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                return f"{param}_btn = \"h{bind.value.hat.hat}up\"\n"
            if button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                return f"{param}_btn = \"h{bind.value.hat.hat}down\"\n"
            if button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                return f"{param}_btn = \"h{bind.value.hat.hat}left\"\n"
            if button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                return f"{param}_btn = \"h{bind.value.hat.hat}right\"\n"
    return f"{param} = \"nul\"\n"

class Backend(QObject):

    closeSignal = pyqtSignal()
    gamepadTotalSignal = pyqtSignal(int, arguments=['total'])

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__userSettings = pes.common.UserSettings()
        self.__consoleSettings = pes.common.ConsoleSettings()
        self.__updateDateTimeFormat()
        self.__dbusBroker = pes.system.DbusBroker()
        if self.__dbusBroker.btAvailable():
            self.__btAgent = pes.system.BluetoothAgent()
            # set-up Bluetooth so it can be paired etc.
            self.__dbusBroker.btPowered = True
            self.__dbusBroker.btDiscoverable = True
            self.__dbusBroker.btDiscoverableTimeout = 0
            self.__dbusBroker.btPairable = True
            self.__dbusBroker.btStartDiscovery()
        else:
            self.__btAgent = None
        self.__screenSaverTimeout = self.__userSettings.get("settings", "screenSaverTimeout")
        self.__gamepadTotal = 0
        logging.debug("Backend.__init__: connecting to database: %s", pes.userDb)
        #self.__romscanThread = None

    @pyqtSlot(result=bool)
    def btAvailable(self):
        return self.__dbusBroker.btAvailable()

    @pyqtProperty(bool, constant=True)
    def cecEnabled(self):
        return cecImported

    @pyqtSlot()
    def close(self):
        logging.debug("Backend.close: closing...")
        self.closeSignal.emit()

    @staticmethod
    def __createCommandFile(command):
        logging.debug("Backend.__createCommandFile: creating %s", pes.userScriptFile)
        with open(pes.userScriptFile, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write("# THIS FILE WAS AUTOMATICALLY CREATED BY PES\n")
            f.write(f"{command}\n")
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                f.write("exec pes -v\n")
            else:
                f.write("exec pes\n")
        os.chmod(pes.userScriptFile, 0o700)
        logging.debug("Backend.__createCommandFile: done")

    @pyqtSlot(int, bool)
    def favouriteGame(self, gameId, favourite):
        logging.debug("Backend.favouriteGame: %d -> %s", gameId, favourite)
        with pes.sql.Session.begin() as session:
            game = session.query(pes.sql.Game).get(gameId)
            if game:
                game.favourite = favourite
                session.add(game)
            else:
                logging.error("Backend.favouriteGame: could not find game with ID: %d", gameId)

    @pyqtProperty(int)
    def gamepadTotal(self):
        return self.__gamepadTotal

    @gamepadTotal.setter
    def gamepadTotal(self, total):
        self.__gamepadTotal = total
        self.gamepadTotalSignal.emit(total)

    @pyqtSlot(result=list)
    def getAvailableTimezones(self):
        logging.debug("Backend.getAvailableTimeZones: getting time zones")
        return self.__dbusBroker.getTimezones()

    @pyqtSlot(result=bool)
    def getBluetoothEnabled(self):
        logging.debug("Backend.getBluetoothEnabled: called")
        return self.__userSettings.bluetooth

    @pyqtSlot(int, result=str)
    def getConsoleArt(self, consoleId):
        logging.debug("Backend.getConsoleArt: getting console art URL for %d", consoleId)
        with pes.sql.Session() as session:
            console = session.query(pes.sql.Console).get(consoleId)
            if console:
                path = os.path.join(pes.imagesDir, console.art)
                logging.debug("Backend.getConsoleArt: path is %s", path)
                return path
        logging.error("Backend.getConsoleArt: could not find console with ID: %d", consoleId)
        return None

    @pyqtSlot(int, result=str)
    def getConsole(self, consoleId):
        logging.debug("Backend.getConsole: getting console with ID: %d", consoleId)
        with pes.sql.Session() as session:
            console = session.query(pes.sql.Console).get(consoleId)
            if console:
                return console.getDict()
        logging.error("Backend.getConsole: could not find console with ID: %d", consoleId)
        return None

    @pyqtSlot(bool, result=list)
    def getConsoles(self, withGames=False):
        logging.debug("Backend.getConsoles: getting consoles, withGames = %s", withGames)
        consoleList = []
        with pes.sql.Session() as session:
            if withGames:
                result = session.query(pes.sql.Console).join(pes.sql.Game).order_by(pes.sql.Console.name).all()
            else:
                result = session.query(pes.sql.Console).order_by(pes.sql.Console.name).all()
            for c in result:
                consoleList.append(c.getDict())
        return consoleList

    @pyqtSlot(result=str)
    def getDateFormat(self):
        logging.debug("Backed.getDateFormat: called")
        return self.__userSettings.dateFormat

    @pyqtSlot(result=list)
    def getDateFormats(self):
        logging.debug("Backend.getDateFormats: called")
        return list(self.__userSettings.DATE_FORMATS.keys())

    @pyqtSlot(int, result=QVariant)
    def getGame(self, gameId):
        logging.debug("Backend.getGame: getting game: %d", gameId)
        with pes.sql.Session() as session:
            game = session.query(pes.sql.Game).get(gameId)
            if game:
                return game.getDict()
        logging.error("Backend.getGame: could not find game for: %d", gameId)
        return None

    @pyqtSlot(int, result=list)
    def getFavouriteGames(self, consoleId=None):
        games = []
        with pes.sql.Session() as session:
            if not consoleId or consoleId == 0:
                logging.debug("Backand.getFavouriteGames: getting favourite games for all consoles")
                result = session.query(pes.sql.Game).filter(pes.sql.Game.favourite).order_by(pes.sql.Game.name)
            else:
                logging.debug("Backend.getFavouriteGames: getting favourite games for console %d", consoleId)
                result = session.query(pes.sql.Game).filter(sqlalchemy.sql.expression.and_(pes.sql.Game.consoleId == consoleId, pes.sql.Game.favourite)).order_by(pes.sql.Game.name)
            for g in result:
                games.append(g.getDict())
        return games

    @pyqtSlot(int, result=list)
    def getGames(self, consoleId):
        logging.debug("Backend.getGames: getting games for console %d", consoleId)
        games = []
        with pes.sql.Session() as session:
            result = session.query(pes.sql.Game).filter(pes.sql.Game.consoleId == consoleId).order_by(pes.sql.Game.name)
            for g in result:
                games.append(g.getDict())
        return games

    @pyqtSlot(result=bool)
    def getHardcoreMode(self):
        logging.debug("Backend.getHardcoreMode: called")
        return self.__userSettings.hardcore

    @pyqtSlot(result=bool)
    def getHdmiCecEnabled(self):
        logging.debug("Backend.getHdmiCecEnabled: called")
        return self.__userSettings.hdmiCec

    @pyqtSlot(int, int, result=list)
    def getMostPlayedGames(self, consoleId=None, limit=10):
        games = []
        with pes.sql.Session() as session:
            if not consoleId or consoleId == 0:
                logging.debug("Backand.getMostPlayedGames: getting most played games for all consoles")
                result = session.query(pes.sql.Game).filter(pes.sql.Game.playCount > 0).order_by(pes.sql.Game.playCount)
                if limit > 0:
                    result = result.limit(limit)
            else:
                logging.debug("Backend.getMostPlayedGames: getting most played games for console %d", consoleId)
                result = session.query(pes.sql.Game).filter(sqlalchemy.sql.expression.and_(pes.sql.Game.consoleId == consoleId, pes.sql.Game.playCount > 0)).order_by(pes.sql.Game.playCount)
                if limit > 0:
                    result = result.limit(limit)
            for g in result:
                games.append(g.getDict())
        return games

    @pyqtSlot(result=bool)
    def getNetworkAvailable(self):
        return pes.common.getIpAddress() != "127.0.0.1"

    @pyqtSlot(int, int, result=list)
    def getRecentlyAddedGames(self, consoleId=None, limit=10):
        games = []
        with pes.sql.Session() as session:
            if not consoleId or consoleId == 0:
                logging.debug("Backend.getRecentlyAddedGames: getting games for all consoles")
                result = session.query(pes.sql.Game).order_by(pes.sql.Game.added.desc())
                if limit > 0:
                    result = result.limit(limit)
            else:
                logging.debug("Backend.getRecentlyAddedGames: getting games for console %d", consoleId)
                result = session.query(pes.sql.Game).filter(pes.sql.Game.consoleId == consoleId).order_by(pes.sql.Game.added.desc())
                if limit > 0:
                    result = result.limit(limit)
            for g in result:
                games.append(g.getDict())
        return games

    @pyqtSlot(int, int, result=list)
    def getRecentlyPlayedGames(self, consoleId=None, limit=10):
        games = []
        with pes.sql.Session() as session:
            if not consoleId or consoleId == 0:
                logging.debug("Backend.getRecentlyPlayedGames: getting games for all consoles")
                result = session.query(pes.sql.Game).filter(pes.sql.Game.playCount > 0).order_by(pes.sql.Game.lastPlayed.desc())
                if limit > 0:
                    result = result.limit(limit)
            else:
                logging.debug("Backend.getRecentlyPlayedGames: getting games for console %d", consoleId)
                result = session.query(pes.sql.Game).filter(pes.sql.Game.consoleId == consoleId).filter(pes.sql.Game.playCount > 0).order_by(pes.sql.Game.lastPlayed.desc())
                if limit > 0:
                    result = result.limit(limit)
            for g in result:
                games.append(g.getDict())
        return games

    @pyqtSlot(result=int)
    def getScreenSaverTimeout(self):
        return self.__screenSaverTimeout

    @pyqtSlot(result=str)
    def getTime(self):
        return datetime.datetime.now().strftime(self.__dateTimeFormat)

    @pyqtSlot(result=str)
    def getTimezone(self):
        return self.__dbusBroker.timezone

    @pyqtSlot()
    def loadKodi(self):
        self.__createCommandFile(self.__userSettings.kodiCommand)
        self.close()

    @pyqtSlot(int, result=QVariant)
    def playGame(self, gameId):
        # pylint: disable=too-many-locals
        gameName = None
        with pes.sql.Session.begin() as session:
            game = session.query(pes.sql.Game).get(gameId)
            if not game:
                logging.error("Backend.playGame: could not find game ID %d", gameId)
                return { "result": False, "msg": f"Could not find game {gameId}" }

            logging.debug("Backend.playGame: found game ID %d", gameId)
            gameName = game.name
            requireFiles = self.__consoleSettings.get(game.console.name, "require")
            if requireFiles:
                for f in requireFiles:
                    f = f.strip()
                    logging.debug("Backend.playGame: checking for: %s", f)
                    if not os.path.exists(f) or not os.path.isfile(f):
                        logging.error("Backend.playGame: could not find required file: %s", f)
                        return { "result": False, "msg": f"Could not find required file: {f}"}
            else:
                logging.debug("Backend.playGame: no required files for console %s", game.console.name)

            # generate emulator config
            emulator = self.__consoleSettings.get(game.console.name, "emulator")
            if emulator == "RetroArch":
                # note: RetroArch uses a SNES control pad button layout, SDL2 uses XBOX 360 layout!
                # check joystick configs
                joystickTotal = sdl2.joystick.SDL_NumJoysticks()
                if joystickTotal > 0:
                    for i in range(joystickTotal):
                        if sdl2.SDL_IsGameController(i):
                            c = sdl2.SDL_GameControllerOpen(i)
                            if sdl2.SDL_GameControllerGetAttached(c):
                                # get joystick name
                                j = sdl2.SDL_GameControllerGetJoystick(c)
                                jsName = sdl2.SDL_JoystickName(j).decode()
                                jsConfig = os.path.join(pes.userRetroArchJoysticksConfDir, f"{jsName}.cfg")
                                logging.debug("Backend.playGame: creating configuration file %s for %s", jsConfig, jsName)
                                vendorId, productId = getJoystickDeviceInfoFromGUID(getJoystickGUIDString(sdl2.SDL_JoystickGetDeviceGUID(i)))
                                with open(jsConfig, "w", encoding="utf-8") as f:
                                    # control pad id etc.
                                    f.write(f"input_device = \"{jsName}\"\n")
                                    f.write(f"input_vendor_id = \"{vendorId}\"\n")
                                    f.write(f"input_product_id = \"{productId}\"\n")
                                    #f.write("input_driver = \"udev\"\n")
                                    # buttons
                                    f.write(getRetroArchConfigButtonValue("input_a", c, sdl2.SDL_CONTROLLER_BUTTON_B))
                                    f.write(getRetroArchConfigButtonValue("input_b", c, sdl2.SDL_CONTROLLER_BUTTON_A))
                                    f.write(getRetroArchConfigButtonValue("input_x", c, sdl2.SDL_CONTROLLER_BUTTON_Y))
                                    f.write(getRetroArchConfigButtonValue("input_y", c, sdl2.SDL_CONTROLLER_BUTTON_X))
                                    f.write(getRetroArchConfigButtonValue("input_start", c, sdl2.SDL_CONTROLLER_BUTTON_START))
                                    f.write(getRetroArchConfigButtonValue("input_select", c, sdl2.SDL_CONTROLLER_BUTTON_BACK))
                                    # shoulder buttons
                                    f.write(getRetroArchConfigButtonValue("input_l", c, sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER))
                                    f.write(getRetroArchConfigButtonValue("input_r", c, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER))
                                    f.write(getRetroArchConfigAxisValue("input_l2", c, sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT))
                                    f.write(getRetroArchConfigAxisValue("input_r2", c, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT))
                                    # L3/R3 buttons
                                    f.write(getRetroArchConfigButtonValue("input_l3", c, sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK))
                                    f.write(getRetroArchConfigButtonValue("input_r3", c, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK))
                                    # d-pad buttons
                                    f.write(getRetroArchConfigButtonValue("input_up", c, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP))
                                    f.write(getRetroArchConfigButtonValue("input_down", c, sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN))
                                    f.write(getRetroArchConfigButtonValue("input_left", c, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT))
                                    f.write(getRetroArchConfigButtonValue("input_right", c, sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT))
                                    # axis
                                    f.write(getRetroArchConfigAxisValue("input_l_x", c, sdl2.SDL_CONTROLLER_AXIS_LEFTX, True))
                                    f.write(getRetroArchConfigAxisValue("input_l_y", c, sdl2.SDL_CONTROLLER_AXIS_LEFTY, True))
                                    f.write(getRetroArchConfigAxisValue("input_r_x", c, sdl2.SDL_CONTROLLER_AXIS_RIGHTX, True))
                                    f.write(getRetroArchConfigAxisValue("input_r_y", c, sdl2.SDL_CONTROLLER_AXIS_RIGHTY, True))
                                    # hot key buttons
                                    bind = sdl2.SDL_GameControllerGetBindForButton(c, sdl2.SDL_CONTROLLER_BUTTON_GUIDE)
                                    if bind:
                                        f.write(getRetroArchConfigButtonValue("input_enable_hotkey", c, sdl2.SDL_CONTROLLER_BUTTON_GUIDE))
                                    else:
                                        f.write(getRetroArchConfigButtonValue("input_enable_hotkey", c, sdl2.SDL_CONTROLLER_BUTTON_BACK))
                                    f.write(getRetroArchConfigButtonValue("input_menu_toggle", c, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP))
                                    f.write(getRetroArchConfigButtonValue("input_exit_emulator", c, sdl2.SDL_CONTROLLER_BUTTON_START))
                                    f.write(getRetroArchConfigButtonValue("input_save_state", c, sdl2.SDL_CONTROLLER_BUTTON_A))
                                    f.write(getRetroArchConfigButtonValue("input_load_state", c, sdl2.SDL_CONTROLLER_BUTTON_B))
                                    f.write("input_pause_toggle = \"nul\"\n")
                            sdl2.SDL_GameControllerClose(c)

                # now set-up RetroAchievements
                retroUser = self.__userSettings.get("RetroAchievements", "username")
                retroPass = self.__userSettings.get("RetroAchievements", "password")
                s = "# THIS FILE IS AUTOMATICALLY GENERATED BY PES!\n"
                if retroUser is None or retroPass is None:
                    s += "cheevos_enable = false\n"
                else:
                    s += f"cheevos_username = {retroUser}\n"
                    s += f"cheevos_password = {retroPass}\n"
                    s += "cheevos_enable = true\n"
                    if self.__userSettings.get("RetroAchievements", "hardcore"):
                        s += "cheevos_hardcore_mode_enable = true\n"
                    else:
                        s += "cheevos_hardcore_mode_enable = false\n"
                with open(pes.userRetroArchCheevosConfFile, "w", encoding="utf-8") as f:
                    f.write(s)

            # get emulator launch string
            command = self.__consoleSettings.get(game.console.name, "command").replace("%%GAME%%", f"\"{game.path}\"")
            if not command:
                logging.error("Backend.playGame: could not determine launch command for the %s console", game.console.name)
                return { "result": False, "msg": f"Could not determine launch command for the {game.console.name} console" }
            logging.debug("Backend.playGame: launch string: %s", command)
            self.__createCommandFile(command)
            logging.debug("Backend.playGame: updating play count for %s", game.name)
            game.playCount += 1
            game.lastPlayed = datetime.datetime.now()
            session.add(game)
        logging.debug("Backend.playGame: done")
        self.close()
        return { "result": True, "msg": f"Loading {gameName}" }

    @pyqtSlot()
    def reboot(self):
        logging.info("Rebooting")
        pes.common.runCommand(self.__userSettings.rebootCommand)

    @pyqtSlot(bool, bool)
    def resetData(self, resetConfig, resetDatabase):
        command = ""
        if resetConfig:
            logging.debug("Backend.resetData: user configuration will be deleted")
            command += f"rm -rf {pes.userConfDir}/*\n"
        if resetDatabase:
            logging.debug("Backend.resetData: PES database will be deleted")
            command += f"rm -f {pes.userDb}\n"
        self.__createCommandFile(command)
        self.close()

    @pyqtSlot(QJSValue)
    def saveSettings(self, settings):
        # pylint: disable=comparison-with-callable
        logging.info("Saving settings")
        settings = settings.toVariant()
        logging.debug("Backend.saveSettings: %s", settings)
        self.__userSettings.bluetooth = settings["bluetoothEnabled"]
        self.__userSettings.dateFormat = settings["dateFormat"]
        self.__userSettings.hardcore = settings["hardcoreEnabled"]
        self.__userSettings.hdmiCec = settings["hdmiCecEnabled"]
        self.__updateDateTimeFormat()
        self.__userSettings.save()
        if self.__btAgent:
            self.__dbusBroker.btPowered = self.__userSettings.bluetooth
        if self.getTimezone() != settings["timezone"]: # generates comparison-with-callable pylint warning
            logging.debug("Backend.saveSettings: changing timezone")
            pes.common.runCommand(f"{self.__userSettings.setTimezoneCommand} {settings['timezone']}")

    @pyqtSlot()
    def shutdown(self):
        logging.info("Shutting down...")
        pes.common.runCommand(self.__userSettings.shutdownCommand)

    def __updateDateTimeFormat(self):
        self.__dateTimeFormat = f"{self.__userSettings.pythonDateFormat} %H:%M:%S"
        pes.sql.CustomBase.DATE_TIME_FORMAT = f"{self.__userSettings.pythonDateFormat} %H:%M"

class KeyboardEmitter(QObject):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.__app = app
        logging.debug("KeyboardEmitter.__init__: created")

    @pyqtSlot(int)
    def keyPress(self, key):
        event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
        logging.debug("KeyboardEmitter.keyPress: %s", key)
        self.__app.sendEvent(self.__app.focusWindow(), event)

class PESGuiApplication(QGuiApplication):
    # pylint: disable=unused-private-member

    def __init__(self, argv, backend, windowed=False):
        super().__init__(argv)
        self.setOverrideCursor(Qt.BlankCursor) # hide mouse pointer
        self.__windowed = windowed
        self.__running = True
        self.__player1Controller = None
        self.__player1ControllerIndex = None
        self.__engine = None
        self.__backend = backend
        self.__backend.closeSignal.connect(self.close)
        self.__keyboardEmitter = KeyboardEmitter(self)
        qmlRegisterType(pes.controlpad.ControlPad, 'ControlPad', 1, 0, 'ControlPad')
        qmlRegisterType(pes.controlpad.ControlPadManager, 'ControlPadManager', 1, 0, 'ControlPadManager')
        qmlRegisterType(pes.romscan.RomScanMonitorThread, 'RomScanMonitorThread', 1, 0, 'RomScanMonitorThread')
        qmlRegisterType(pes.retroachievement.RetroAchievementUser, 'RetroAchievementUser', 1, 0, 'RetroAchievementUser')
        qmlRegisterType(pes.retroachievement.RetroAchievementThread, 'RetroAchievementThread', 1, 0, 'RetroAchievementThread')
        self.__engine = QQmlApplicationEngine()
        self.__engine.rootContext().setContextProperty("backend", self.__backend)
        self.__engine.rootContext().setContextProperty("keyboardEmitter", self.__keyboardEmitter)
        logging.debug("loading QML from: %s", pes.qmlMain)
        self.__engine.load(pes.qmlMain)

    def close(self):
        logging.debug("closing")
        self.__running = False
        sdl2.SDL_Quit()
        self.exit()

#    @staticmethod
#    def getControlPadPower(controlpad):
#        power = sdl2.SDL_JoystickCurrentPowerLevel(sdl2.SDL_GameControllerGetJoystick(controlpad))
#        if power == sdl2.SDL_JOYSTICK_POWER_UNKNOWN:
#            logging.debug("PESGuiApplication.getControlPadPower: unknown")
#            return -1
#        if power == sdl2.SDL_JOYSTICK_POWER_WIRED:
#            logging.debug("PESGuiApplication.getControlPadPower: wired")
#            return 101
#        if power == sdl2.SDL_JOYSTICK_POWER_MAX:
#            logging.debug("PESGuiApplication.getControlPadPower: max")
#            return 100
#        if power == sdl2.SDL_JOYSTICK_POWER_MEDIUM:
#            logging.debug("PESGuiApplication.getControlPadPower: medium")
#            return 70
#        if power == sdl2.SDL_JOYSTICK_POWER_LOW:
#            logging.debug("PESGuiApplication.getControlPadPower: low")
#            return 20
#        if power == sdl2.SDL_JOYSTICK_POWER_EMPTY:
#            logging.debug("PESGuiApplication.getControlPadPower: empty")
#            return 5
#        return -1

    def processCecEvent(self, button, dur):
        if not cecImported:
            raise Exception("PESGuiApplication.processCecEvent: CEC module not imported")
        if dur > 0:
            logging.debug("PESGuiApplication.processCecEvent: button %s", button)
            if button == cec.CEC_USER_CONTROL_CODE_UP:
                self.__keyboardEmitter.keyPress(Qt.Key_Up)
            elif button == cec.CEC_USER_CONTROL_CODE_DOWN:
                self.__keyboardEmitter.keyPress(Qt.Key_Down)
            elif button == cec.CEC_USER_CONTROL_CODE_LEFT:
                self.__keyboardEmitter.keyPress(Qt.Key_Left)
            elif button == cec.CEC_USER_CONTROL_CODE_RIGHT:
                self.__keyboardEmitter.keyPress(Qt.Key_Right)
            elif button == cec.CEC_USER_CONTROL_CODE_SELECT:
                self.__keyboardEmitter.keyPress(Qt.Key_Return)
            elif button in [cec.CEC_USER_CONTROL_CODE_AN_RETURN, cec.CECDEVICE_RESERVED2]:
                self.__keyboardEmitter.keyPress(Qt.Key_Backspace)

    def run(self):
        joystickTick = sdl2.timer.SDL_GetTicks()

        while self.__running:
            events = sdl2.ext.get_events()
            for event in events:
                if event.type == sdl2.SDL_CONTROLLERBUTTONUP and event.cbutton.state == sdl2.SDL_RELEASED:
                    pes.controlpad.ControlPadManager.fireButtonEvent(event.cbutton.button)
                elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                    if event.caxis.value < JOYSTICK_AXIS_MIN or event.caxis.value > JOYSTICK_AXIS_MAX:
                        logging.debug("controller: axis \"%s\" activated: %d", sdl2.SDL_GameControllerGetStringForAxis(event.caxis.axis), event.caxis.value)
                        pes.controlpad.ControlPadManager.fireAxisEvent(event.caxis.axis, event.caxis.value)
                #elif event.type == sdl2.SDL_JOYHATMOTION:
                # NOTE: could be handling an already handled game controller event!
                #    if event.jhat.value == sdl2.SDL_HAT_UP:
                #        logging.debug("player (hat): up")
                #        self.__sendKeyEvent(Qt.Key_Up)
                #    elif event.jhat.value == sdl2.SDL_HAT_DOWN:
                #        logging.debug("player (hat): down")
                #        self.__sendKeyEvent(Qt.Key_Down)
                #    elif event.jhat.value == sdl2.SDL_HAT_LEFT:
                #        logging.debug("player (hat): left")
                #        self.__sendKeyEvent(Qt.Key_Left)
                #    elif event.jhat.value == sdl2.SDL_HAT_RIGHT:
                #        logging.debug("player (hat): right")
                #        self.__sendKeyEvent(Qt.Key_Right)

            if sdl2.timer.SDL_GetTicks() - joystickTick > 1000:
                tick = sdl2.timer.SDL_GetTicks()
                joystickTotal = sdl2.joystick.SDL_NumJoysticks()
                controlPadTotal = 0
                if joystickTotal > 0:
                    for i in range(joystickTotal):
                        if sdl2.SDL_IsGameController(i):
                            close = True
                            c = sdl2.SDL_GameControllerOpen(i)
                            if sdl2.SDL_GameControllerGetAttached(c):
                                controlPadTotal += 1
                                #logging.debug("PESWindow.run: %s is attached at %d", sdl2.SDL_GameControllerNameForIndex(i).decode(), i)
                                if self.__player1Controller is None:
                                    logging.debug("PESApp.run: switching player 1 to control pad #%d: %s (%s)", i, sdl2.SDL_GameControllerNameForIndex(i).decode(), getJoystickGUIDString(sdl2.SDL_JoystickGetDeviceGUID(i)))
                                    self.__player1ControllerIndex = i
                                    self.__player1Controller = c
                                    #self.__updateControlPad(self.__player1ControllerIndex)
                                    close = False
                            if close:
                                sdl2.SDL_GameControllerClose(c)
                else:
                    self.__player1Controller = None
                    self.__player1ControllerIndex = None
                joystickTick = tick
                if pes.controlpad.ControlPadManager.total != controlPadTotal:
                    pes.controlpad.ControlPadManager.fireTotalChangedEvent(controlPadTotal)

            self.processEvents()

    #def __updateControlPad(self, jsIndex):
    #    if jsIndex == self.__player1ControllerIndex:
    #        # hack for instances where a dpad is an axis
    #        bind = sdl2.SDL_GameControllerGetBindForButton(self.__player1Controller, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP)
    #        if bind:
    #            if bind.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_AXIS:
    #                self.__dpadAsAxis = True
    #                logging.debug("PESWindow.updateControlPad: enabling dpad as axis hack")
    #            else:
    #                self.__dpadAsAxis = False
