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

    function forceActiveFocus() {
        menuView.forceActiveFocus();
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
                            
                        }
                        onItemHighlighted: {
                            screenStack.currentIndex = menuView.currentIndex;
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
                id: screenStack
                anchors.fill: parent
                currentIndex: 0

                // system settings
                Rectangle {
                    color: Colour.panelBg

                    ColumnLayout {
                        HeaderText {
                            text: "System Settings"
                        }

                        RowLayout {
                            BodyText {
                                text: "Hardcore mode:"
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Bluetooth:"
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Timezone:"
                            }
                        }

                        RowLayout {
                            BodyText {
                                text: "Date/Time format:"
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