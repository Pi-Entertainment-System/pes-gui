/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2021 Neil Munday (neil@mundayweb.com)

    PES is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PES is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PES.  If not, see <http://www.gnu.org/licenses/>.
*/

pragma Singleton
import QtQuick 2.7

QtObject {
  readonly property color panelBg: "#4b5656"
  readonly property color bg: "#1f2326"
  readonly property color menuBg: "#1f2326"
  readonly property color text: "#f0f0f0"
  readonly property color line: "#f08819"
  readonly property color progressBar: "#f08819"
  readonly property color progressBarBg: "#1f2326"
  readonly property color menuFocus: "#2e3235"
  readonly property color buttonFocus: "#f08819"
  readonly property color favouriteText: "#f08819"
  readonly property color menuText: "#999999"
  readonly property color dialogBg: "#323232"
}
