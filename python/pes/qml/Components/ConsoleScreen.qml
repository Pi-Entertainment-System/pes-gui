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

    id: mainRect
    color: "transparent"

    // can't use "console" as a variable name!
    property var consoleObj: null

    // custom signals
    signal addFavourite(int gameId)
    signal removeFavourite(int gameId)
    signal gameSelected(int gameId)

    // listeners
    onAddFavourite: function(gameId) {
        _processFavouriteEvent();
    }

    onRemoveFavourite: function(gameId) {
        _processFavouriteEvent();
    }

    function addGame(game) {
        gameModel.append(game);
    }

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    function gridFocus() {
        if (gameModel.count > 0) {
            if (internal.gameIndex == -1) {
                gridView.currentIndex = 0;
                internal.gameIndex = 0;
            }
            else {
                gridView.currentIndex = internal.gameIndex;
            }
            gridView.forceActiveFocus();
        }
    }

    function _processFavouriteEvent() {
        internal.useFavouriteCache = false;
        internal.useGameCache = false;
        internal.useMostPlayedCache = false;
        internal.useRecentlyAddedCache = false;
        internal.useRecentlyPlayedCache = false;
        if (menuModel.get(menuView.currentIndex).name == "Favourites") {
            refresh();
            gridFocus();
        }
    }

    function refresh() {
        gameModel.clear();
        var games = null;
        switch (menuModel.get(menuView.currentIndex).name) {
            case "Browse": {
                games = PES.getGames(consoleObj.id, internal.useGameCache);
                internal.useGameCache = true;
                break;
            }
            case "Recently Added": {
                games = PES.getRecentlyAddedGames(consoleObj.id, 0, internal.useRecentlyAddedCache);
                internal.useRecentlyAddedCache = true;
                break;
            }
            case "Recently Played": {
                games = PES.getRecentlyPlayedGames(consoleObj.id, 0, internal.useRecentlyPlayedCache);
                internal.useRecentlyPlayedCache = true;
                break;
            }
            case "Most Played": {
                games = PES.getMostPlayedGames(consoleObj.id, 0, internal.useMostPlayedCache);
                internal.useMostPlayedCache = true;
                break;
            }
            case "Favourites": {
                games = PES.getFavouriteGames(consoleObj.id, internal.useFavouriteCache);
                internal.useFavouriteCache = true;
                break;
            }
        }

        for (var i = 0; i < games.length; i++) {
            addGame(games[i]);
        }

        gridView.currentIndex = -1;
        internal.gameIndex = -1;
    }

    onConsoleObjChanged: {
        headerText.text = consoleObj.name;
        backgroundImg.source = PES.getConsoleArt(consoleObj.id);
        menuView.currentIndex = 0;
        internal.useRecentlyAddedCache = false;
        internal.useRecentlyPlayedCache = false;
        internal.useMostPlayedCache = false;
        internal.useGameCache = false;
        internal.useFavouriteCache = false;
        refresh();
    }

    QtObject {
        id: internal
        property int gameIndex: -1
        property bool useRecentlyAddedCache: false
        property bool useRecentlyPlayedCache: false
        property bool useMostPlayedCache: false
        property bool useGameCache: false
        property bool useFavouriteCache: false;
    }

    RowLayout {

        anchors.fill: parent

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

                Keys.onPressed: {
                    if (event.key == Qt.Key_Return) {
                        internal.gameIndex = gridView.currentIndex;
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
                width: parent.width
                height: parent.height - this.y
                color: parent.color

                ScrollView {
                    id: menuScrollView
                    width: parent.width
                    height: parent.height
                    clip: true

                    Keys.onPressed: {
                    if (event.key == Qt.Key_Backspace) {
                            PES.goHome();
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
                            Keys.onReturnPressed: gridFocus()
                            Keys.onRightPressed: gridFocus()
                        }
                        onItemHighlighted: {
                            refresh();
                        }
                    }
                }
            }
        }

        Rectangle {
            id: screenDisplayRect
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

                BodyText {
                    id: noGamesText
                    text: "No games found"
                    visible: gameModel.count == 0
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

                        Keys.onPressed: {
                            if (event.key == Qt.Key_Backspace || (event.key == Qt.Key_Left && currentIndex == 0)) {
                                internal.gameIndex = currentIndex;
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