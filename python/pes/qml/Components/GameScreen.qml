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

Rectangle {

    id: mainRect
    color: "transparent"

    property var game: null

    signal backPressed()
    signal play(int gameId)

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    onGameChanged: function() {
        if (game) {
            backgroundImg.source = PES.getConsoleArt(game.consoleId);
            headerText.text = game.name;
            coverartFrontImg.source = "file://" + game.coverartFront;
            if (game.coverartBack && game.coverartBack != "") {
                coverartBackImg.source = "file://" + game.coverartBack;
            }
            else {
                coverartBackImg.source = "";
            }
            if (game.screenshots.length > 0) {
                screenshotImg.source = "file://" + game.screenshots[0];
            }
            else {
                screenshotImg.source = "";
            }
            filenameText.text = "Filename: " + game.filename + " (" + PES.humanFileSize(game.fileSize, false, 0) + ")";
            /*if (game.playCount > 0) {
                if (game.playCount == 1) {
                    historyText.text = "History: played " + game.playCount + " time on " + game.lastPlayed;
                }
                else {
                    historyText.text = "History: played " + game.playCount + " times, last time " + game.lastPlayed;
                }
            }
            else {
                historyText.text = "History: Never played";
            }*/
            releasedText.text = "Released: " + game.releaseDate
            overviewText.text = game.overview;
            reset();
        }
    }

    function reset() {
        scrollUpTimer.running = false;
        overviewScroll.scrollToTop();
        if (overviewText.height > overviewScroll.height) {
            scrollDownTimer.running = true;
        }
        else {
            scrollDownTimer.running = false;
        }
    }

    Timer {
        id: scrollDownTimer
        interval: 100
        repeat: true
        running: false
        onTriggered: function() {
            var currentY = overviewScroll.getContentItemY();
            var contentHeight = overviewScroll.getContentHeight();
            if (currentY < overviewText.height - contentHeight) {
                overviewScroll.setContentItemY(currentY + 1);
            }
            else {
                scrollDownTimer.running = false;
                scrollUpTimer.running = true;
            }
        }
    }

    Timer {
        id: scrollUpTimer
        interval: 1
        repeat: true
        running: false
        onTriggered: function() {
            var currentY = overviewScroll.getContentItemY();
            var contentHeight = overviewScroll.getContentHeight();
            if (currentY > 0) {
                overviewScroll.setContentItemY(currentY - 1);
            }
            else {
                scrollUpTimer.running = false;
                scrollDownTimer.running = true;
            }
        }
    }

    RowLayout {

        anchors.fill: parent

        ListModel {
            id: gameModel
        }

        ListModel {
            id: menuModel

            ListElement {
                name: "Play"
            }

            ListElement {
                name: "Achievements"
            }
        }

        Rectangle {
            id: menuRect
            color: Colour.menuBg
            Layout.preferredWidth: 300
            Layout.minimumWidth: 300
            Layout.maximumWidth: 300
            Layout.topMargin: 30
            Layout.bottomMargin: 30
            Layout.fillHeight: true
            Layout.fillWidth: false

            ScrollView {
                id: menuScrollView
                width: parent.width
                height: parent.height
                clip: true

                Keys.onPressed: {
                if (event.key == Qt.Key_Backspace) {
                        mainRect.backPressed();
                    }
                }

                SoundListView {
                    id: menuView
                    anchors.fill: parent
                    focus: false
                    model: menuModel
                    //navSound: navSound
                    soundOn: false
                    delegate: MenuDelegate {
                        Keys.onReturnPressed: {
                            if (name == "Play") {
                                play(game.id);
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            color: Colour.panelBg
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
                spacing: 10
                anchors.fill: parent

                HeaderText {
                    id: headerText
                    Layout.fillWidth: true
                }

                RowLayout {
                    spacing: 10

                    Item {
                        Layout.fillWidth: true
                    }

                    Image {
                        id: coverartFrontImg
                        Layout.margins: 10
                        Layout.maximumHeight: 300
                    }

                    Image {
                        id: coverartBackImg
                        Layout.margins: 10
                        Layout.maximumHeight: 300
                        visible: source || (source == "")
                    }

                    Image {
                        id: screenshotImg
                        Layout.margins: 10
                        Layout.maximumHeight: 300
                        visible: source || (source == "")
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }

                /*BodyText {
                    id: historyText
                }*/

                BodyText {
                    id: filenameText
                    Layout.fillWidth: true
                }

                BodyText {
                    id: releasedText
                    Layout.fillWidth: true
                }

                BodyText {
                    id: overviewLabel
                    text: "Overview:"
                    visible: overviewText.text != ""
                    Layout.fillWidth: true
                }

                ScrollView {
                    id: overviewScroll
                    clip: true
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOff
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 10
                    // hack for text wrapping
                    Layout.preferredWidth: mainRect.width - menuRect.width - 20
                    
                    BodyText {
                        id: overviewText
                        width: overviewScroll.width

                        /*onTextChanged: function(){
                            if (overviewText.height > overviewScroll.height) {
                                overviewScroll.ScrollBar.vertical.policy = ScrollBar.AlwaysOn;
                            }
                            else {
                                overviewScroll.ScrollBar.vertical.policy = ScrollBar.AlwaysOff;
                            }
                        }*/
                    }

                    function getContentHeight() {
                        return contentItem.height;
                    }

                    function getContentItemY() {
                        return contentItem.contentY;
                    }

                    function scrollToTop() {
                        setContentItemY(0);
                    }

                    function setContentItemY(x) {
                        contentItem.contentY = x;
                    }
                }
            }
        }
    }
}