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
import RetroAchievementUser 1.0
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

  QtObject {
    id: mainWindowInternal
    property var restoreFocusItem: null
  }

  RetroAchievementUser {
    id: retroUser
  }

	Connections {
	    target: backend

			function onHomeButtonPress() {
        PES.goHome();
			}

			function onControlPadButtonPress() {
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
    //navSound: navSound
    text: "Are you sure you want to exit?"
    onYesButtonPressed: mainWindow.close()
  }

  // poweroff dialog
  YesNoDialog {
    id: poweroffDialog
    //navSound: navSound
    text: "Are you sure you want to power off?"
    onNoButtonPressed: powerDialog.forceActiveFocus()
    onYesButtonPressed: {
      mainWindow.close();
      backend.shutdown();
    }
  }

  // reboot dialog
  YesNoDialog {
    id: rebootDialog
    //navSound: navSound
    text: "Are you sure you want to reboot?"
    onNoButtonPressed: powerDialog.forceActiveFocus()
    onYesButtonPressed: {
      mainWindow.close();
      backend.reboot();
    }
  }

  // message box
  MessageBox {
    id: msgBox
    text: ""
    width: mainWindow.width - (mainWindow.width * 0.25)
  }

	// options dialog
  Dialog {
    id: optionsDialog
    modal: true
    width: 500
    height: 65 * optionsPopupMenu.count
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2

    background: Rectangle {
      color: Colour.menuBg
      border.color: Colour.line
    }

    ListModel {
      id: optionsPopupMenu

      ListElement {
        name: "Update Games"
      }

      ListElement {
        name: "Settings"
      }
    }

    SoundListView {
      id: optionsPopupMenuView
      anchors.fill: parent
      focus: true
      model: optionsPopupMenu
      //navSound: navSound
      delegate: MenuDelegate {
        width: optionsPopupMenuView.width
				Keys.onReturnPressed: PES.optionsDialogEvent(text);
        Keys.onPressed: {
          // no onBackspace event that I can see!
          if (event.key == Qt.Key_Backspace) {
            optionsDialog.close();
            event.accepted = true;
          }
        }
			}
      keyNavigationEnabled: true
      keyNavigationWraps: true
    }

		onOpened: optionsPopupMenuView.forceActiveFocus()
  }

	// power dialog
  Dialog {
    id: powerDialog
    modal: true
    width: 500
    height: 65 * powerPopupMenu.count
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2

    background: Rectangle {
      color: Colour.menuBg
      border.color: Colour.line
    }

    ListModel {
      id: powerPopupMenu

      ListElement {
        name: "Reboot"
      }

      ListElement {
        name: "Power Off"
      }

      ListElement {
        name: "Exit"
      }
    }

    SoundListView {
      id: powerPopupMenuView
      anchors.fill: parent
      focus: true
      model: powerPopupMenu
      //navSound: navSound
      delegate: MenuDelegate {
        width: powerPopupMenuView.width
				Keys.onReturnPressed: PES.powerDialogEvent(text);
        Keys.onPressed: {
          // no onBackspace event that I can see!
          if (event.key == Qt.Key_Backspace) {
            powerDialog.close();
            event.accepted = true;
          }
        }
			}
      keyNavigationEnabled: true
      keyNavigationWraps: true
    }
		onOpened: powerPopupMenuView.forceActiveFocus()
  }

  // shortcuts
  Shortcut {
    sequence: "Home"
    onActivated: PES.goHome()
  }

  Shortcut {
    sequence: "Esc"
    onActivated: powerDialog.open()
  }

	// models
	ListModel {
		id: mainMenuModel

		ListElement {
			name: "Home"
		}
	}

  // screen saver timer
  Timer {
    id: screenSaverTimer
    interval: 1000 * 120
    repeat: false
    running: true

    Component.onCompleted: {
      interval = backend.getScreenSaverTimeout() * 1000 * 60
    }

    onTriggered: {
      mainWindowInternal.restoreFocusItem = mainWindow.activeFocusItem;
      mainStackView.push(screenSaver);
      screenSaver.forceActiveFocus();
    }
  }

  StackView {
    id: mainStackView
    anchors.fill: parent

    Keys.onReleased: {
      screenSaverTimer.restart();
      event.accepted = false;
    }

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

    initialItem: Rectangle {
      id: mainRect

      // layout
      Rectangle {
        id: headerRect
        x: 0
        y: 0
        color: Colour.bg
        height: 40
        width: mainWindow.width

        RowLayout {
          anchors.fill: parent

          TitleText {
            id: titleTxt
            text: "Pi Entertainment System"
          }

          TitleText {
            id: retroHeaderTxt
            text: " | " + retroUser.username + " (" + retroUser.score + ")"
            visible: retroUser.loggedIn
          }

          // filler to force right alignment
          Item {
            Layout.fillWidth: true
          }

          Image {
            id: gamepadIcon
            source: "icons/gamepad.png"
            visible: false
            // connecting directly to gamepadTotal propery via visible
            // property can result in a race conditon where backend
            // is null, therefore use the following workaround
            function visibleHandler(total) {
              visible = total > 0;
            }

            Component.onCompleted: {
              visible = backend.gamepadTotal;
              backend.gamepadTotalSignal.connect(visibleHandler);
            }
          }

          Image {
            id: bluetoothIcon
            source: "icons/bluetooth.png"
            visible: false

            Component.onCompleted: {
              visible = backend.btAvailable();
            }
          }

          Image {
            id: trophyIcon
            source: "icons/trophy.png"
            visible: retroUser.loggedIn

            Component.onCompleted: {
              retroUser.login();
            }
          }

          Image {
            id: remoteIcon
            source: "icons/remote.png"
            visible: false

            Component.onCompleted: {
              remoteIcon.visible = backend.cecEnabled;
            }
          }

          Image {
            id: networkIcon
            source: "icons/network.png"
            visible: false

            Component.onCompleted: {
              networkIcon.visible = backend.getNetworkAvailable();
            }
          }

          TitleText {
            id: clockTxt
            text: "Time"
            Layout.leftMargin: 10
            Layout.rightMargin: 5
          }
        }
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
        y: headerRect.height
        height: 2
        width: mainWindow.width
        color: Colour.line
      }

      Rectangle {
        id: panelRect
        color: Colour.menuBg
        x: 0
        y: headerLine.y + headerLine.height
        height: parent.height - y
        width: parent.width

        StackLayout {
          id: screenStack
          anchors.fill: parent
          currentIndex: 0

          // main layout
          StackView {
            id: mainScreenStackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            initialItem: RowLayout {
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

                ColumnLayout {

                  RowLayout {
                    UiIconButton {
                      id: powerBtn
                      source: "icons/power-button.png"
                      KeyNavigation.right: kodiBtn
                      Keys.onDownPressed: {
                        mainMenuScrollView.forceActiveFocus()
                        mainMenuView.currentIndex = 0
                      }
                      Keys.onUpPressed: {
                        mainMenuScrollView.forceActiveFocus()
                        mainMenuView.currentIndex = mainMenuView.count - 1
                      }
                      Keys.onReturnPressed: powerDialog.open()
                    }

                    UiIconButton {
                      id: kodiBtn
                      source: "icons/film-strip.png"
                      KeyNavigation.right: settingsBtn
                      KeyNavigation.left: powerBtn
                      Keys.onDownPressed: {
                        mainMenuScrollView.forceActiveFocus()
                        mainMenuView.currentIndex = 0
                      }
                      Keys.onUpPressed: {
                        mainMenuScrollView.forceActiveFocus()
                        mainMenuView.currentIndex = mainMenuView.count - 1
                      }
                      Keys.onReturnPressed: backend.loadKodi()
                    }

                    UiIconButton {
                      id: settingsBtn
                      source: "icons/cog.png"
                      KeyNavigation.left: kodiBtn
                      Keys.onDownPressed: {
                        mainMenuScrollView.forceActiveFocus()
                        mainMenuView.currentIndex = 0
                      }
                      Keys.onUpPressed: {
                        mainMenuScrollView.forceActiveFocus()
                        mainMenuView.currentIndex = mainMenuView.count - 1
                      }
                      Keys.onReturnPressed: optionsDialog.open()
                    }
                  }

                  ScrollView {
                    id: mainMenuScrollView
                    Layout.topMargin: 10
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: mainMenuRect.Layout.minimumWidth
                    clip: true
                    focus: true

                    SoundListView {
                      id: mainMenuView
                      anchors.fill: parent
                      focus: false
                      focusBottom: powerBtn
                      focusTop: powerBtn
                      model: mainMenuModel
                      //navSound: navSound
                      soundOn: false
                      delegate: MenuDelegate {
                        width: mainMenuView.width
                        Keys.onReturnPressed: PES.mainMenuEvent()
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

                  Component.onCompleted: PES.updateMainScreen()
                }
              }

              Rectangle {
                id: mainScreenDisplayRect
                color: Colour.panelBg

                Layout.fillWidth: true
                Layout.fillHeight: true

                Image {
                  id: mainBackgroundImg
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
                    color: "transparent"
                    headerText: "Recently Played Games"
                    height: 300
                    keyLeft: mainMenuScrollView
                    keyDown: recentlyAddedMainPanel
                    Layout.fillWidth: true
                    //navSound: navSound
                    visible: false

                    onAddFavourite: function(gameId) {
                      PES.favouriteGame(gameId, true);
                    }

                    onGameSelected: function(gameId) {
                      PES.loadGameScreen(mainScreenStackView, mainGameScreen, gameId);
                    }

                    onRemoveFavourite: function(gameId) {
                      PES.favouriteGame(gameId, false);
                    }
                  }

                  CoverartPanel {
                    id: recentlyAddedMainPanel
                    color: "transparent"
                    headerText: "Recently Added Games"
                    height: 300
                    keyLeft: mainMenuScrollView
                    keyUp: recentlyPlayedMainPanel
                    keyDown: exploreBtn
                    Layout.fillWidth: true
                    //navSound: navSound
                    visible: false

                    onAddFavourite: function(gameId) {
                      PES.favouriteGame(gameId, true);
                    }

                    onGameSelected: function(gameId) {
                      PES.loadGameScreen(mainScreenStackView, mainGameScreen, gameId);
                    }

                    onRemoveFavourite: function(gameId) {
                      PES.favouriteGame(gameId, false);
                    }
                  }

                  UiButton {
                    id: exploreBtn
                    btnText: "Explore"
                    height: 50
                    width: 200
                    visible: false
                    KeyNavigation.left: mainMenuScrollView
                    KeyNavigation.up: recentlyAddedMainPanel.visible ? recentlyAddedMainPanel : recentlyPlayedMainPanel

                    Keys.onReturnPressed: {
                      PES.loadConsoleScreen(PES.getCurrentConsole());
                    }
                  }
                }
              }
            }

            GameScreen {
              id: mainGameScreen
              retroUser: retroUser
              visible: false

              onBackPressed: {
                mainScreenStackView.pop();
                mainGameScreen.visible = false;
                if (recentlyPlayedMainPanel.visible && recentlyPlayedMainPanel.isGameSelected()) {
                  recentlyPlayedMainPanel.gainFocus();
                }
                else if (recentlyAddedMainPanel.visible && recentlyAddedMainPanel.isGameSelected()) {
                  recentlyAddedMainPanel.gainFocus();
                }
              }

              onPlay: function(gameId) {
                PES.play(gameId);
              }
            }
          }

          // Update games screen
          UpdateGamesScreen {
            id: updateGamesScreen
            Layout.fillWidth: true
            Layout.fillHeight: true

            Component.onCompleted: {
              scanCompleted.connect(PES.updateMainScreen);
              scanCompleted.connect(screenSaver.refresh);
            }
          }

          StackView {
            id: consoleStackView
            // Console screen
            initialItem: ConsoleScreen {
              id: consoleScreen
              Layout.fillWidth: true
              Layout.fillHeight: true

              onGameSelected: function(gameId) {
                PES.loadGameScreen(consoleStackView, consoleGameScreen, gameId);
              }

              onAddFavourite: function(gameId) {
                PES.favouriteGame(gameId, true);
              }

              onRemoveFavourite: function(gameId) {
                PES.favouriteGame(gameId, false);
              }
            }

            GameScreen {
              id: consoleGameScreen
              retroUser: retroUser
              visible: false

              onBackPressed: {
                consoleStackView.pop();
                consoleGameScreen.visible = false;
                consoleScreen.gridFocus();
              }

              onPlay: function(gameId) {
                PES.play(gameId);
              }
            }
          }

          // Settings screen
          SettingsScreen {
            id: settingsScreen
            Layout.fillWidth: true
            Layout.fillHeight: true

            onResetData: {
              backend.resetData(config, database);
            }

            onSettingsApplied: {
              backend.saveSettings({
                  bluetoothEnabled: settingsScreen.getBluetoothEnabled(),
                  dateFormat: settingsScreen.getDateFormat(),
                  hardcoreEnabled: settingsScreen.getHardcoreMode(),
                  hdmiCecEnabled: settingsScreen.getHdmiCecEnabled(),
                  timezone: settingsScreen.getTimezone()
              });
            }

            Component.onCompleted: {
              settingsScreen.setAvailableTimezones(backend.getAvailableTimezones());
              settingsScreen.setBluetoothEnabled(backend.getBluetoothEnabled());
              settingsScreen.setDateFormats(backend.getDateFormats());
              settingsScreen.setDateFormat(backend.getDateFormat());
              settingsScreen.setHardcoreMode(backend.getHardcoreMode());
              settingsScreen.setHdmiCecEnabled(backend.getHdmiCecEnabled());
              settingsScreen.setTimezone(backend.getTimezone());
            }
          }
        }
      }
    }

    ScreenSaver {
      id: screenSaver

      onClose: {
        screenSaverTimer.restart();
        mainStackView.pop();
        mainWindowInternal.restoreFocusItem.forceActiveFocus();
      }
    }
  }
}
