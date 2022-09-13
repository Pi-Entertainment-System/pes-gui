#
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020-2022 Neil Munday (neil@mundayweb.com)
#
#    PES is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PES is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PES.  If not, see <http://www.gnu.org/licenses/>.
#

# pylint: disable=invalid-name,line-too-long,missing-class-docstring,missing-function-docstring

"""
Experimental PES web GUI.
"""

import logging
import os
import pes

from flask import abort, Flask, render_template, request, send_file
from PyQt5.QtCore import QThread
from waitress import serve

class WebThread(QThread):

    def __init__(self, port, backend, parent=None):
        logging.debug("WebThread.__init__: created")
        super().__init__(parent)
        if port < 1:
            raise ValueError("WebThread.__init__: port is less than 1")
        self._backend = backend
        self._port = port
        self._server = Flask(__name__, template_folder=os.path.join(pes.webDir, "templates"), static_folder=os.path.join(pes.webDir, "static"))
        self._server.add_url_rule("/", "index", self.index)
        self._server.add_url_rule("/coverart", "coverart", self.coverart, methods=["GET"])
        self._server.add_url_rule("/game", "game", self.game, methods=["GET"])
        self._server.add_url_rule("/games", "games", self.games, methods=["GET"])
        self._server.add_url_rule("/play", "play", self.play, methods=["GET"])
        self._server.add_url_rule("/power", "power", self.power, methods=["GET"])
        self._server.add_url_rule("/poweroff", "poweroff", self.poweroff, methods=["GET"])
        self._server.add_url_rule("/reboot", "reboot", self.reboot, methods=["GET"])
        self._consoles = self._backend.getConsoles(True)

    def coverart(self): # pylint: disable=inconsistent-return-statements
        gameId = self._getGameId()
        game = self._backend.getGame(gameId)
        if game:
            return send_file(game["coverartFront"])
        abort(404)

    def game(self): # pylint: disable=inconsistent-return-statements
        gameId = self._getGameId()
        game = self._backend.getGame(gameId)
        if game:
            return render_template("game.html", consoleId=game["consoleId"], consoles=self._consoles, game=game)
        abort(404)

    def games(self):
        consoleId = int(request.args.get("id"))
        console = self._backend.getConsole(consoleId)
        if not console:
            abort(404)
        games = self._backend.getGames(consoleId)
        return render_template("games.html", consoleId=consoleId, console=console, consoles=self._consoles, games=games)

    @staticmethod
    def _getGameId():
        return int(request.args.get("id"))

    def index(self):
        recentlyAdded = self._backend.getRecentlyAddedGames()
        recentlyPlayed = self._backend.getRecentlyPlayedGames()
        return render_template("index.html", consoleId=0, consoles=self._consoles, recentlyAdded=recentlyAdded, recentlyPlayed=recentlyPlayed)

    def play(self):
        gameId = self._getGameId()
        result = self._backend.playGame(gameId)
        return render_template("result.json", result=result["result"], msg=result["msg"])

    def power(self):
        return render_template("power.html", consoleId=0, consoles=self._consoles)

    def poweroff(self):
        self._backend.shutdown()
        return render_template("result.json", result=True, msg="")

    def reboot(self):
        self._backend.reboot()
        return render_template("result.json", result=True, msg="")

    def run(self):
        logging.debug("WebThread.run: starting Flask app via Waitress on port %d", self._port)
        serve(self._server, host="0.0.0.0", port=self._port, _quiet=True)
