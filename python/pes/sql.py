#
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2021 Neil Munday (neil@mundayweb.com)
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

import logging
import os
import pes

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

Base = declarative_base()

def connect(db=pes.userDb):
	# disable check_same_thread check
	# must make sure writes only happen in one thread!
	s = "sqlite:///%s?check_same_thread=false" % db
	logging.debug("pes.sql.connect: connecting to: %s" % s)
	return create_engine(s)

def createAll(engine):
	Base.metadata.create_all(engine)

class CustomBase(object):
	def getDict(self):
		j = {}
		for c in self.__table__.columns:
			val = getattr(self, c.name)
			t = type(c.type)
			if val:
				if t is DateTime:
					j[c.name] = int(val.timestamp())
				else:
					j[c.name] = val
			else:
				if t is DateTime:
					j[c.name] = 0
				elif t is Integer:
					j[c.name] = 0
				else:
					j[c.name] = ""
		return j

class Console(Base, CustomBase):
	__tablename__ = "console"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	gamesDbId = Column(Integer, ForeignKey('gamesdb_platform.id')) # FBA and MAMA use the same ID
	retroId = Column(Integer, ForeignKey('retroachievement_console.id'), default=0) # Mega Drive & Gensis use same ID
	nocoverart = Column(String)
	art = Column(String)

	platform = relationship("GamesDbPlatform", back_populates="consoles")
	retroAchievementConsole = relationship("RetroAchievementConsole", back_populates="consoles")

	def __repr__(self):
		return "<Console id=%s name=%s retroId=%s>" % (self.id, self.name, self.retroId)

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

	def getDict(self):
		j = super().getDict()
		if self.gamesDbGame:
			j["overview"] = self.gamesDbGame.overview
			j["releaseDate"] = self.gamesDbGame.releaseDate
		else:
			j["overview"] = ""
			j["releaseDate"] = "N/A"
		if j["added"] > 0:
			j["addedStr"] = self.added.strftime("%H:%M %d/%m/%Y")
		else:
			j["addedStr"] = "Unknown"
		if j["lastPlayed"] > 0:
			j["lastPlayedStr"] = self.lastPlayed.strftime("%H:%M %d/%m/%Y")
		elif self.playCount == 0:
			j["lastPlayedStr"] = "Not played"
		else:
			j["lastPlayedStr"] = "Unknown"
		if not os.path.exists(j["coverartFront"]):
			logging.warning("%s does not exist!" % self.coverartFront)
			j["coverartFront"] = os.path.join(pes.resourcesDir, self.console.nocoverart)
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

	def __repr__(self):
		return "<GameScreenshot id=%d gameId=%d path=\"%s\">" % (self.id, self.gameId, self.path)

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

	def __repr__(self):
		return "<GamesDbGame id=%d platformId=%d name=\"%s\" releaseDate=%s retroId=%s>" % (self.id, self.platformId, self.name, self.releaseDate, self.retroId)

class GamesDbPlatform(Base, CustomBase):
	__tablename__ = "gamesdb_platform"

	id = Column(Integer, primary_key=True)
	name = Column(String)

	def __repr__(self):
		return "<GamesDbPlatform id=%d name=%s>" % (self.id, self.name)

class GamesDbScreenshot(Base, CustomBase):
	__tablename__ = "gamesdb_screenshot"
	id = Column(Integer, primary_key=True)
	gameId = Column(Integer, ForeignKey('gamesdb_game.id'), index=True)
	original = Column(Text)
	medium = Column(Text)
	large = Column(Text)

	game = relationship("GamesDbGame", back_populates="screenshots")

	def __repr__(self):
		return "<GamesDbScreenShot id=%d gameId=%d url=\"%s\">" % (self.id, self.gameId, self.url)

class MameGame(Base, CustomBase):
	__tablename__ = "mame_game"

	shortName = Column(String, primary_key=True)
	name = Column(String)

class RetroAchievementConsole(Base, CustomBase):
	__tablename__ = "retroachievement_console"
	id = Column(Integer, primary_key=True)

	console = relationship("Console", back_populates="retroAchievementConsoles")

class RetroAchievementGame(Base, CustomBase):
	__tablename__ = "retroachievement_game"
	id = Column(Integer, primary_key=True)
	name = Column(Text)
	retroConsoleId = Column(Integer, ForeignKey('retroachievement_console.id'))

	console = relationship("RetroAchievementConsole", back_populates="games")

	def __repr__(self):
		return "<RetroAchievementGame id=%d rasum=%s name=%s retroConsoleId=%d>" % (self.id, self.rasum, self.name, self.retroConsoleId)

class RetroAchievementGameHash(Base, CustomBase):
	__tablename__ = "retroachievement_game_hash"
	id = Column(Integer, ForeignKey('retroachievement_game.id'), primary_key=True)
	rasum = Column(String, primary_key=True)

	game = relationship("RetroAchievementGame", back_populates="hashes")

	def __repr__(self):
		return "<RetroAchievementGameHash id=%d rasum=%s>" % (self.id, self.rasum)		

Console.games = relationship("Game", order_by=Game.id, back_populates="console")
Console.retroAchievementConsoles = relationship("RetroAchievementConsole", order_by=RetroAchievementConsole.id, back_populates="console")
Game.screenshots = relationship("GameScreenshot", order_by=GameScreenshot.id, back_populates="game", cascade="all,delete")
GamesDbGame.games = relationship("Game", order_by=Game.id, back_populates="gamesDbGame")
GamesDbGame.screenshots = relationship("GamesDbScreenshot", order_by=GamesDbScreenshot.id, back_populates="game")
GamesDbPlatform.consoles = relationship("Console", order_by=Console.id, back_populates="platform")
GamesDbPlatform.games = relationship("GamesDbGame", order_by=GamesDbGame.id, back_populates="platform")
RetroAchievementConsole.consoles = relationship("Console", order_by=Console.id, back_populates="retroAchievementConsole")
RetroAchievementConsole.games = relationship("RetroAchievementGame", order_by=RetroAchievementGame.id, back_populates="console")
RetroAchievementGame.games = relationship("Game", order_by=Game.id, back_populates="retroAchievementGame")
RetroAchievementGame.gamesDbGame = relationship("GamesDbGame", order_by=GamesDbGame.id, back_populates="retroAchievementGame")
RetroAchievementGame.hashes = relationship("RetroAchievementGameHash", order_by=RetroAchievementGameHash.rasum, back_populates="game")
