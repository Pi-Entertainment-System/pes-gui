#
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020 Neil Munday (neil@mundayweb.com)
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
import pes

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Date, ForeignKey, Integer, String
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
	def getJson(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Console(Base, CustomBase):
	__tablename__ = "console"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	gamesDbId = Column(Integer, ForeignKey('gamesdb_platform.id')) # FBA and MAMA use the same ID
	retroId = Column(Integer, ForeignKey('retroachievement_console.id')) # Mega Drive & Gensis use same ID

	platform = relationship("GamesDbPlatform", back_populates="consoles")
	retroAchievementConsole = relationship("RetroAchievementConsole", back_populates="consoles")

	def __repr__(self):
		return "<Console id=%s name=%s retroId=%s>" % (self.id, self.name, self.retroId)

class Game(Base, CustomBase):
	__tablename__ = "game"

	id = Column(Integer, primary_key=True)
	consoleId = Column(Integer, ForeignKey('console.id'))
	rasum = Column(String)
	gamesDbId = Column(Integer, index=True)
	retroId = Column(Integer, ForeignKey('retroachievement_game.id'), index=True)
	path = Column(String)

	console = relationship("Console", back_populates="games")

class GamesDbGame(Base, CustomBase):
	__tablename__ = "gamesdb_game"

	id = Column(Integer, primary_key=True)
	platformId = Column(Integer, ForeignKey('gamesdb_platform.id'))
	name = Column(String)
	releaseDate = Column(String)
	overview = Column(String)
	boxArtFrontOriginal = Column(String)
	boxArtFrontMedium = Column(String)
	boxArtFrontLarge = Column(String)

	platform = relationship("GamesDbPlatform", back_populates="games")

	def __repr__(self):
		return "<GamesDbGame id=%d platformId=%d name=\"%s\" releaseDate=%s>" % (self.id, self.platformId, self.name, self.releaseDate)

class GamesDbPlatform(Base, CustomBase):
	__tablename__ = "gamesdb_platform"

	id = Column(Integer, primary_key=True)
	name = Column(String)

	def __repr__(self):
		return "<GamesDbPlatform id=%d name=%s>" % (self.id, self.name)

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
	rasum = Column(String, index=True)
	name = Column(String)
	retroConsoleId = Column(Integer, ForeignKey('retroachievement_console.id'))

	console = relationship("RetroAchievementConsole", back_populates="games")

	def __repr__(self):
		return "<RetroAchievementGame id=%d rasum=%s name=%s retroConsoleId=%d>" % (self.id , self.rasum, self.name, self.retroConsoleId)

Console.games = relationship("Game", order_by=Game.id, back_populates="console")
Console.retroAchievementConsoles = relationship("RetroAchievementConsole", order_by=RetroAchievementConsole.id, back_populates="console")
GamesDbPlatform.consoles = relationship("Console", order_by=Console.id, back_populates="platform")
GamesDbPlatform.games = relationship("GamesDbGame", order_by=GamesDbGame.id, back_populates="platform")
RetroAchievementConsole.consoles = relationship("Console", order_by=Console.id, back_populates="retroAchievementConsole")
RetroAchievementConsole.games = relationship("RetroAchievementGame", order_by=RetroAchievementGame.id, back_populates="console")
