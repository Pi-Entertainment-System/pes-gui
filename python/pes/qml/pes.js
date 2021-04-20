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

function getConsolesWithGames() {
  return backend.getConsoles(true);
}

function goHome() {
  screenStack.currentIndex = 0;
  mainMenuScrollView.forceActiveFocus();
}

function getRecentlyAddedGames(consoleId) {
  return backend.getRecentlyAddedGames(consoleId, 10)
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
      beginScanLayout.visible = true;
      beginFullScanLayout.visible = true;
      beginScanBtn.forceActiveFocus();
      beginScanTxt.visible = true;
      abortScanBtn.visible = false;
      updateRomsProgressBar.visible = false;
      statusTxt.visible = false;
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
    mainText.text = "You have not added any games to PES yet. To do so press the Home button and select 'Update Games' option.";
  }
  else {
    mainText.text = "Time to go gaming!";
  }
  mainText.visible = true;
  mainMenuView.forceActiveFocus();
  mainMenuView.soundOn = true;
}

function updateMainScreen(){
  // main menu model
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
  
  var games = getRecentlyAddedGames(0);
  if (games.length == 0) {
    recentlyAddedMainPanel.visible = false;
  }
  else {
    for (var i = 0; i < games.length; i++) {
      recentlyAddedMainPanel.addGame(games[i]);
    }
    recentlyAddedMainPanel.visible = true;
  }

  updateHomeScreen();
}

