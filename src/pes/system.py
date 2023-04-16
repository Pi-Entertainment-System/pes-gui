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

# pylint: disable=broad-exception-raised,invalid-name,line-too-long,missing-class-docstring,missing-function-docstring,too-few-public-methods

"""
This module provides system level classes that make use of dbus
to adjust Bluetooth and date/time settings.
"""

# standard imports
import logging

# third-party imports
from dbus.mainloop.pyqt5 import DBusQtMainLoop # pylint: disable=import-error
from PyQt5.QtCore import Q_CLASSINFO, QObject, QVariant, pyqtProperty, pyqtSlot, QMetaType
from PyQt5.QtDBus import QDBusArgument, QDBusConnection, QDBusAbstractAdaptor, QDBusInterface, QDBusVariant, QDBusMessage, QDBusObjectPath, QDBusError

BT_SERVICE = "org.bluez"
BT_ADAPTER_INTERFACE = BT_SERVICE  + ".Adapter1"
BT_AGENT_INTERFACE = BT_SERVICE + ".Agent1"
BT_DEVICE_INTERFACE = BT_SERVICE + ".Device1"

TIMEDATE_SERVICE = "org.freedesktop.timedate1"
TIMEDATE_PATH = "/org/freedesktop/timedate1"
TIMEDATE_INTERFACE = "org.freedesktop.timedate1"

DBUS_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

PS3_CONTROLLER = "Sony PLAYSTATION(R)3 Controller"
WII_CONTROLLER = "Nintendo RVL-CNT-01"
WIRELESS_CONTROLLER = "Wireless Controller"
CONTROLLERS = [WII_CONTROLLER, PS3_CONTROLLER, WIRELESS_CONTROLLER]

class BluetoothAdapter(QDBusAbstractAdaptor):

    _PINS = ["0000", "1234"] # PINS to try

    Q_CLASSINFO("D-Bus Interface", "org.bluez.Agent1")
    Q_CLASSINFO("D-Bus Introspection", """                                                                         <interface name=\"org.bluez.Agent1\">
        <method name=\"AuthorizeService\">
            <arg direction=\"in\" type=\"o\"/>
            <arg direction=\"in\" type=\"s\"/>"
        </method>
    </interface>""")

    # request PIN signature
    # <method name=\"RequestPinCode\">
    #    <arg direction=\"in\" type=\"o\"/>
    #    <arg direction=\"out\" type=\"s\"/>"
    #</method>

    def __init__(self, parent=None):
        super().__init__(parent)
        #self._devicePINTries = {}
        DBusQtMainLoop(set_as_default=True)
        self._bus = QDBusConnection.systemBus()
        self.setAutoRelaySignals(True)

    @pyqtSlot(QDBusMessage)
    def AuthorizeService(self, message):
        # only automatically accept PS3 control pads
        device, service = message.arguments()
        connection = QDBusInterface(BT_SERVICE, device, DBUS_PROPERTIES_INTERFACE, self._bus)
        alias = connection.call("Get", BT_DEVICE_INTERFACE, "Alias").arguments()[0]
        #address = connection.call("Get", BT_DEVICE_INTERFACE, "Address").arguments()[0]
        if alias in CONTROLLERS:
            # authorized
            logging.info("BluetoothAdapter.AuthorizeService: authorized %s %s", alias, device)
            return
        # deny unknown devices
        logging.warning("BluetoothAdapter.AuthorizeService: denied for %s (%s), service %s", device, alias, service)
        error = message.createErrorReply(QDBusError.AccessDenied, "Failed")
        self._bus.send(error)

    #@pyqtSlot(QDBusMessage, result=str)
    #def RequestPinCode(self, message):
    #    device = message.arguments()[0]
    #    logging.debug("BluetoothAdapter.RequestPinCode: device = %s" % device)
    #    if device in self._devicePINTries:
    #        if self._devicePINTries[device] == len(self._PINS):
    #            logging.debug("BluetoothAdapter.RequestPinCode: PIN tries exhausted for %s" % device)
    #            error = message.createErrorReply(QDBusError.AccessDenied, "Failed")
    #            self._bus.send(error)
    #            return None
    #    else:
    #        self._devicePINTries[device] = 0
    #    pin = self._PINS[self._devicePINTries[device]]
    #    self._devicePINTries[device] += 1
    #    logging.debug("BluetoothAdapter.RequestPinCode: trying PIN %s" % pin)
    #    message.createReply(pin)
    #    return pin

class BluetoothAgent(QObject):

    PATH = "/com/mundayweb/pes/agent"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bus = QDBusConnection.systemBus()
        self._apdater = BluetoothAdapter(self)
        agentManager = QDBusInterface(BT_SERVICE, "/org/bluez", "org.bluez.AgentManager1", self._bus, self)
        if not self._bus.registerObject(BluetoothAgent.PATH, self):
            raise Exception("BluetoothAgent.__init__: failed to register object")
        logging.debug("BluetoothAgent.__init__: registered object")
        msg = agentManager.call("RegisterAgent", QDBusObjectPath(BluetoothAgent.PATH), "DisplayYesNo")
        if msg.type() == QDBusMessage.ErrorMessage:
            logging.warning("DbusBroker.__init__: Failed to register Bluetooth agent: %s", msg.errorMessage())
        else:
            result = agentManager.call("RequestDefaultAgent", QDBusObjectPath(BluetoothAgent.PATH)).arguments()
            if result[0] is not None:
                raise Exception(f"BluetoothAgent.__init__: failed to register default agent: {result[0]}")

class DbusBroker(QObject):
    """
    A helper class to manage system devices and properties
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bus = QDBusConnection.systemBus()
        self._adapterPath = None
        self.__timezones = None
        # look for Bluez service
        bluezFound = False
        for service in self._bus.interface().registeredServiceNames().value():
            if service == BT_SERVICE:
                bluezFound = True
                break

        if bluezFound:
            self._adapterPath = self._getBtAdapter()
            if self._adapterPath is None:
                logging.warning("DbusBroker.__init__: could not find BT adapter")
            else:
                logging.debug("DbusBroker.__init__: found BT adapter %s", self._adapterPath)
                # listen for devices being added
                if not self._bus.connect("", "", "org.freedesktop.DBus.ObjectManager", "InterfacesAdded", self.btDeviceAdded):
                    raise Exception("DbusBroker.__init__: failed to connect to org.freedesktop.DBus.ObjectManager:InterfacesAdded")
                # listen for all Bluez related property changes
                if not self._bus.connect(BT_SERVICE, "", DBUS_PROPERTIES_INTERFACE, "PropertiesChanged", self.btPropertyChange):
                    raise Exception(f"DbusBroker.__init__: failed to connected to org.freedesktop.DBus.Properties:PropertiesChanged for {BT_SERVICE}")
        else:
            logging.warning("DbusBroker.__init__: could not find %s", BT_SERVICE)

    def _getBtAdapter(self):
        adapterPath = None
        connection = QDBusInterface(BT_SERVICE, "/", "org.freedesktop.DBus.ObjectManager", self._bus)
        msg = connection.call("GetManagedObjects")
        if msg.type() == QDBusMessage.ErrorMessage:
            logging.warning("DbusBroker._getBtAdapter: %s", msg.errorMessage())
        else:
            for path, value in msg.arguments()[0].items():
                if BT_ADAPTER_INTERFACE in value:
                    adapterPath = path
                    break
        return adapterPath

    def _getBtAdapterProperty(self, prop):
        if self._adapterPath:
            connection = QDBusInterface(BT_SERVICE, self._adapterPath, DBUS_PROPERTIES_INTERFACE, self._bus)
            return connection.call("Get", BT_ADAPTER_INTERFACE, prop).arguments()[0]
        raise Exception("DbusBroker._getBtAdapterProperty: Bluetooth adapter not found")

    def _setBtAdapterProperty(self, prop, value):
        if self._adapterPath:
            connection = QDBusInterface(BT_SERVICE, self._adapterPath, DBUS_PROPERTIES_INTERFACE, self._bus)
            if isinstance(value, int):
                # convert integer properties to UInt32
                rslt = connection.call("Set", BT_ADAPTER_INTERFACE, prop, QDBusVariant(QDBusArgument(value, QMetaType.UInt))).arguments()
            else:
                rslt = connection.call("Set", BT_ADAPTER_INTERFACE, prop, QDBusVariant(value)).arguments()
            if rslt[0] is not None:
                raise Exception(f"DbusBroker._setBtAdapterProperty: {rslt[0]}")
            return
        raise Exception(f"DbusBroker._setBtAdapterProperty: Bluetooth adapter not found when seting '{prop}'")

    def _getTimedateConnection(self, interface=TIMEDATE_INTERFACE):
        return QDBusInterface(TIMEDATE_SERVICE, TIMEDATE_PATH, interface, self._bus)

    def _getTimedateProperty(self, prop):
        return self._getTimedateConnection(DBUS_PROPERTIES_INTERFACE).call("Get", TIMEDATE_INTERFACE, prop).arguments()[0]

    @pyqtSlot(result=bool)
    def btAvailable(self):
        logging.debug("DbusBroker.btAvailale: %s", (self._adapterPath is not None))
        return self._adapterPath is not None

    @pyqtSlot(QDBusMessage)
    def btDeviceAdded(self, message):
        args = message.arguments()
        if "org.bluez.Device1" in args[1]:
            device = args[0]
            logging.debug("DbusBroker.btDeviceAdded: detected device %s", device)
            connection = QDBusInterface(BT_SERVICE, device, DBUS_PROPERTIES_INTERFACE, self._bus)
            alias = connection.call("Get", BT_DEVICE_INTERFACE, "Alias").arguments()[0]
            address = connection.call("Get", BT_DEVICE_INTERFACE, "Address").arguments()[0]
            logging.debug("DbusBroker.btDeviceAdded: alias = %s, address = %s ", alias, address)
            if alias in CONTROLLERS:
                if connection.call("Get", BT_DEVICE_INTERFACE, "Trusted").arguments()[0]:
                    logging.debug("DbusBroker.btDeviceAdded: already truested")
                else:
                    logging.debug("DbusBroker.btDeviceAdded: trusting device")
                    connection.call("Set", BT_DEVICE_INTERFACE, "Trusted", QDBusVariant(True)).arguments()
                if alias == WIRELESS_CONTROLLER:
                    # PS4 / PS5 and possibly others...
                    logging.debug("DbusBroker.btDeviceAdded: wireless controller detected, initiating pairing")
                    connection = QDBusInterface(BT_SERVICE, device, BT_DEVICE_INTERFACE, self._bus, self)
                    connection.call("Pair").arguments()
                elif alias == WII_CONTROLLER:
                    logging.debug("DbusBroker.btDeviceAdded: connecting to Wiimote")
                    connection = QDBusInterface(BT_SERVICE, device, BT_DEVICE_INTERFACE, self._bus, self)
                    connection.call("Connect").arguments()

    @pyqtSlot(QDBusMessage)
    def btPropertyChange(self, message):
        path = message.path()
        args = message.arguments()
        logging.debug("DbusBroker.btPropertyChange: property change: %s -> %s", path, args)

    @pyqtProperty(bool)
    def btDiscoverable(self) -> bool:
        logging.debug("DbusBroker.btDiscoverable: getting property")
        return self._getBtAdapterProperty("Discoverable")

    @btDiscoverable.setter
    def btDiscoverable(self, discoverable: bool):
        logging.debug("DbusBroker.btDiscoverable: setting to %s", discoverable)
        self._setBtAdapterProperty("Discoverable", discoverable)

    @pyqtProperty(int)
    def btDiscoverableTimeout(self) -> int:
        logging.debug("DbusBroker.btDiscoverable: getting property")
        return self._getBtAdapterProperty("DiscoverableTimeout")

    @btDiscoverableTimeout.setter
    def btDiscoverableTimeout(self, timeout: int):
        logging.debug("DbusBroker.btDiscoverableTimeout: setting to %d", timeout)
        self._setBtAdapterProperty("DiscoverableTimeout", timeout)

    @pyqtProperty(bool)
    def btPairable(self) -> bool:
        logging.debug("DbusBroker.btPairable: getting property")
        return self._getBtAdapterProperty("Pairable")

    @btPairable.setter
    def btPairable(self, pairable: bool):
        logging.debug("DbusBroker.btPairable: setting to %s", pairable)
        self._setBtAdapterProperty("Pairable", pairable)

    @pyqtProperty(bool)
    def btPowered(self) -> bool:
        logging.debug("DbusBroker.btPowered: getting property")
        return self._getBtAdapterProperty("Powered")

    @btPowered.setter
    def btPowered(self, powered: bool):
        logging.debug("DbusBroker.btPowered: setting to %s", powered)
        return self._setBtAdapterProperty("Powered", powered)

    @pyqtSlot()
    def btStartDiscovery(self):
        logging.debug("DbusBroker.btStartDiscovery: starting")
        connection = QDBusInterface(BT_SERVICE, self._adapterPath, BT_ADAPTER_INTERFACE, self._bus, self)
        connection.call("StartDiscovery").arguments()

    @pyqtSlot(result=QVariant)
    def getBtGamingDevices(self):
        devices = {}
        connection = QDBusInterface(BT_SERVICE, "/", "org.freedesktop.DBus.ObjectManager", self._bus)
        for _, value in connection.call("GetManagedObjects").arguments()[0].items():
            if BT_DEVICE_INTERFACE in value:
                if value[BT_DEVICE_INTERFACE]["Alias"] in CONTROLLERS:
                    devices[value[BT_DEVICE_INTERFACE]["Address"]] = value[BT_DEVICE_INTERFACE]["Alias"]
        return devices

    @pyqtSlot(result=QVariant)
    def getTimezones(self):
        """
        Get all available timezones as a list.
        """
        logging.debug("DbusBroker.getTimezones: getting timezones")
        if self.__timezones is None:
            self.__timezones = self._getTimedateConnection().call("ListTimezones").arguments()[0]
        return self.__timezones

    @pyqtProperty(str)
    def timezone(self) -> str:
        """
        Get the current timezone.
        """
        logging.debug("DbusBroker.timezone: getting current time zone")
        return self._getTimedateProperty("Timezone")

    @timezone.setter
    def timezone(self, tz: str):
        """
        Sets the current timezone.
        Note: requires root privileges!
        """
        logging.debug("DbusBroker.timezone: setting to %s", tz)
        if tz not in self.getTimezones():
            raise ValueError(f"{tz} is not a valid timezone")
        rslt = self._getTimedateConnection().call("SetTimezone", tz, False).arguments()
        if rslt[0] is not None:
            raise Exception(f"DbusBroker.timezone: {rslt[0]}")
        