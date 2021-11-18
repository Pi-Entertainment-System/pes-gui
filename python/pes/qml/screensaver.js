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

var consoles = null;

function change() {
    // pick random consoleId
    if (!consoles) {
        consoles = PES.getConsolesWithGames(true);
    }
    const consoleId = getRandomElement(consoles).id;
    const games = PES.getGames(consoleId, true);
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

function getRandomElement(x) {
    return x[Math.floor(Math.random() * x.length)];
}