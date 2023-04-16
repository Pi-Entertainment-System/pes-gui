#
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020-2023 Neil Munday (neil@mundayweb.com)
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
This module provides classes and functions for PES' database functionality.
"""

# standard imports
from datetime import datetime
import logging
import os

# third-party imports
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import class_mapper, relationship, sessionmaker, ColumnProperty

# pes imports
import pes

Base = declarative_base()
Session = None

def connect(db=pes.userDb):
    global Session # pylint: disable=global-statement
    # disable check_same_thread check
    # must make sure writes only happen in one thread!
    s = f"sqlite:///{db}?check_same_thread=false"
    logging.debug("pes.sql.connect: connecting to: %s", s)
    engine = create_engine(s)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

class CustomBase:

    DATE_TIME_FORMAT = "%d/%m/%Y %H:%M"

    def __init__(self) -> None:
        self.__table__ = None

    @staticmethod
    def getDateStr(column: datetime) -> str:
        return column.strftime(CustomBase.DATE_TIME_FORMAT)

    def getDict(self) -> dict:
        j = {}
        if self.__table__ is not None:
            for prop in class_mapper(self.__class__).iterate_properties:
                if isinstance(prop, ColumnProperty):
                    val = getattr(self, prop.key)
                    t = type(prop.columns[0].type)
                    if val:
                        if t is DateTime:
                            j[prop.key] = int(val.timestamp())
                        else:
                            j[prop.key] = val
                    else:
                        if t is DateTime:
                            j[prop.key] = 0
                        elif t is Integer:
                            j[prop.key] = 0
                        elif t is Boolean:
                            j[prop.key] = False
                        else:
                            j[prop.key] = ""
        return j

    def __repr__(self) -> str:
        vals = []
        for prop in class_mapper(self.__class__).iterate_properties:
            if isinstance(prop, ColumnProperty):
                vals.append(f"{prop.key}={getattr(self, prop.key)}")
        return f"<{self.__class__.__name__} {' '.join(vals)} >"

class Console(Base, CustomBase):
    __tablename__ = "console"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    gamesDbId = Column(Integer, ForeignKey('gamesdb_platform.id')) # FBA and MAMA use the same ID
    retroId = Column(Integer, ForeignKey('retroachievement_console.id'), default=0) # Mega Drive & Gensis use same ID
    nocoverart = Column(String)
    art = Column(String)

    platform = relationship("GamesDbPlatform", back_populates="consoles")
    #retroAchievementConsole = relationship("RetroAchievementConsole", back_populates="consoles")

class Game(Base, CustomBase):
    __tablename__ = "game"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    consoleId = Column(Integer, ForeignKey('console.id'))
    rasum = Column(String, index=True, default=0)
    gamesDbId = Column(Integer, ForeignKey('gamesdb_game.id'), index=True, default=0)
    retroId = Column(Integer, ForeignKey('retroachievement_game.id'), index=True, default=0)
    path = Column(Text)
    coverartFront = Column(Text)
    coverartBack = Column(Text)
    lastPlayed = Column(DateTime)
    added = Column(DateTime)
    favourite = Column(Boolean, default=False)
    playCount = Column(Integer, default=0)
    fileSize = Column(Integer, default=0)
    found = Column(Boolean, default=False)

    console = relationship("Console", back_populates="games")
    gamesDbGame = relationship("GamesDbGame", back_populates="games")
    retroAchievementGame = relationship("RetroAchievementGame", back_populates="games")

    def getDict(self) -> dict:
        j = super().getDict()
        if self.gamesDbGame:
            j["overview"] = self.gamesDbGame.overview
            j["releaseDate"] = self.gamesDbGame.releaseDate
        else:
            j["overview"] = ""
            j["releaseDate"] = "N/A"
        if j["added"] > 0:
            j["addedStr"] = self.getDateStr(self.added)
        else:
            j["addedStr"] = "Unknown"
        if j["lastPlayed"] > 0:
            j["lastPlayedStr"] = self.getDateStr(self.lastPlayed)
        elif self.playCount == 0:
            j["lastPlayedStr"] = "Not played"
        else:
            j["lastPlayedStr"] = "Unknown"
        if not os.path.exists(j["coverartFront"]):
            logging.warning("%s does not exist!", self.coverartFront)
            j["coverartFront"] = os.path.join(pes.imagesDir, self.console.nocoverart)
        j["filename"] = os.path.basename(self.path)
        j["screenshots"] = []
        for screenshot in self.screenshots:
            j["screenshots"].append(screenshot.path)
        return j

class GameScreenshot(Base, CustomBase):
    __tablename__ = "game_screenshot"
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer, ForeignKey('game.id'), index=True)
    path = Column(Text)

    game = relationship("Game", back_populates="screenshots")

class GamesDbGame(Base, CustomBase):
    __tablename__ = "gamesdb_game"

    id = Column(Integer, primary_key=True)
    platformId = Column(Integer, ForeignKey('gamesdb_platform.id'), index=True)
    retroId = Column(Integer, ForeignKey('retroachievement_game.id'), index=True)
    name = Column(Text)
    releaseDate = Column(String)
    overview = Column(Text)
    boxArtBackOriginal = Column(Text)
    boxArtBackMedium = Column(Text)
    boxArtBackLarge = Column(Text)
    boxArtFrontOriginal = Column(Text)
    boxArtFrontMedium = Column(Text)
    boxArtFrontLarge = Column(Text)

    platform = relationship("GamesDbPlatform", back_populates="games")
    retroAchievementGame = relationship("RetroAchievementGame", back_populates="gamesDbGame")

class GamesDbPlatform(Base, CustomBase):
    __tablename__ = "gamesdb_platform"

    id = Column(Integer, primary_key=True)
    name = Column(String)

class GamesDbScreenshot(Base, CustomBase):
    __tablename__ = "gamesdb_screenshot"
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer, ForeignKey('gamesdb_game.id'), index=True)
    original = Column(Text)
    medium = Column(Text)
    large = Column(Text)

    game = relationship("GamesDbGame", back_populates="screenshots")

class MameGame(Base, CustomBase):
    __tablename__ = "mame_game"

    shortName = Column(String, primary_key=True)
    name = Column(String)

class RetroAchievementBadge(Base, CustomBase):
    __tablename__ = "retroachievement_badge"
    id = Column(Integer, primary_key=True)
    retroGameId = Column(Integer, ForeignKey("retroachievement_game.id"))
    name = Column(Text)
    title = Column(Text)
    description = Column(Text)
    points = Column(Integer)
    lockedPath = Column(Text, default="")
    unlockedPath = Column(Text, default="")
    earned = Column(DateTime)
    earnedHardcore = Column(DateTime)
    displayOrder = Column(Integer)
    totalAwarded = Column(Integer, default=0)
    totalAwardedHardcore = Column(Integer, default=0)

    game = relationship("RetroAchievementGame", back_populates="badges")

    def getDict(self) -> dict:
        j = super().getDict()
        if j["earned"] > 0:
            j["earnedStr"] = self.getDateStr(self.earned)
        else:
            j["earnedStr"] = ""
        if j["earnedHardcore"]:
            j["earnedHardcoreStr"] = self.getDateStr(self.earnedHardcore)
        else:
            j["earnedHardcoreStr"] = ""
        return j

class RetroAchievementConsole(Base, CustomBase):
    __tablename__ = "retroachievement_console"
    id = Column(Integer, primary_key=True)

    console = relationship("Console", back_populates="retroAchievementConsoles")

class RetroAchievementGame(Base, CustomBase):
    __tablename__ = "retroachievement_game"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    retroConsoleId = Column(Integer, ForeignKey('retroachievement_console.id'))
    score = Column(Integer, default=0)
    maxScore = Column(Integer, default=0)
    totalPlayers = Column(Integer, default=0)
    totalPlayersHardcore = Column(Integer, default=0)
    syncDate = Column(DateTime)

    console = relationship("RetroAchievementConsole", back_populates="games")

class RetroAchievementGameHash(Base, CustomBase):
    __tablename__ = "retroachievement_game_hash"
    id = Column(Integer, ForeignKey('retroachievement_game.id'), primary_key=True)
    rasum = Column(String, primary_key=True)

    game = relationship("RetroAchievementGame", back_populates="hashes")

Console.games = relationship("Game", order_by=Game.id, back_populates="console")
Console.retroAchievementConsoles = relationship("RetroAchievementConsole", order_by=RetroAchievementConsole.id, back_populates="console")
Game.screenshots = relationship("GameScreenshot", order_by=GameScreenshot.id, back_populates="game", cascade="all,delete")
GamesDbGame.games = relationship("Game", order_by=Game.id, back_populates="gamesDbGame")
GamesDbGame.screenshots = relationship("GamesDbScreenshot", order_by=GamesDbScreenshot.id, back_populates="game")
GamesDbPlatform.consoles = relationship("Console", order_by=Console.id, back_populates="platform")
GamesDbPlatform.games = relationship("GamesDbGame", order_by=GamesDbGame.id, back_populates="platform")
#RetroAchievementConsole.consoles = relationship("Console", order_by=Console.id, back_populates="retroAchievementConsole")
RetroAchievementConsole.games = relationship("RetroAchievementGame", order_by=RetroAchievementGame.id, back_populates="console")
RetroAchievementGame.badges = relationship("RetroAchievementBadge", order_by=RetroAchievementBadge.id, back_populates="game")
RetroAchievementGame.games = relationship("Game", order_by=Game.id, back_populates="retroAchievementGame")
RetroAchievementGame.gamesDbGame = relationship("GamesDbGame", order_by=GamesDbGame.id, back_populates="retroAchievementGame")
RetroAchievementGame.hashes = relationship("RetroAchievementGameHash", order_by=RetroAchievementGameHash.rasum, back_populates="game")
