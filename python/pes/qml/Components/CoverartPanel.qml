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

import QtQuick 2.7
import QtQuick.Layouts 1.12
import QtQuick.Controls 2.5
import "../Style/" 1.0

Rectangle {
    id: mainRect
    property alias headerText: headerText.text
    color: 'white'
    KeyNavigation.left: null
    KeyNavigation.right: null

    onFocusChanged: {
        scrollView.forceActiveFocus();
        listView.currentIndex = 0;
    }

    function addGame(game) {
        myModel.append(game);
    }

    function itemSelected(id) {

    }

    function removeAll() {
        if (myModel.count > 0) {
            for (var i = myModel.count - 1; i > 1; i--) {
                myModel.remove(i);
            }
        }
    }

    ListModel {
        id: myModel
    }

    Component {
        id: listDelegate

        Rectangle {
            border.color: Colour.line
            border.width: focus ? 2: 0
            color: focus ? Colour.menuFocus : Colour.panelBg
            height: 225
            width: 220

            Keys.onReturnPressed: {
                mainRect.itemSelected(id);
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
                Keys.onLeftPressed: {
                    if (listView.currentIndex > 0) {
                        listView.currentIndex -= 1;
                    }
                    else {
                        if (mainRect.KeyNavigation.left) {
                            mainRect.KeyNavigation.left.forceActiveFocus();
                            listView.currentItem.focus = false;
                            listView.currentIndex = -1;
                        }
                    }
                }
                Keys.onRightPressed: {
                    if (listView.currentIndex < listView.count - 1 ) {
                        listView.currentIndex += 1;
                    }
                    else {
                        if (mainRect.KeyNavigation.right) {
                            mainRect.KeyNavigation.right.forceActiveFocus();
                            listView.currentItem.focus = false;
                            listView.currentIndex = -1;
                        }
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
            }
        }
    }
}