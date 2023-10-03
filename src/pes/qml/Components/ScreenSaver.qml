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
import QtQuick.Window 2.2
import QtQuick.Controls 2.5
import QtMultimedia 5.12
import "../pes.js" as PES
import "screensaver.js" as SCREENSAVER

Rectangle {

    id: mainRect
    color: "black"
    focus: true

    // custom signals
    signal close()

    function refresh() {
        SCREENSAVER.refresh();
    }

    Component.onCompleted: {
        SCREENSAVER.init(false);
    }

    Keys.onPressed: {
        close();
        event.accepted = true;
    }

    onVisibleChanged: {
        if (visible) {
            imageTimer.start();
        }
        else {
            imageTimer.stop();
        }
    }

    Timer {
        id: imageTimer
        interval: 5000
        repeat: true
        running: false

        onTriggered: {
            SCREENSAVER.change();
        }
    }

    StackView {
        id: imgStackView
        anchors.fill: parent

        pushEnter: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 0
                to:1
                duration: 200
            }
        }
        pushExit: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 1
                to:0
                duration: 200
            }
        }
        popEnter: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 0
                to:1
                duration: 200
            }
        }
        popExit: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 1
                to:0
                duration: 200
            }
        }

        initialItem: Image {
            id: firstImg
            fillMode: Image.PreserveAspectFit
            source: ""

            Component.onCompleted: {
                imageTimer.start();
            }
        }

        Image {
            id: secondImg
            fillMode: Image.PreserveAspectFit
            source: ""
        }
    }
}
