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

    function forceActiveFocus() {
        menuView.forceActiveFocus();
    }

    function setAvailableTimezones(zones) {
        timezoneCombo.setValues(zones);
    }

    function setBluetoothEnabled(enabled) {
        bluetoothToggle.setValue(enabled);
    }

    function setDatetimeFormat(fmt) {
        dateFmtCombo.setValue(fmt);
    }

    function setHardcoreMode(mode) {
        hardcoreModeToggle.setValue(mode);
    }

    function setTimezone(zone) {
        timezoneCombo.setValue(zone);
    }

    RowLayout {

        anchors.fill: parent

        ListModel {
            id: menuModel

            ListElement {
                name: "System"
            }

            ListElement {
                name: "Control Pad"
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
                                KeyNavigation.down: bluetoothToggle
                                KeyNavigation.left: menuScrollView
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Bluetooth:"
                                Layout.preferredWidth: internal.labelWidth
                            }

                            YesNoToggle {
                                id: bluetoothToggle
                                KeyNavigation.down: timezoneCombo
                                KeyNavigation.up: hardcoreModeToggle
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
                                values: ["dd/mm/yyyy", "mm/dd/yyyy"]
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
                                    bluetoothToggle.save();
                                    dateFmtCombo.save();
                                    hardcoreModeToggle.save();
                                    timezoneCombo.save();
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