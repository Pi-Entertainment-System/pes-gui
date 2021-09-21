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
    color: Colour.panelBg

    property alias headerText: headerText.text
    property alias overviewText: overviewText.text
    property alias coverartFrontSrc: covertartFrontImg.source
    property alias coverartBackSrc: covertartBackImg.source

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
        interval: 50
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

    ColumnLayout {
        spacing: 10

        HeaderText {
            id: headerText
            Layout.fillWidth: true
        }

        RowLayout {
            spacing: 10

            Image {
                id: covertartFrontImg
                Layout.margins: 10
            }

            Image {
                id: covertartBackImg
                Layout.margins: 10
                visible: source || (source == "")
            }
        }

        ScrollView {
            id: overviewScroll
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn
            //ScrollBar.vertical.position: 1.0
            Layout.fillWidth: true
            Layout.preferredHeight: 300
            // hack for text wrapping
            Layout.preferredWidth: mainRect.width
            
            BodyText {
                id: overviewText
                width: overviewScroll.width

                onTextChanged: function(){
                    if (overviewText.height > overviewScroll.height) {
                        overviewScroll.ScrollBar.vertical.policy = ScrollBar.AlwaysOn;
                    }
                    else {
                        overviewScroll.ScrollBar.vertical.policy = ScrollBar.AlwaysOff;
                    }
                }
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