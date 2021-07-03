/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2021 Neil Munday (neil@mundayweb.com)

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

Dialog {
  id: dialog
  modal: true
  width: 500
  height: 150
  x: (parent.width - width) / 2
  y: (parent.height - height) / 2

  // custom signals
  signal noButtonPressed()
  signal yesButtonPressed()

  // additional properties
  property alias text: promptTxt.text
  property QtObject navSound: null

  background: Rectangle {
    color: Colour.dialogBg
    anchors.fill: parent
    border.color: Colour.line
  }

  ColumnLayout {
    anchors.fill: parent
    spacing: 10
    Text {
      id: promptTxt
      color: Colour.text
      font.pixelSize: FontStyle.dialogSize
      text: "Prompt"
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

        Keys.onRightPressed: {
          if (dialog.navSound) {
            dialog.navSound.play();
          }
          event.accepted = true;
          exitNoBtn.forceActiveFocus();
        }

        Keys.onReturnPressed: {
          dialog.yesButtonPressed();
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

        Keys.onLeftPressed: {
          if (dialog.navSound) {
            dialog.navSound.play();
          }
          event.accepted = true;
          exitYesBtn.forceActiveFocus();
        }

        Keys.onReturnPressed: {
          dialog.close();
          dialog.noButtonPressed();
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
