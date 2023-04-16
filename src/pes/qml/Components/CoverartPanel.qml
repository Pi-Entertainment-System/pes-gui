/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2020-2023 Neil Munday (neil@mundayweb.com)

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
import QtMultimedia 5.12
import "../Style/" 1.0

Rectangle {
    id: mainRect
    property Item keyDown: null
    property Item keyLeft: null
    property Item keyRight: null
    property Item keyUp: null

    property alias headerText: headerText.text
    property alias navSound: listView.navSound

    // custom signals
    signal addFavourite(int gameId)
    signal removeFavourite(int gameId)
    signal gameSelected(int gameId)

    onFocusChanged: {
        scrollView.forceActiveFocus();
        listView.currentIndex = 0;
    }

    function addGame(game) {
        myModel.append(game);
    }

    function gainFocus() {
        if (listView.currentIndex == -1) {
            listView.currentIndex = 0;
        }
        scrollView.forceActiveFocus();
    }

    function isGameSelected() {
        return listView.currentIndex != -1;
    }

    function loseFocus() {
        if (listView.currentItem) {
            listView.currentItem.focus = false;
        }
        listView.currentIndex = -1;
    }

    function removeAll() {
        myModel.clear();
    }

    ListModel {
        id: myModel
    }

    Component {
        id: listDelegate

        Rectangle {
            border.color: Colour.line
            border.width: focus ? 2: 0
            color: focus ? Colour.menuFocus : mainRect.color
            height: 225
            width: 220

            Keys.onPressed: {
                if (event.key == Qt.Key_Return) {
                    mainRect.gameSelected(id);    
                }
                else if (event.key == Qt.Key_S) {
                    if (favourite) {
                        favourite = false;
                        mainRect.removeFavourite(id);
                    }
                    else {
                        favourite = true;
                        mainRect.addFavourite(id);
                    }
                }
            }

            Image {
                id: img
                x: 10
                y: 10
                height: 180
                width: 200
                source: 'file://' + coverartFront
            }

            Text {
                x: 10
                y: img.y + img.height
                color: favourite ? Colour.favouriteText : Colour.text
                elide: Text.ElideRight
                font.pixelSize: FontStyle.bodySmallSize
                font.bold: true
                font.family: FontStyle.font
                maximumLineCount: 1
                text: name
                wrapMode: Text.Wrap
                width: parent.width - (x * 2)
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent

        BodyText {
            id: headerText
            text: ""

            Layout.minimumHeight: 50
        }

        ScrollView {
            id: scrollView
            clip: true
            Layout.fillHeight: true
            Layout.fillWidth: true

            ListView {
                id: listView
                property QtObject navSound: null;
                Keys.onDownPressed: {
                    if (mainRect.keyDown && mainRect.keyDown.visible) {
                        mainRect.keyDown.forceActiveFocus();
                        mainRect.loseFocus();
                    }
                }
                Keys.onLeftPressed: {
                    if (currentIndex > 0) {
                        if (navSound) {
                            navSound.play();
                        }
                        currentIndex -= 1;
                    }
                    else {
                        if (mainRect.keyLeft && mainRect.keyLeft.visible) {
                            mainRect.keyLeft.forceActiveFocus();
                            mainRect.loseFocus();
                        }
                    }
                }
                Keys.onRightPressed: {
                    if (currentIndex < count - 1 ) {
                        if (navSound) {
                            navSound.play();
                        }
                        currentIndex += 1;
                    }
                    else {
                        if (mainRect.keyRight && mainRect.keyRight.visible) {
                            mainRect.keyRight.forceActiveFocus();
                            mainRect.loseFocus();
                        }
                    }
                }
                Keys.onUpPressed: {
                    if (mainRect.keyUp && mainRect.keyUp.visible) {
                        mainRect.keyUp.forceActiveFocus();
                        mainRect.loseFocus();
                    }
                }
                Layout.fillHeight: true
                Layout.fillWidth: true
                currentIndex: -1 // set no item as selected
                delegate: listDelegate
                focus: true
                keyNavigationEnabled: true
                keyNavigationWraps: false
                model: myModel
                orientation: Qt.Horizontal
                spacing: 20

                onActiveFocusChanged: {
                    if (activeFocus && navSound) {
                        navSound.play();
                    }
                }
            }
        }
    }
}