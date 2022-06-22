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

# pylint: disable=broad-except,invalid-name,line-too-long,missing-class-docstring,missing-function-docstring,redefined-outer-name,too-many-locals

"""
A simple program that can be used to test the functionality
of PES' dbus module.
"""

import logging
import signal
import sys

from dbus.mainloop.pyqt5 import DBusQtMainLoop
from PyQt5.QtCore import QCoreApplication, QTimer

import pes.system

def handleSignal(sig, frame): # pylint: disable=no-value-for-parameter,unused-argument
    global app # pylint: disable=global-variable-not-assigned
    if sig == signal.SIGINT:
        print("Exiting...")
        app.quit()

if __name__ == "__main__":

    logLevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

    DBusQtMainLoop(set_as_default=True)

    app = QCoreApplication(sys.argv)
    broker = pes.system.DbusBroker()

    signal.signal(signal.SIGINT, handleSignal)
    timer = QTimer()
    timer.start()
    timer.timeout.connect(lambda: None)

    logging.info("Timezone: %s", broker.timezone)
    logging.info("Available timezones:")
    for t in broker.getTimezones():
        logging.info("TZ = %s", t)

    if broker.btAvailable():
        agent = pes.system.BluetoothAgent()
        #logging.info("Adapter: %s", broker.btAdapter)
        logging.info("Powered: %s", broker.btPowered)
        logging.info("Discoverable: %s", broker.btDiscoverable)
        logging.info("Discoverable timeout: %d", broker.btDiscoverableTimeout)
        logging.info("Pairable: %s", broker.btPairable)
        broker.btPowered = True
        broker.btDiscoverableTimeout = 0
        broker.btDiscoverable = True
        broker.btPairable = True
        broker.btStartDiscovery()
    else:
        logging.info("No Bluetooth adapter found")
        sys.exit()

    app.exec()
