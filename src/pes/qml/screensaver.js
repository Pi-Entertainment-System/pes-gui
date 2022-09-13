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

var games = [];

/**
 * Create a cache of games.
 */
function init(useCache) {
    if (!useCache) {
      games = [];
    }
    if (games.length == 0) {
        const consoles = PES.getConsolesWithGames(useCache);
        for (var i = 0; i < consoles.length; i++) {
            games.push.apply(games, PES.getGames(consoles[i].id, true));
        }
    }
}

/**
 * Called by timer in ScreenSaver component.
 *
 */
function change() {
    if (games.length == 0) {
        return;
    }
    const game = getRandomElement(games);
    var images = [game.coverartFront];
    if (game.coverartBack && game.coverartBack != "") {
        images.push(game.coverartBack);
    }
    for (var i = 0; i < game.screenshots.length; i ++) {
        images.push(game.screenshots[i]);
    }
    const image = getRandomElement(images);
    if (imgStackView.currentItem == firstImg) {
        secondImg.source = "file://" + image;
        imgStackView.push(secondImg);
    }
    else {
        firstImg.source = "file://" + image;
        imgStackView.pop();
    }
}

/**
 * Get a random elment from the given array.
 *
 * @returns a random element from the given array
 */
function getRandomElement(x) {
    return x[Math.floor(Math.random() * x.length)];
}

/**
 * Refresh the game cache, e.g. after a ROM scan.
 */
function refresh() {
    games = [];
    init(false);
}
