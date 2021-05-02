/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2020 Neil Munday (neil@mundayweb.com)

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
//import QtGamepad 1.12
import "Components"
import "./Style/" 1.0
import "pes.js" as PES

ApplicationWindow {

  id: mainWindow
  visible: true
  color: Colour.bg
  //height: 600
  //width: 800
  visibility: "FullScreen"

  onClosing: backend.close()

	Connections {
	    target: backend

			onHomeButtonPress: {
				//pesDialog.open();
	      //popupMenuView.forceActiveFocus();
			}

			onControlPadButtonPress: {
				console.warn("button: " + button);
				console.warn(mainWindow.activeFocusItem.Keys.downPressed({ key: Qt.KeyDown }));
			}
	}

  // sounds
  SoundEffect {
    id: navSound
    source: "sounds/slide-scissors.wav"
    loops: 1
  }

	// closing dialog
  YesNoDialog {
    id: closeDialog
    navSound: navSound
    text: "Are you sure you want to exit?"
    onYesButtonPressed: mainWindow.close()
  }

	// options dialog
  Dialog {
    id: optionsDialog
    modal: true
    width: 500
    height: 274
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2

    background: Rectangle {
      color: Colour.menuBg
      border.color: Colour.line
    }

    ListModel {
      id: popupMenu

      ListElement {
        name: "Update Games"
      }

      ListElement {
        name: "Settings"
      }

      ListElement {
        name: "Reboot"
      }

      ListElement {
        name: "Shutdown"
      }

      ListElement {
        name: "Exit"
      }
    }

    SoundListView {
      id: popupMenuView
      anchors.fill: parent
      focus: true
      model: popupMenu
      navSound: navSound
      delegate: MenuDelegate {
				Keys.onReturnPressed: PES.optionsDialogEvent(text);
			}
      keyNavigationEnabled: true
      keyNavigationWraps: true
    }

		onOpened: popupMenuView.forceActiveFocus()
  }

  // shortcuts
  Shortcut {
    sequence: "Home"
    onActivated: optionsDialog.open()
  }

  Shortcut {
    sequence: "Esc"
    onActivated: closeDialog.open()
  }

	// models
	ListModel {
		id: mainMenuModel

		ListElement {
			name: "Home"
		}
	}

	// layout
	Text {
		id: titleTxt
		text: "Pi Entertainment System"
		x: 0
		y: 0
		font.pixelSize: FontStyle.titleSize
		font.bold: true
		font.family: FontStyle.font
		color: Colour.text
	}

	Text {
		id: clockTxt
		text: "Time"
		x: mainWindow.width - clockTxt.width
		y: 0
		font.pixelSize: FontStyle.titleSize
		font.bold: true
		font.family: FontStyle.font
		color: Colour.text
		rightPadding: 5
	}

	Timer {
		interval: 1000
		running: true
		repeat: true
		onTriggered: {
      clockTxt.text = backend.getTime();
    }
	}

	Rectangle {
		id: headerLine
		x: 0
		y: 32
		height: 2
		width: mainWindow.width
		color: Colour.line
	}

	Rectangle {
		id: panelRect
		color: Colour.menuBg
		x: 0
		y: headerLine.y + headerLine.height + 1
		height: parent.height - this.y
		width: parent.width

		StackLayout {
      id: screenStack
			anchors.fill: parent
      currentIndex: 0
      // main layout
			RowLayout {

				spacing: 0

				Rectangle {

					id: mainMenuRect
					Layout.preferredWidth: 300
					Layout.minimumWidth: 300
					Layout.maximumWidth: 300
					Layout.topMargin: 30
					Layout.bottomMargin: 30
					Layout.fillHeight: true
					Layout.fillWidth: false

					color: Colour.menuBg

					Rectangle {
		        x: 0
		        y: parent.y
		        width: parent.width
		        height: parent.height - this.y
		        color: parent.color

		        ScrollView {
              id: mainMenuScrollView
		          width: parent.width
		          height: parent.height
		          clip: true
		          focus: true

		          SoundListView {
		            id: mainMenuView
		            anchors.fill: parent
		            focus: false
		            model: mainMenuModel
                navSound: navSound
                soundOn: false
		            delegate: MenuDelegate {
									Keys.onReturnPressed: PES.mainMenuEvent(mainMenuModel.get(mainMenuView.currentIndex));
                  Keys.onRightPressed: PES.setCoverartPanelFocus()
								}
                onItemHighlighted: {
                  // console objects in the model will have ID set
                  if (item.id) {
                    PES.updateCoverartPanels(item.id);
                  }
                  else {
                    PES.updateCoverartPanels(0);
                  }
                }
		          }
		        }
					}
					Component.onCompleted: PES.updateMainScreen()
				}

				Rectangle {
					id: mainScreenDisplayRect
					color: Colour.panelBg

					Layout.fillWidth: true
					Layout.fillHeight: true

          ColumnLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            spacing: 10

            Keys.onPressed: {
              if (event.key == Qt.Key_Backspace) {
                event.accepted = true;
                recentlyAddedMainPanel.loseFocus();
                recentlyPlayedMainPanel.loseFocus();
                mainMenuView.forceActiveFocus();
              }
            }

            HeaderText {
              id: welcomeText
              text: "Welcome to PES!"

              Layout.fillWidth: true
            }

            BodyText {
              id: mainText
              visible: false
              text: ""
              Layout.fillWidth: true
            }

            CoverartPanel {
              id: recentlyPlayedMainPanel
              color: Colour.panelBg
              headerText: "Recently Played Games"
              height: 300
              KeyNavigation.left: mainMenuScrollView
              KeyNavigation.down: recentlyAddedMainPanel
              Layout.fillWidth: true
              navSound: navSound
              visible: false

              onItemSelected: function(gameId) {
                var r = backend.playGame(gameId);
                if (!r.result) {
                  // @TODO: implement error message dialog
                }
              }
            }

            CoverartPanel {
              id: recentlyAddedMainPanel
              color: Colour.panelBg
              headerText: "Recently Added Games"
              height: 300
              KeyNavigation.left: mainMenuScrollView
              KeyNavigation.up: recentlyPlayedMainPanel
              Layout.fillWidth: true
              navSound: navSound
              visible: false

              onItemSelected: function(gameId) {
                var r = backend.playGame(gameId);
                if (!r.result) {
                  // @TODO: implement error message dialog
                }
              }
            }
          }
				}
			}

      // Update games layout
      UpdateGamesScreen {
        id: updateGamesScreen
        Layout.fillWidth: true
        Layout.fillHeight: true
      }
		}
	}
}
