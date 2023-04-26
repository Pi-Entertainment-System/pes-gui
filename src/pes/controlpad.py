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

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Q_ENUMS, QObject

class ControlPad(QObject):
    """
    ControlPad class.
    """

    class Axis:
        """
        This class is used to create ENUM for axis values for associated QML type.
        """
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

    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def getButtonName(button: int) -> str:
        """
        Returns the string name for the given button value.
        """
        if button not in ControlPad.__nameMap["buttons"]:
            raise ValueError(f"{button} not found")
        return ControlPad.__nameMap["buttons"][button]

class ControlPadListener(QObject):
    """
    Helper class to fire control pad events.
    """

    buttonEventSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def fireButtonEvent(self, button: int):
        """
        Fires the given button event.
        """
        self.buttonEventSignal.emit(button)

class ControlPadManager(QObject):
    """
    Manages control pads.
    """

    buttonEventSignal = pyqtSignal(int, arguments=['button'])
    listener = ControlPadListener()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener.buttonEventSignal.connect(self.__fireButtonEvent)

    @pyqtSlot(int)
    def __fireButtonEvent(self, button: int):
        logging.debug("ControlPadManager.__fireButtonEvent: %s", ControlPad.getButtonName(button))
        self.buttonEventSignal.emit(button)
