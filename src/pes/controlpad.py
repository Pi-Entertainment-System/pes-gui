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

class ControlPadListener(QObject):
    """
    Helper class to fire control pad events.
    """

    axisEvent = pyqtSignal(int, int)
    buttonEvent = pyqtSignal(int)
    totalChangedEvent = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def fireAxisEvent(self, axis: int, value: int):
        """
        Fires the given axis event
        """
        self.axisEvent.emit(axis, value)

    def fireButtonEvent(self, button: int):
        """
        Fires the given button event.
        """
        self.buttonEvent.emit(button)

    def fireTotalChangedEvent(self, total: int):
        """
        Fires the control pad total changed event.
        """
        self.totalChangedEvent.emit(total)

class ControlPadManager(QObject):
    """
    Manages control pads.
    """

    axisEvent = pyqtSignal(int, int, arguments=['axis', 'value'])
    buttonEvent = pyqtSignal(int, arguments=['button'])
    totalChangedEvent = pyqtSignal(int, arguments=['total'])
    __listener = ControlPadListener() # shared instance
    __controlPads = {} # shared dictionary of connected control pads

    def __init__(self, parent=None):
        super().__init__(parent)
        # connect this instance to the shared ControlPadListener instance
        self.__listener.axisEvent.connect(self.__fireAxisEvent)
        self.__listener.buttonEvent.connect(self.__fireButtonEvent)
        self.__listener.totalChangedEvent.connect(self.__fireTotalChangedEvent)

    @pyqtSlot(int, int)
    def __fireAxisEvent(self, axis: int, value: int):
        """
        Fire axis event.
        """
        logging.debug(
            "ControlPadManager.__fireAxisEvent: %s, value: %d",
            ControlPad.getAxisName(axis), value
        )
        self.axisEvent.emit(axis, value)

    @pyqtSlot(int)
    def __fireButtonEvent(self, button: int):
        """
        Fire button event.
        """
        logging.debug("ControlPadManager.__fireButtonEvent: %s", ControlPad.getButtonName(button))
        self.buttonEvent.emit(button)

    @pyqtSlot(int)
    def __fireTotalChangedEvent(self, total: int):
        """
        Fire control pad total changed event.
        """
        logging.debug("ControlPadManager.__fireTotalChangedEvent: %d", total)
        self.totalChangedEvent.emit(total)

    @staticmethod
    def beginUpdate():
        """
        This method should be called before polling connected
        control pads.
        """
        for controlPad in ControlPadManager.__controlPads.values():
            controlPad.present = False

    @staticmethod
    def endUpdate():
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
                    "ControlPadManager.endUpdate: %s is no longer connected",
                    controlPad.name
                )
                del ControlPadManager.__controlPads[controlPad.guid]
            ControlPadManager.__listener.fireTotalChangedEvent(len(ControlPadManager.__controlPads))

    @staticmethod
    def fireAxisEvent(axis: int, value: int):
        """
        Fire axis event.
        """
        ControlPadManager.__listener.fireAxisEvent(axis, value)

    @staticmethod
    def fireButtonEvent(button: int):
        """
        Fire button event.
        """
        ControlPadManager.__listener.fireButtonEvent(button)

    @pyqtSlot(result=list)
    def getControlPads(self) -> list:
        """
        Return a list of all the ControlPad objects that
        are connected.
        """
        return list(ControlPadManager.__controlPads.values())

    @pyqtProperty(int, notify=totalChangedEvent)
    def total(self) -> int:
        """
        Returns the total number of control pads connected.
        """
        return len(ControlPadManager.__controlPads)

    @staticmethod
    def updateControlPad(guid: str, name: str):
        """
        Update the list of control pads.
        """
        if guid in ControlPadManager.__controlPads:
            ControlPadManager.__controlPads[guid].present = True
            return
        logging.debug("ControlPadManager.addControlPad: adding %s (%s)", guid, name)
        ControlPadManager.__controlPads[guid] = ControlPad(name, guid)
        ControlPadManager.__listener.fireTotalChangedEvent(len(ControlPadManager.__controlPads))
