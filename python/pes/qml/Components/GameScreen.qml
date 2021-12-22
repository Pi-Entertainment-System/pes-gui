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
import RetroAchievementUser 1.0
import RetroAchievementThread 1.0
import "../Style/" 1.0
import "../pes.js" as PES

Rectangle {

    id: mainRect
    color: "transparent"

    property var game: null
    property var retroUser: null

    signal backPressed()
    signal play(int gameId)

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    onGameChanged: function() {
        if (game) {
            backgroundImg.source = PES.getConsoleArt(game.consoleId);
            infoHeaderText.text = game.name;
            achievementHeaderText.text = game.name;
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

            if (game.retroId > 0 && retroUser && retroUser.hasApiKey()) {
                achievementBodyText.text = "Loading achievements...";
                retroThread.gameId = game.id;
                retroThread.retroGameId = game.retroId;
                retroThread.start();
            }
            else {
                __noAchievements();
            }
        }
    }

    function __noAchievements() {
        achievementBodyText.text = "There are no achievements associated with this game.";
    }

    function reset() {
        screenStack.currentIndex = 0
        menuView.currentIndex = 0;
        badgeModel.clear();
        scrollUpTimer.running = false;
        overviewScroll.scrollToTop();
        if (overviewText.height > overviewScroll.height) {
            scrollDownTimer.running = true;
        }
        else {
            scrollDownTimer.running = false;
        }
    }

    RetroAchievementThread {
        id: retroThread
        user: retroUser

        onFinished: {
            var badges = retroThread.getBadges();
            if (badges && badges.length > 0) {
                var retroGame = retroThread.getRetroGame();
                var earned = 0;
                for (var i = 0; i < badges.length; i++) {
                    if (badges[i].earned || badges[i].earnedHardcore) {
                        earned++;
                    }
                    badges[i]["playersEarnedPercent"] = Math.round((badges[i].totalAwarded / retroGame.totalPlayers) * 100);
                    badgeModel.append(badges[i]);
                }
                var percent = Math.round((earned / badges.length) * 100);
                achievementBodyText.text = "Score: " + retroGame.score + ", " + percent + "% complete\n" + badges.length + " badges found.";
            }
            else {
                __noAchievements();
            }
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

    Component {
        id: badgeDelegate

        Rectangle {
            height: badgeDelegateLayout.height
            width: badgesListView.width
            border.color: Colour.line
            border.width: focus ? 2: 0
            color: focus ? Colour.badgeFocusBg : Colour.badgeBg

            ColumnLayout {
                id: badgeDelegateLayout
                spacing: 3
                width: parent.width

                BodyText {
                    text: title
                }
                
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 20
                    Layout.bottomMargin: 5

                    ColumnLayout {
                        Layout.rightMargin: 20
                        spacing: 0
                        Image {
                            id: badgeImg
                            source: earned || earnedHardcore ? "file://" + unlockedPath : "file://" + lockedPath
                        }
                        SmallText {
                            text: points + "pts"
                            padding: 0
                        }
                    }

                    ColumnLayout {
                        spacing: 1
                        BodyText {
                            text: description
                            font.bold: false
                            padding: 0
                            Layout.maximumWidth: badgesListView.width - 380 - badgeImg.width
                        }

                        SmallText {
                            text: earned ? "Earned: " + earnedStr : ""
                            padding: 0
                        }

                        SmallText {
                            text: earnedHardcore ? "Hardcore Earned: " + earnedHardcoreStr : ""
                            padding: 0
                        }
                    }
                    // spacer
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }

                    ColumnLayout {
                        Layout.maximumWidth: 380
                        Layout.rightMargin: 10
                        
                        RowLayout {

                            SmallText {
                                text: "Casual: "
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                            }

                            ProgressBarRect {
                                width: 200
                                height: 20
                                progress: playersEarnedPercent / 100
                            }
                        }

                        RowLayout {

                            SmallText {
                                text: "Hardcore: "
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                            }

                            ProgressBarRect {
                                width: 200
                                height: 20
                                progress: playersEarnedPercent / 100
                            }
                        }
                    }
                }
            }
        }
    }

    RowLayout {
        anchors.fill: parent

        ListModel {
            id: badgeModel
        }

        ListModel {
            id: menuModel

            ListElement {
                name: "Play"
                stackId: 0
            }

            ListElement {
                name: "Achievements"
                stackId: 1
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
                        Keys.onPressed: {
                            if (event.key == Qt.Key_Return && name == "Play") {
                                play(game.id);
                            }
                            else if ((event.key == Qt.Key_Return || event.key == Qt.Key_Right) && name == "Achievements") {
                                if (badgesListView.currentIndex == -1) {
                                    badgesListView.currentIndex = 0;
                                }
                                badgesListView.forceActiveFocus();
                            }
                        }
                    }
                    onItemHighlighted: {
                        screenStack.currentIndex = item.stackId;
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

            StackLayout {
                id: screenStack
                anchors.fill: parent

                // put screens inside a rectangle to prevent polish loop
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        HeaderText {
                            id: infoHeaderText
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

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"

                    ColumnLayout {
                        spacing: 10
                        anchors.fill: parent

                        HeaderText {
                            id: achievementHeaderText
                            Layout.fillWidth: true
                        }

                        BodyText {
                            id: achievementBodyText
                            text: ""
                            Layout.fillWidth: true
                        }

                        ScrollView {
                            id: badgesScrollView
                            clip: true
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            Layout.leftMargin: 20
                            Layout.rightMargin: 20

                            ListView {
                                id: badgesListView
                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                currentIndex: -1
                                delegate: badgeDelegate
                                focus: true
                                keyNavigationEnabled: true
                                keyNavigationWraps: false
                                model: badgeModel
                                orientation: Qt.Vertical
                                spacing: 20

                                Keys.onPressed: {
                                    if (event.key == Qt.Key_Backspace || event.key == Qt.Key_Left) {
                                        menuView.forceActiveFocus();
                                        currentItem.focus = false;
                                        currentIndex = -1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}