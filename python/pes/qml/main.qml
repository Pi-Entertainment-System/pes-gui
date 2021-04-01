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
//import QtGamepad 1.12
import "Components"
import "./Style/" 1.0
import "pes.js" as PES
import RomScanMonitorThread 1.0

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

	// closing dialog
	Dialog {
    id: closeDialog
    modal: true
    width: 500
    height: 150
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2

    background: Rectangle {
      color: Colour.dialogBg
      border.color: Colour.line
      anchors.fill: parent
    }

    ColumnLayout {
			anchors.fill: parent
      spacing: 10
      Text {
        color: Colour.text
        font.pointSize: FontStyle.dialogSize
        text: "Are you sure you want to exit?"
      }

      RowLayout {
        spacing: 10

				Item {
					Layout.fillHeight: true
					Layout.fillWidth: true
				}

        DialogButton {
					id: exitYesBtn
          Layout.fillWidth: false
          Layout.minimumWidth: 100
					Layout.preferredWidth: 150
					Layout.maximumWidth: 150
					Layout.minimumHeight: 50
          btnText: "Yes"
					focus: true
					KeyNavigation.right: exitNoBtn

					Keys.onReturnPressed: {
						mainWindow.close()
					}
        }

				DialogButton {
					id: exitNoBtn
          Layout.fillWidth: false
          Layout.minimumWidth: 100
					Layout.maximumWidth: 150
					Layout.preferredWidth: 150
					Layout.minimumHeight: 50
          btnText: "No"
					KeyNavigation.left: exitYesBtn

					Keys.onReturnPressed: {
						closeDialog.close()
					}
        }

				Item {
					Layout.fillHeight: true
					Layout.fillWidth: true
				}
      }
    }

		onOpened: {
			exitYesBtn.forceActiveFocus()
		}
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

    ListView {
      id: popupMenuView
      anchors.fill: parent
      focus: true
      model: popupMenu
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
		font.pointSize: FontStyle.titleSize
		font.bold: true
		font.family: FontStyle.font
		color: Colour.text
	}

	Text {
		id: clockTxt
		text: "Time"
		x: mainWindow.width - clockTxt.width
		y: 0
		font.pointSize: FontStyle.titleSize
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

		          ListView {
		            id: menuView
		            anchors.fill: parent
		            focus: true
		            model: mainMenuModel
		            delegate: MenuDelegate {
									Keys.onReturnPressed: PES.mainMenuEvent(text);
								}
		            keyNavigationEnabled: true
		            keyNavigationWraps: false
		          }
		        }
					}
					Component.onCompleted: PES.updateMainMenuModel()
				}

				Rectangle {
					id: mainScreenDisplayRect
					color: Colour.panelBg

					Layout.fillWidth: true
					Layout.fillHeight: true

					HeaderText {
		        id: welcomeText
		        text: "Welcome to PES!"
		      }

		      BodyText {
		        id: mainText
		        y: welcomeText.height + 10
		        visible: false
		        text: ""
		      }
				}
			}

      // Update games layout
      Rectangle {
        id: updateGamesRect

        color: Colour.panelBg

        RomScanMonitorThread {
          id: romScanMonitorThread

          onProgressSignal: {
            updateRomsProgressBar.progress = progress;
          }

          onProgressMessageSignal: {
            statusTxt.text = message;
          }

          onStateChangeSignal: {
            if (state == "done") {
              beginScanTxt.visible = false;
              abortScanBtn.visible = false;
              updateRomsProgressBar.visible = false;
              statusTxt.text = "Scan complete!";
            }
            else if (state == "update") {
              updateRomsProgressBar.visible = true;
            }
          }
        }

        Keys.onPressed: {
          if (event.key == Qt.Key_Backspace) {
            screenStack.currentIndex = 0;
            mainMenuScrollView.forceActiveFocus();
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
            Layout.preferredWidth: panelRect.width
            text: "Select the <i>Begin</i> button below to begin the scan. A working Inernet connection is required to download game metadata and cover art."
          }

          UiButton {
            id: beginScanBtn
            btnText: "Begin"

            Layout.preferredWidth: 100
            Layout.preferredHeight: 50
            Layout.leftMargin: 30

            Keys.onReturnPressed: {
              this.visible = false;
              abortScanBtn.visible = true;
              abortScanBtn.forceActiveFocus();
              updateRomsProgressBar.progress = 0;
              statusTxt.visible = true;
              romScanMonitorThread.start();
            }
          }

          BodyText {
            id: statusTxt
            text: "Scanning..."
            visible: false
          }

          /*IndeterminateProgressBar {
            id: romSearchProgessBar
            visible: false

            Layout.leftMargin: 30
            Layout.rightMargin: 30
            Layout.preferredWidth: panelRect.width - 60
            Layout.preferredHeight: 50
          }*/

          ProgressBar {
            id: updateRomsProgressBar
            visible: false
            progress: 0

            Layout.leftMargin: 30
            Layout.rightMargin: 30
            Layout.preferredWidth: panelRect.width - 60
            Layout.preferredHeight: 50
          }

          UiButton {
            id: abortScanBtn
            btnText: "Abort"
            visible: false

            Layout.preferredWidth: 100
            Layout.preferredHeight: 50
            Layout.leftMargin: 30
            Layout.topMargin: 20
          }
        }
      }
		}
	}
}
