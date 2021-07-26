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
    property int consoleId: 0
    property alias background: backgroundImg.source
    property alias headerText: headerText.text
    property alias menuIndex: menuView.currentIndex

    function addGame(game) {
        gameModel.append(game);
    }

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    function refresh() {
        gameModel.clear();
        if (menuModel.get(menuView.currentIndex).name == "Browse") {
            var games = PES.getGames(consoleId);
            for (var i = 0; i < games.length; i++) {
                addGame(games[i]);
            }
        }
    }

    Keys.onPressed: {
        if (event.key == Qt.Key_Backspace) {
            PES.goHome();
        }
    }

    ListModel {
        id: gameModel
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

    Component {
        id: gridDelegate

        Rectangle {
            border.color: Colour.line
            border.width: focus ? 2: 0
            color: focus ? Colour.menuFocus : "transparent"
            height: 225
            width: 220

            Keys.onReturnPressed: {
                
            }

            Image {
                id: img
                x: 10
                y: 10
                height: 180
                width: 200
                source: 'file://' + coverart
            }

            Text {
                x: 10
                y: img.y + img.height
                color: Colour.text
                elide: Text.ElideRight
                font.pixelSize: FontStyle.bodySmallSize
                font.bold: true
                font.family: FontStyle.font
                maximumLineCount: 1
                text: name
                wrapMode: Text.Wrap
                width: parent.width
            }
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
                        Keys.onReturnPressed: {
                            gridView.forceActiveFocus();
                        }
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

            ScrollView {
                clip: true
                Layout.fillWidth: true
                Layout.preferredHeight: screenDisplayRect.height - headerText.height

                GridView {
                    id: gridView
                    cellWidth: 250
                    cellHeight: 250
                    model: gameModel
                    delegate: gridDelegate
                }
            }
        }
    }
}    		
