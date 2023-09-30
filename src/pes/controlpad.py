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

# pylint: disable=invalid-name,too-few-public-methods

"""
This module provides control pad functionality for PES.
"""

import logging

# third-party imports
import sdl2

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Q_ENUMS, QObject

JOYSTICK_AXIS_MIN = -30000
JOYSTICK_AXIS_MAX =  30000

def getLitteEndianFromHex(x: str) -> int:
    """
    Returns the little endian value of the given
    hex value.
    """
    return int(f"{x[2:4]}{x[0:2]}", 16)

def getJoystickGUIDString(guid) -> str:
    """
    Returns the a string representation of the given 
    joystick GUID.
    """
    # pylint: disable=line-too-long
    # workaround for http://bugs.python.org/issue22273
    # thanks to https://github.com/GreatFruitOmsk/py-sdl2/commit/e9b13cb5a13b0f5265626d02b0941771e0d1d564
    s = ''
    for g in guid.data:
        s += "{:x}".format(g >> 4) # pylint: disable=consider-using-f-string
        s += "{:x}".format(g & 0x0F) # pylint: disable=consider-using-f-string
    return s

def getJoystickDeviceInfoFromGUID(guid: str) -> tuple[str, str]:
    """
    Returns a tuple containing the vendor and product ID of the
    given GUID.
    """
    vendorId = guid[8:12]
    productId = guid[16:20]
    # swap from big endian to little endian and covert to an int
    vendorId = getLitteEndianFromHex(vendorId)
    productId = getLitteEndianFromHex(productId)
    return (vendorId, productId)

class ControlPad(QObject):
    """
    ControlPad class.
    """

    class Axis:
        """
        This class is used to create ENUM for axis values for associated QML type.
        """
        # axis
        LeftX = sdl2.SDL_CONTROLLER_AXIS_LEFTX
        LeftY = sdl2.SDL_CONTROLLER_AXIS_LEFTY
        RightX = sdl2.SDL_CONTROLLER_AXIS_RIGHTX
        RightY = sdl2.SDL_CONTROLLER_AXIS_RIGHTY
        # trigger buttons
        LeftTriggerAxis = sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT
        RightTriggerAxis = sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT

    class Button:
        """
        This class is used to create ENUM for button values for associated QML type.
        """
        # DPAD buttons
        UpButton = sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP
        DownButton = sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN
        LeftButton = sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT
        RightButton = sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT
        # shoulder buttons
        LeftShoulderButton = sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER
        RightShoulderButton = sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER
        # action buttons
        AButton = sdl2.SDL_CONTROLLER_BUTTON_A
        BButton = sdl2.SDL_CONTROLLER_BUTTON_B
        XButton = sdl2.SDL_CONTROLLER_BUTTON_X
        YButton = sdl2.SDL_CONTROLLER_BUTTON_Y
        # others
        BackButton = sdl2.SDL_CONTROLLER_BUTTON_BACK
        GuideButton = sdl2.SDL_CONTROLLER_BUTTON_GUIDE
        StartButton = sdl2.SDL_CONTROLLER_BUTTON_START

    Q_ENUMS(Axis)
    Q_ENUMS(Button)

    __nameMap = {
        "axis": {
            Axis.LeftTriggerAxis: "Left trigger",
            Axis.LeftX: "Left axis: X direction",
            Axis.LeftY: "Left axis: Y direction",
            Axis.RightTriggerAxis: "Right trigger",
            Axis.RightX: "Right axis: X direction",
            Axis.RightY: "Right axis: Y direction"
        },
        "buttons": {
            Button.AButton: "A Button",
            Button.BackButton: "Back Button",
            Button.BButton: "B Button",
            Button.DownButton: "Down Button",
            Button.GuideButton: "Guide Button",
            Button.LeftButton: "Left Button",
            Button.LeftShoulderButton: "Left Shoulder Button",
            Button.RightButton: "Right Button",
            Button.RightShoulderButton: "Right Shoulder Button",
            Button.UpButton: "Up Button",
            Button.StartButton: "Start Button",
            Button.XButton: "X Button",
            Button.YButton: "Y Button"
        }
    }

    def __init__(self, name: str, guid: str, parent: QObject = None):
        super().__init__(parent)
        self.__name = name
        self.__guid = guid
        self.__present = True

    @staticmethod
    def getAxisName(axis: int) -> str:
        """
        Returns the string name for the given axis value.
        """
        if axis not in ControlPad.__nameMap["axis"]:
            raise ValueError("f{axis} not found")
        return ControlPad.__nameMap["axis"][axis]

    @staticmethod
    def getButtonName(button: int) -> str:
        """
        Returns the string name for the given button value.
        """
        if button not in ControlPad.__nameMap["buttons"]:
            raise ValueError(f"{button} not found")
        return ControlPad.__nameMap["buttons"][button]

    @pyqtProperty(str)
    def guid(self) -> str:
        """
        Returns the GUID of the control pad.
        """
        return self.__guid

    @pyqtProperty(str)
    def name(self) -> str:
        """
        Returns the name of the control pad.
        """
        return self.__name

    @pyqtProperty(bool)
    def present(self) -> bool:
        """
        Returns true if the control pad is present, false otherwise.
        """
        return self.__present

    @present.setter
    def present(self, present: bool):
        """
        Set the present status of the control pad.
        """
        self.__present = present

    def __repr__(self) -> str:
        return f"<ControlPad guid=\"{self.__guid}\" name=\"{self.__name}\">"

class ControlPadListener(QObject):
    """
    Helper class to fire control pad events.
    """

    axisEvent = pyqtSignal(int, int, ControlPad)
    buttonEvent = pyqtSignal(int, ControlPad)
    totalChangedEvent = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def fireAxisEvent(self, axis: int, value: int, controlPad: ControlPad):
        """
        Fires the given axis event
        """
        self.axisEvent.emit(axis, value, controlPad)

    def fireButtonEvent(self, button: int, controlPad: ControlPad):
        """
        Fires the given button event.
        """
        self.buttonEvent.emit(button, controlPad)

    def fireTotalChangedEvent(self, total: int):
        """
        Fires the control pad total changed event.
        """
        self.totalChangedEvent.emit(total)

class ControlPadManager(QObject):
    """
    Manages control pads.
    """

    axisEvent = pyqtSignal(int, int, ControlPad, arguments=['axis', 'value', 'controlPad'])
    buttonEvent = pyqtSignal(int, ControlPad, arguments=['button', 'controlPad'])
    totalChangedEvent = pyqtSignal(int, arguments=['total'])
    __listener = ControlPadListener() # shared instance
    __controlPads = {} # shared dictionary of connected control pads

    def __init__(self, parent=None):
        super().__init__(parent)
        # connect this instance to the shared ControlPadListener instance
        self.__listener.axisEvent.connect(self.__fireAxisEvent)
        self.__listener.buttonEvent.connect(self.__fireButtonEvent)
        self.__listener.totalChangedEvent.connect(self.__fireTotalChangedEvent)

    @staticmethod
    def __beginUpdate():
        """
        This method should be called before polling connected
        control pads.
        """
        for controlPad in ControlPadManager.__controlPads.values():
            controlPad.present = False

    @staticmethod
    def __endUpdate():
        """
        This method should be called after polling connected
        control pads is complete.
        """
        toRemove = [
            controlPad for controlPad in
                ControlPadManager.__controlPads.values() if not controlPad.present
        ]
        if len(toRemove) > 0:
            for controlPad in toRemove:
                logging.info(
                    "ControlPadManager.__endUpdate: %s is no longer connected",
                    controlPad.name
                )
                del ControlPadManager.__controlPads[controlPad.guid]
            ControlPadManager.__listener.fireTotalChangedEvent(len(ControlPadManager.__controlPads))

    @pyqtSlot(int, int, ControlPad)
    def __fireAxisEvent(self, axis: int, value: int, controlPad: ControlPad):
        """
        Fire axis event.
        """
        logging.debug(
            "ControlPadManager.__fireAxisEvent: %s, value: %d",
            ControlPad.getAxisName(axis), value
        )
        self.axisEvent.emit(axis, value, controlPad)

    @pyqtSlot(int, ControlPad)
    def __fireButtonEvent(self, button: int, controlPad: ControlPad):
        """
        Fire button event.
        """
        logging.debug("ControlPadManager.__fireButtonEvent: %s", ControlPad.getButtonName(button))
        self.buttonEvent.emit(button, controlPad)

    @pyqtSlot(int)
    def __fireTotalChangedEvent(self, total: int):
        """
        Fire control pad total changed event.
        """
        logging.debug("ControlPadManager.__fireTotalChangedEvent: %d", total)
        self.totalChangedEvent.emit(total)

    @pyqtSlot(result=list)
    def getControlPads(self) -> list:
        """
        Return a list of all the ControlPad objects that
        are connected.
        """
        return list(ControlPadManager.__controlPads.values())

    @staticmethod
    def processEvent(event):
        """
        Processes the given SDL event.
        """
        if event.type == sdl2.SDL_CONTROLLERBUTTONUP and event.cbutton.state == sdl2.SDL_RELEASED:
            joystickGUID = getJoystickGUIDString(
                sdl2.SDL_JoystickGetDeviceGUID(event.cbutton.which)
            )
            ControlPadManager.__listener.fireButtonEvent(
                event.cbutton.button,
                ControlPadManager.__controlPads[joystickGUID]
            )
        elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
            if event.caxis.value < JOYSTICK_AXIS_MIN or event.caxis.value > JOYSTICK_AXIS_MAX:
                joystickGUID = getJoystickGUIDString(
                    sdl2.SDL_JoystickGetDeviceGUID(event.cbutton.which)
                )
                logging.debug(
                    "ControlPadManager.processEvent: axis \"%s\" activated: %d",
                    sdl2.SDL_GameControllerGetStringForAxis(event.caxis.axis),
                    event.caxis.value
                )
                ControlPadManager.__listener.fireAxisEvent(
                    event.caxis.axis,
                    event.caxis.value,
                    ControlPadManager.__controlPads[joystickGUID]
                )

    @pyqtProperty(int, notify=totalChangedEvent)
    def total(self) -> int:
        """
        Returns the total number of control pads connected.
        """
        return len(ControlPadManager.__controlPads)

    @staticmethod
    def updateControlPads():
        """
        Poll the control pads that are currently connected.
        """
        ControlPadManager.__beginUpdate()
        joystickTotal = sdl2.joystick.SDL_NumJoysticks()

        if joystickTotal > 0:
            for i in range(joystickTotal):
                if sdl2.SDL_IsGameController(i):
                    c = sdl2.SDL_GameControllerOpen(i)
                    if sdl2.SDL_GameControllerGetAttached(c):
                        controlPadName = sdl2.SDL_GameControllerNameForIndex(i).decode()
                        joystickGUID = getJoystickGUIDString(sdl2.SDL_JoystickGetDeviceGUID(i))
                        ControlPadManager.__updateControlPad(joystickGUID, controlPadName)

                    if i > 0:
                        # only allow first controller to control GUI
                        sdl2.SDL_GameControllerClose(c)

        ControlPadManager.__endUpdate()

    @staticmethod
    def __updateControlPad(guid: str, name: str):
        """
        Update the list of control pads.
        """
        if guid in ControlPadManager.__controlPads:
            ControlPadManager.__controlPads[guid].present = True
            return
        logging.debug("ControlPadManager.addControlPad: adding %s (%s)", guid, name)
        ControlPadManager.__controlPads[guid] = ControlPad(name, guid)
        ControlPadManager.__listener.fireTotalChangedEvent(len(ControlPadManager.__controlPads))
