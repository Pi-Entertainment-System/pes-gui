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

function getConsolesWithGames() {
  return backend.getConsoles(true);
}

function mainMenuEvent(text) {
	switch(text) {
    default: console.error(text);
	}
}

function optionsDialogEvent(text) {
	switch(text) {
		case "Update Games": {
      optionsDialog.close();
      screenStack.currentIndex = 1;
			break;
		}
		case "Exit": {
			optionsDialog.close();
			closeDialog.open();
			break;
		}
	}
}

function updateHomeScreen() {
  if (mainMenuModel.count == 1) {
    noGamesText.visible = true;
  }
}

function updateMainMenuModel() {
  // remove existing entries
  if (mainMenuModel.count > 1) {
    for (var i = mainMenuModel.count - 1; i > 1; i--) {
      mainMenuModel.remove(i);
    }
  }
  var consoles = getConsolesWithGames();
  for (var i = 0; i < consoles.length; i++) {
    mainMenuModel.append(consoles[i]);
  }
}
