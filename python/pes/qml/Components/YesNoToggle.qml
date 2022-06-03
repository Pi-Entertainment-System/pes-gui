/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2020-2022 Neil Munday (neil@mundayweb.com)

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

import QtQuick 2.7
import QtQuick.Layouts 1.12
import QtQuick.Controls 2.5
import "../Style/" 1.0

Rectangle {
    color: focus ? Colour.buttonFocus : Colour.menuBg
    width: 100
    height: 50

    // private properties
    QtObject {
        id: internal
        property bool toggled: true
        property bool resetValue: true
    }

    function getValue() {
        return internal.toggled;
    }

    function isDirty() {
        return (internal.toggled != internal.resetValue);
    }

    function reset() {
        internal.toggled =  internal.resetValue;
    }

    function save() {
        internal.resetValue = internal.toggled;
    }

    function setValue(toggled) {
        internal.toggled = toggled;
        internal.resetValue = toggled;
    }

    Keys.onReturnPressed: {
        internal.toggled = !internal.toggled;
    }

    Text {
        anchors.centerIn: parent
        text: internal.toggled ? "Yes" : "No"
        color: Colour.text
        font.pixelSize: FontStyle.menuSize
        font.family: FontStyle.font
    }
        
}