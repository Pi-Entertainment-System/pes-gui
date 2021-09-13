/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2020-2021 Neil Munday (neil@mundayweb.com)

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

var allConsoles = null;
var consoleArtCache = {};
var recentlyAddedCovertArtCache = {};
var recentlyPlayedCovertArtCache = {};
var currentConsoleId = null;
var gamesAdded = false;

function getConsoleArt(consoleId) {
  var img = "";
  if (consoleId in consoleArtCache) {
    img = consoleArtCache[consoleId];
  }
  else {
    var rslt = backend.getConsoleArt(consoleId);
    if (rslt) {
      consoleArtCache[consoleId] = rslt;
      img = rslt;
    }
  }
  return img;
}

function getConsolesWithGames() {
  return backend.getConsoles(true);
}

function getCurrentConsole() {
  return allConsoles[currentConsoleId];
}

function getGames(consoleId) {
  return backend.getGames(consoleId);
}

function getRecentlyAddedGames(consoleId, useCache) {
  if (!useCache || !(consoleId in recentlyAddedCovertArtCache)) {
    recentlyAddedCovertArtCache[consoleId] = backend.getRecentlyAddedGames(consoleId, 10);
  }
  return recentlyAddedCovertArtCache[consoleId];
}

function getRecentlyPlayedGames(consoleId, useCache) {
  if (!useCache || !(consoleId in recentlyPlayedCovertArtCache)) {
    recentlyPlayedCovertArtCache[consoleId] = backend.getRecentlyPlayedGames(consoleId, 10);
  }
  return recentlyPlayedCovertArtCache[consoleId];
}

function goHome() {
  screenStack.currentIndex = 0;
  mainMenuScrollView.forceActiveFocus();
}

function loadConsoleScreen(console) {
  consoleScreen.consoleId = console.id;
  consoleScreen.headerText = console.name;
  consoleScreen.background = PES.getConsoleArt(console.id);
  consoleScreen.menuIndex = 0;
  consoleScreen.refresh();
  screenStack.currentIndex = 2;
  consoleScreen.forceActiveFocus();
}

function loadGameScreen(stackView, screen, gameId) {
  var game = backend.getGame(gameId);
  if (game) {
    screen.headerText = game.name;
    screen.coverartSrc = "file://" + game.coverart;
    screen.visible = true;
    stackView.push(screen);
  }
  else {
    console.error("Could not load game ID " + gameId);
  }
}

function mainMenuEvent() {
  // if a console is selected, then load the console screen
  var i = mainMenuModel.get(mainMenuView.currentIndex);
  if (i.id) {
    PES.loadConsoleScreen(PES.allConsoles[i.id]);
  }
}

function optionsDialogEvent(text) {
	switch(text) {
		case "Update Games": {
      optionsDialog.close();
      screenStack.currentIndex = 1;
      updateGamesScreen.reset();
			break;
		}
	}
}

function powerDialogEvent(text) {
	switch(text) {
		case "Exit": {
			powerDialog.close();
			closeDialog.open();
			break;
		}
    case "Reboot": {
      rebootDialog.open();
      break;
    }
    case "Power Off": {
      poweroffDialog.open();
      break;
    }
	}
}

function setCoverartPanelFocus() {
  if (gamesAdded) {
    if (recentlyPlayedMainPanel.visible) {
      recentlyPlayedMainPanel.forceActiveFocus();
    }
    else {
      recentlyAddedMainPanel.forceActiveFocus();
    }
  }
}

function updateCoverartPanels(consoleId) {
  currentConsoleId = consoleId;
  recentlyAddedMainPanel.removeAll();
  recentlyPlayedMainPanel.removeAll();

  var games = getRecentlyAddedGames(consoleId, true);
  if (games.length == 0) {
    recentlyAddedMainPanel.visible = false;
  }
  else {
    for (var i = 0; i < games.length; i++) {
      recentlyAddedMainPanel.addGame(games[i]);
    }
    recentlyAddedMainPanel.visible = true;
  }

  games = getRecentlyPlayedGames(consoleId, true);
  if (games.length == 0) {
    recentlyPlayedMainPanel.visible = false;
  }
  else {
    for (var i = 0; i < games.length; i++) {
      recentlyPlayedMainPanel.addGame(games[i]);
    }
    recentlyPlayedMainPanel.visible = true;
  }

  if (consoleId > 0){
    mainBackgroundImg.source = getConsoleArt(consoleId);
    exploreBtn.visible = true;
  }
  else {
    mainBackgroundImg.source = "";
    exploreBtn.visible =  false;
  }
}

function updateHomeScreen() {
  if (!gamesAdded) {
    mainText.text = "You have not added any games to PES yet. To do so press the Home button and select 'Update Games' option.";
    mainText.visible = true;
  }
  else {
    //mainText.text = "Time to go gaming!";
    mainText.visible = false;
  }
  mainMenuView.forceActiveFocus();
  mainMenuView.soundOn = true;
}

function updateMainScreen(){
  if (allConsoles == null) {
    allConsoles = {};
    var consoles = backend.getConsoles(false);
    for (var i = 0; i < consoles.length; i++) {
      allConsoles[consoles[i].id] = consoles[i];
    }
  }
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

  gamesAdded = consoles.length > 0;

  // purge recently added covert art cache
  recentlyAddedCovertArtCache = {};

  updateCoverartPanels(0);

  updateHomeScreen();
}
