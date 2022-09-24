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

    // private properties
    QtObject {
        id: internal
        property int btnWidth: 250
        property int btnHeight: 50
        property int labelWidth: 400
        property var systemFocusItem: hardcoreModeToggle
    }

    // signals
    signal settingsApplied()

    // functions

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    function getBluetoothEnabled() {
        return bluetoothToggle.getValue();
    }

    function getDateFormat() {
        return dateFmtCombo.getValue();
    }

    function getHardcoreMode() {
        return hardcoreModeToggle.getValue();
    }

    function getHdmiCecEnabled() {
        return hdmiCecToggle.getValue();
    }

    function getTimezone() {
        return timezoneCombo.getValue();
    }

    function saveSettings() {
        var restartRequired = hdmiCecToggle.isDirty();
        bluetoothToggle.save();
        dateFmtCombo.save();
        hardcoreModeToggle.save();
        hdmiCecToggle.save();
        timezoneCombo.save();
        if (restartRequired) {
            restartMsgBox.open();
        }
        else {
            savedMsgBox.open();
        }
        settingsApplied();
    }

    function setAvailableTimezones(zones) {
        timezoneCombo.setValues(zones);
    }

    function setBluetoothEnabled(enabled) {
        bluetoothToggle.setValue(enabled);
    }

    function setDateFormat(fmt) {
        dateFmtCombo.setValue(fmt);
    }

    function setDateFormats(fmts) {
        dateFmtCombo.setValues(fmts);
    }

    function setHardcoreMode(mode) {
        hardcoreModeToggle.setValue(mode);
    }

    function setHdmiCecEnabled(mode) {
        hdmiCecToggle.setValue(mode);
    }

    function setTimezone(zone) {
        timezoneCombo.setValue(zone);
    }

    // bluetooth disable confirm
    YesNoDialog {
        id: bluetoothDialog
        //navSound: navSound
        text: "Are you sure you want to disable Bluetooth? This could cause your controller to disconnect!"
        width: 650
        height: 200
        onYesButtonPressed: {
            saveSettings();
            bluetoothDialog.close();
        }
        onNoButtonPressed: {
            // re-enable Bluetooth
            setBluetoothEnabled(true);
        }
    }

    MessageBox {
        id: restartMsgBox
        text: "Settings saved OK.\nThe PES GUI will need to be restarted for the changes to be applied."
        width: 650
    }

    MessageBox {
        id: savedMsgBox
        text: "Settings saved OK"
        width: 650
    }

    RowLayout {

        anchors.fill: parent

        ListModel {
            id: menuModel

            ListElement {
                name: "System"
            }

            /*ListElement {
                name: "Control Pad"
            }*/
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
                            Keys.onPressed: {
                                if (event.key == Qt.Key_Right || event.key == Qt.Key_Return) {
                                    if (name == "System") {
                                        internal.systemFocusItem.forceActiveFocus();
                                    }
                                }
                            }
                        }
                        onItemHighlighted: {
                            settingsScreenStack.currentIndex = menuView.currentIndex;
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

            Keys.onPressed: {
                if (event.key == Qt.Key_Backspace) {
                    PES.goHome();
                }
            }

            StackLayout {
                id: settingsScreenStack
                anchors.fill: parent
                currentIndex: 0

                // system settings
                Rectangle {
                    color: Colour.panelBg

                    ColumnLayout {
                        width: parent.width

                        HeaderText {
                            text: "System Settings"
                        }

                        RowLayout {
                            BodyText {
                                text: "Hardcore mode:"
                                Layout.preferredWidth: internal.labelWidth
                            }

                            YesNoToggle {
                                id: hardcoreModeToggle
                                KeyNavigation.down: hdmiCecToggle
                                KeyNavigation.left: menuScrollView
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "HDMI-CEC on:"
                                Layout.preferredWidth: internal.labelWidth
                            }

                            YesNoToggle {
                                id: hdmiCecToggle
                                KeyNavigation.down: bluetoothToggle
                                KeyNavigation.up: hardcoreModeToggle
                                KeyNavigation.left: menuScrollView
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Bluetooth on:"
                                Layout.preferredWidth: internal.labelWidth
                            }

                            YesNoToggle {
                                id: bluetoothToggle
                                KeyNavigation.down: timezoneCombo
                                KeyNavigation.up: hdmiCecToggle
                                KeyNavigation.left: menuScrollView
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Timezone:"
                                Layout.preferredWidth: internal.labelWidth
                            }

                            ComboScroll {
                                id: timezoneCombo
                                values: []
                                KeyNavigation.down: dateFmtCombo
                                KeyNavigation.up: bluetoothToggle
                                KeyNavigation.left: menuScrollView
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Date/Time format:"
                                Layout.preferredWidth: internal.labelWidth
                            }

                            ComboScroll {
                                id: dateFmtCombo
                                values: []
                                KeyNavigation.down: applyBtn
                                KeyNavigation.up: timezoneCombo
                                KeyNavigation.left: menuScrollView
                            }
                        }

                        RowLayout {
                            Layout.topMargin: 100

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                            }

                            UiButton {
                                id: applyBtn
                                btnText: "Apply"
                                Layout.rightMargin: 50
                                Layout.preferredWidth: internal.btnWidth
                                Layout.preferredHeight: internal.btnHeight
                                KeyNavigation.up: dateFmtCombo
                                KeyNavigation.right: resetBtn
                                KeyNavigation.left: menuScrollView

                                Keys.onReturnPressed: {
                                    if (bluetoothToggle.isDirty() && !bluetoothToggle.getValue()) {
                                        bluetoothDialog.open();
                                    }
                                    else {
                                        saveSettings();
                                    }
                                }
                            }

                            UiButton {
                                id: resetBtn
                                btnText: "Reset"
                                Layout.preferredWidth: internal.btnWidth
                                Layout.preferredHeight: internal.btnHeight
                                KeyNavigation.up: dateFmtCombo
                                KeyNavigation.left: applyBtn

                                Keys.onReturnPressed: {
                                    bluetoothToggle.reset();
                                    dateFmtCombo.reset();
                                    hardcoreModeToggle.reset();
                                    timezoneCombo.reset();
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                            }
                        }
                    }
                }

                // control pad settings
                Rectangle {
                    id: controlPadScreen
                    color: Colour.panelBg
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    ColumnLayout {
                        HeaderText {
                            text: "Control Pad"
                        }

                        RowLayout {
                            Layout.minimumWidth: controlPadScreen.width

                            Item {
                                Layout.fillWidth: true
                            }

                            Image {
                                source: "../images/gamepad-layout.png"
                            }

                            Item {
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }
        }
    }
}