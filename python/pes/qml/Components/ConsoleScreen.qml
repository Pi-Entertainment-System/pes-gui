/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2020-2021 Neil Munday (neil@mundayweb.com)

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

RowLayout {
    property alias background: backgroundImg.source
    property alias headerText: headerText.text
    property alias menuIndex: menuView.currentIndex

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    Keys.onPressed: {
        if (event.key == Qt.Key_Backspace) {
            PES.goHome();
        }
    }

    ListModel {
        id: menuModel

        ListElement {
            name: "Browse"
        }

        ListElement {
            name: "Favourites"
        }

        ListElement {
            name: "Recently Played"
        }

        ListElement {
            name: "Recently Added"
        }

        ListElement {
            name: "Most Played"
        }
    }

    Rectangle {
        id: menuRect
        Layout.preferredWidth: 300
        Layout.minimumWidth: 300
        Layout.maximumWidth: 300
        Layout.topMargin: 30
        Layout.bottomMargin: 30
        Layout.fillHeight: true
        Layout.fillWidth: false

        color: Colour.menuBg

        Rectangle {
            x: 0
            y: parent.y
            width: parent.width
            height: parent.height - this.y
            color: parent.color

            ScrollView {
                id: menuScrollView
                width: parent.width
                height: parent.height
                clip: true
                //focus: true

                SoundListView {
                    id: menuView
                    anchors.fill: parent
                    focus: false
                    model: menuModel
                    //navSound: navSound
                    soundOn: false
                    delegate: MenuDelegate {
                        //Keys.onReturnPressed: PES.mainMenuEvent(mainMenuModel.get(mainMenuView.currentIndex));
                        //Keys.onRightPressed: PES.setCoverartPanelFocus()
                    }
                }
            }
        }
    }

    Rectangle {
        id: screenDisplayRect
        color: Colour.panelBg

        width: 500
        height: 500
        Layout.fillWidth: true
        Layout.fillHeight: true

        Image {
            id: backgroundImg
            x: 0
            y: 0
            anchors.fill: parent
            opacity: 0.2
            source: ""
            visible: source != ""
        }

        ColumnLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            spacing: 10

            HeaderText {
            id: headerText
            text: "Console"

            Layout.fillWidth: true
            }
        }
    }
}    		
