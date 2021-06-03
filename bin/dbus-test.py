#!/usr/bin/env python

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

"""
A simple program that can be used to test the functionality
of PES' dbus module.
"""

import logging
import os
import signal
import sys
import pes.system
from dbus.mainloop.pyqt5 import DBusQtMainLoop
from PyQt5.QtCore import Qt, QCoreApplication, QTimer

def handleSignal(sig, frame):
    global app
    if sig == signal.SIGINT:
        print("Exiting...")
        app.quit()

if __name__ == "__main__":

    logLevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

    DBusQtMainLoop(set_as_default=True)

    app = QCoreApplication(sys.argv)
    broker = pes.system.DbusBroker()
    agent = pes.system.BluetoothAgent()

    signal.signal(signal.SIGINT, handleSignal)
    timer = QTimer()
    timer.start()
    timer.timeout.connect(lambda: None)

    logging.info("Powered: %s" % broker.btPowered)
    logging.info("Discoverable: %s" % broker.btDiscoverable)
    logging.info("Pairable: %s" % broker.btPairable)
    broker.btPowered = True
    broker.btDiscoverable = True
    broker.btPairable = True
    broker.btStartDiscovery()

    app.exec()
