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
import "../pes.js" as PES
import RomScanMonitorThread 1.0

Rectangle {
    id: updateGamesRect
    color: Colour.panelBg

    signal scanCompleted()

    function abortRomScan() {
        romScanMonitorThread.stop();
        abortScanBtn.visible = false;
    }

    function beginRomScan(fullscan) {
        beginScanTxt.visible = false;
        beginScanLayout.visible = false;
        beginFullScanLayout.visible = false;
        abortScanBtn.visible = true;
        abortScanBtn.forceActiveFocus();
        updateRomsProgressBar.progress = 0;
        statusTxt.visible = true;
        statusTxt.text = "";
        scanPreviewImg.visible = false;
        scanPreviewTxt.visible = false;
        romScanMonitorThread.fullscan = fullscan;
        romScanMonitorThread.start();
    }

    function reset() {
        beginScanLayout.visible = true;
        beginFullScanLayout.visible = true;
        beginScanBtn.forceActiveFocus();
        beginScanTxt.visible = true;
        abortScanBtn.visible = false;
        homeBtn.visible = false;
        updateRomsProgressBar.visible = false;
        statusTxt.visible = false;
    }

    RomScanMonitorThread {
        id: romScanMonitorThread

        onProgressSignal: {
            updateRomsProgressBar.progress = progress;
            if (coverart) {
                scanPreviewImg.source = "file://" + coverart;
                scanPreviewTxt.text = name;
                if (!scanPreviewImg.visible) {
                    scanPreviewImg.visible = true;
                    scanPreviewTxt.visible = true;
                }
            }
        }

        onProgressMessageSignal: {
            if (romScanMonitorThread.interrupted) {
                statusTxt.text = "Aborting scan, please wait..";
            }
            else {
                statusTxt.text = message;
            }
        }

        onStateChangeSignal: {
            if (state == "done") {
                beginScanTxt.visible = false;
                abortScanBtn.visible = false;
                homeBtn.visible = true;
                scanPreviewImg.visible = false;
                scanPreviewTxt.visible = false;
                updateRomsProgressBar.visible = false;
                beginScanLayout.visible = false;
                beginFullScanLayout.visible = false;
                var s;
                if (romScanMonitorThread.interrupted) {
                    s = "aborted";
                }
                else {
                    s = "complete";
                }
                statusTxt.text = "<p>Scan " + s + "!</p><p>Added: " + romScanMonitorThread.added + "</p><p>Updated: " + romScanMonitorThread.updated + "</p><p>Skipped: " + romScanMonitorThread.skipped + "</p><p>Deleted: " + romScanMonitorThread.deleted + "</p><p>Time taken: " + romScanMonitorThread.timeTaken + "s</p>";
                updateGamesRect.scanCompleted();
                homeBtn.forceActiveFocus();
            }
            else if (state == "update") {
                updateRomsProgressBar.visible = true;
            }
        }
    }

    Keys.onPressed: {
        if (event.key == Qt.Key_Backspace) {
            PES.goHome();
            event.accepted = true;
        }
    }

    ColumnLayout {

        spacing: 10

        HeaderText {
            Layout.fillWidth: true
            text: "Update Games"
        }

        BodyText {
            id: beginScanTxt
            Layout.fillWidth: true
            Layout.preferredWidth: updateGamesRect.width
            text: "Select the type of scan that you would like to perfrom using the buttons below. A working Inernet connection is required to download images."
        }

        RowLayout {
            id: beginScanLayout

            UiButton {
                id: beginScanBtn
                btnText: "Normal Scan"

                Layout.preferredWidth: 220
                Layout.preferredHeight: 50
                Layout.leftMargin: 30

                KeyNavigation.down: beginFullScanBtn
                onButtonPressed: beginRomScan(false)
            }

            BodyText {
                text: "Add new ROMs and remove any deleted ROMs from the database as well as downloading images"
                Layout.fillWidth: true
                // horrible hack to fix text wrapping/width
                Layout.preferredWidth: updateGamesRect.width - beginScanBtn.Layout.preferredWidth - beginScanBtn.Layout.leftMargin
            }
        }

        RowLayout {
            id: beginFullScanLayout

            UiButton {
                id: beginFullScanBtn
                btnText: "Full Scan"

                Layout.preferredWidth: 220
                Layout.preferredHeight: 50
                Layout.leftMargin: 30

                KeyNavigation.down: beginScanBtn
                onButtonPressed: beginRomScan(true)
            }

            BodyText {
                text: "Same as a normal scan but also refresh images from the Internet"
                Layout.fillWidth: true
                // horrible hack to fix text wrapping/width
                Layout.preferredWidth: updateGamesRect.width - beginScanBtn.Layout.preferredWidth - beginScanBtn.Layout.leftMargin
            }
        }

        BodyText {
            id: statusTxt
            text: "Scanning..."
            visible: false
        }

        ProgressBarRect {
            id: updateRomsProgressBar
            visible: false
            progress: 0
            Layout.leftMargin: 30
            Layout.rightMargin: 30
            Layout.fillWidth: true
            Layout.preferredHeight: 50
        }

        Image {
            id: scanPreviewImg
            visible: false
            Layout.preferredWidth: 300
            Layout.preferredHeight: 300
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
        }

        BodyText {
            id: scanPreviewTxt
            horizontalAlignment: Text.AlignHCenter
            text: ""
            visible: false
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            Layout.preferredWidth: updateGamesRect.width
        }

        UiButton {
            id: abortScanBtn
            btnText: "Abort"
            visible: false
            Layout.preferredWidth: 100
            Layout.preferredHeight: 50
            Layout.leftMargin: 30
            Layout.topMargin: 20
            onButtonPressed: updateGamesRect.abortRomScan()
        }

        UiButton {
            id: homeBtn
            btnText: "Home"
            visible: false
            Layout.preferredWidth: 100
            Layout.preferredHeight: 50
            Layout.leftMargin: 30
            Layout.topMargin: 20
            onButtonPressed: PES.goHome()
        }
    }
}
