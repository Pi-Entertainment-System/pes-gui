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
import QtQuick.Window 2.2
import QtQuick.Controls 2.5
import QtMultimedia 5.12
import "../Style/" 1.0
import "../pes.js" as PES

Rectangle {
    color: focus ? Colour.buttonFocus : Colour.menuBg
    width: 400
    height: 50

    // additional properties
    property var values: []
    
    // private properties
    QtObject {
        id: internal
        property int index: 0
        property int prevIndex: 0
    }

    function getIndex() {
        return internal.index;
    }

    function getValue() {
        return values[internal.index];
    }

    function setIndex(i) {
        if (i > 0 && i < values.length) {
            internal.index = i;
        }
        else {
            console.error("ComboScroll: invalid index: " + i);
        }
    }

    function setValue(v) {
        for (var i = 0; i < values.length; i++ ){
            if (values[i] == v) {
                internal.index = i;
                internal.prevIndex = i;
                return;
            }
        }
    }

    function setValues(v) {
        internal.index = 0;
        internal.prevIndex = 0;
        values = v;
    }

    Keys.onPressed: {
        if (event.key == Qt.Key_Up || event.key == Qt.Key_Down || event.key == Qt.Key_Left || event.key == Qt.Key_Right) {
            if (arrowIcon.visible) {
                event.accepted = true;
                if (event.key == Qt.Key_Up) {
                    if (internal.index - 1  >= 0) {
                        internal.index--;
                    }
                }
                else if (event.key == Qt.Key_Down) {
                    if (internal.index + 1 < values.length) {
                        internal.index++;
                    }
                }
            }
            else {
                event.accepted = false;
            }
        }
        else if (event.key == Qt.Key_Return) {
            if (!arrowIcon.visible) {
                internal.prevIndex = internal.index;
            }
            arrowIcon.visible = !arrowIcon.visible;
            event.accepted = true;
        }
        else if (event.key == Qt.Key_Backspace) {
            if (arrowIcon.visible) {
                arrowIcon.visible = false;
                internal.index = internal.prevIndex;
                event.accepted = true;
            }
        }
    }

    RowLayout {
        anchors.fill: parent

        Text {
            id: valueText
            color: Colour.text
            elide: Text.ElideRight
            font.pixelSize: FontStyle.menuSize
            font.family: FontStyle.font
            text: values[internal.index]
            wrapMode: Text.NoWrap
            Layout.leftMargin: 10
            Layout.preferredWidth: parent.width - arrowIcon.width - 20
        }

        Item {
            id: spacerItem
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        Image {
            id: arrowIcon
            height: 32
            width: 32
            source: "../icons/vertical-flip.png"
            visible: false
            Layout.rightMargin: 10
        }
    }
}