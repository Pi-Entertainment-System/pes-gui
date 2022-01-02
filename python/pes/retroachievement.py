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

import logging
import pes
import pes.common
import os
import requests
import sqlalchemy
import sqlalchemy.orm

from datetime import datetime
from PyQt5.QtCore import QThread, QVariant, pyqtSignal, pyqtSlot, pyqtProperty, QObject

URL_TIMEOUT = 30
RETRO_URL = "https://www.retroachievements.org/dorequest.php"
RETRO_BADGE_URL = "http://i.retroachievements.org/Badge"
HEADERS = { "accept": "application/json", 'User-Agent': 'PES Scraper'}

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def getGameHashes(consoleId):
	logging.debug("retroachievement.getGameHashes: consoleId = %d" % consoleId)
	response = requests.get(RETRO_URL, params={ "r": "hashlibrary", "c": consoleId }, timeout=URL_TIMEOUT)
	if not response.status_code == requests.codes.ok:
		logging.error("retroachievement.getGameHashes: could not download game hashes, response code - %s" % response.status_code)
		return None
	hashData = response.json()
	if not hashData['Success']:
		logging.error("retroachievement.getGameHashes: failed to download hashes")
		return None
	games = {}
	# games can have multiple hashes!
	for hash, gameId in hashData['MD5List'].items():
		gameId = int(gameId)
		if gameId in games.keys():
			games[gameId]['hashes'].append(hash)
		else:
			games[gameId] = { 'hashes': [hash] }
	response = requests.get(RETRO_URL, params={ "r": "gameslist", "c": consoleId }, timeout=URL_TIMEOUT)
	if not response.status_code == requests.codes.ok:
		logging.error("retroachievement.getGameHashes: could not download game list, response code - %s" % response.status_code)
		return None
	gameData = response.json()
	if not gameData['Success']:
		logging.error("retroachievement.getGameHashes: failed to download game list data")
		return None
	for gameId, title in gameData['Response'].items():
		gameId = int(gameId)
		if gameId in games.keys():
			games[gameId]['name'] = title.strip()
	return games

def getRasum(path, retroAchievementId):
	if not os.path.exists(path):
		raise FileNotFoundError("getRasum: %s does not exist" % path)
	if not os.path.isfile(path):
		raise ValueError("getRasum: %s is not a file" % path)
	if retroAchievementId == None:
		raise ValueError("getRasum: retroAchievementId is None")
	command = "rasum -i %d \"%s\"" % (int(retroAchievementId), path)
	rtn, stdout, stderr = pes.common.runCommand(command)
	if rtn != 0:
		raise Exception("Failed to run '%s'\nstdout: %s\nstderr: %s" % (command, stdout, stderr))
	return stdout.replace("\n", "")

def getRetroAchievementId(rasum):
	try:
		response = requests.get(RETRO_URL, params={"r": "gameid", "m": rasum}, timeout=URL_TIMEOUT)
		if response.status_code != requests.codes.ok:
			return None
		data = response.json()
		if "Success" not in data:
			logging.error("retroachievement.getRetroAchievementId: could not find \"Success\" in JSON")
			return None
		if not data["Success"]:
			logging.error("retroachievement.getRetroAchievementId: could not get ID for hash \"%s\"" % rasum)
			return None
		return data["GameID"]
	except Exception as e:
		logging.error("retroachievement.getRetroAchievementId: could not get ID for hash \"%s\"" % rasum)
		logging.error(e)
	return None

class RetroAchievementException(Exception):

	def __init__(self, msg):
		Exception.__init__(self, msg)

class RetroAchievementUser(QObject):

	__URL = 'http://retroachievements.org/API/'

	loginSignal = pyqtSignal()
	scoreChanged = pyqtSignal()

	def __init__(self, username=None, password=None, apikey=None):
		super(RetroAchievementUser, self).__init__()
		if username == None:
			# load from user settings file
			userSettings = pes.common.UserSettings()
			username = userSettings.get("RetroAchievements", "username")
			password = userSettings.get("RetroAchievements", "password")
			apikey = userSettings.get("RetroAchievements", "apiKey")
			if username and password:
				logging.debug("RetroAchievementUser.__init__: using username and password from %s" % pes.userPesConfigFile)
			if apikey:
				logging.debug("RetroAchievementUser.__init__: api key: %s" % apikey)
				self.__apikey = apikey
		logging.debug("RetroAchievementUser.__init__: user = %s" % username)
		self.__username = username
		self.__password = password
		self.__apikey = apikey
		self.__token = None
		self.__score = 0
		self.__retroAchievementUserRecord = None
		self.__rank = 0
		self.__totalPoints = 0
		self.__totalTruePoints = 0

	def __doRequest(self, apiUrl, parameters=None):
		params = {'z' : self.__username, 'y': self.__apikey }
		if parameters:
			for k, v in parameters.items():
				params[k] = v
		url = "%s/%s" % (RetroAchievementUser.__URL, apiUrl)
		logging.debug("RetroachievementUser.__doRequest: loading URL %s with %s" % (url, params))
		response = requests.get(
			url,
			params=params,
			timeout=URL_TIMEOUT
		)
		if response.status_code == requests.codes.ok:
			if response.text == 'Invalid API Key':
				raise RetroAchievementException("Invalid RetroAchievement API key")
			logging.debug("RetroAchievementUser.__doRequest: loaded ok")
			return response.json()
		raise RetroAchievementException("Failed to load URL %s with %s" % (url, params))

	def getGameInfoAndProgress(self, gameId):
		return self.getGameInfoAndUserProgress(self.__username, gameId)

	def getGameInfoAndUserProgress(self, user, gameId):
		logging.debug("RetroAchievementUser.getGameInfoAndUserProgress: user = %s, gameId = %d" % (user, gameId))
		return self.__doRequest('API_GetGameInfoAndUserProgress.php', {'u': user, 'g': gameId})

	def getUserSummary(self, user=None, recentGames=0):
		if user == None:
			user = self.__username
		logging.debug("RetroAchievementUser.getUserSummary: getting user %s and games %s" % (user, recentGames))
		return self.__doRequest('API_GetUserSummary.php', {'u': user, 'g': recentGames, 'a': 5})

	@pyqtSlot(result=bool)
	def hasApiKey(self):
		return self.__apikey != None

	def hasEarnedBadge(self, badgeId):
		# has the user earned this badge?
		self.login()
		return self.__retroAchievementUserRecord.hasEarnedBadge(badgeId)

	def hasEarnedHardcoreBadge(self, badgeId):
		# has the user earned this hardcore badge?
		self.login()
		return self.__retroAchievementUserRecord.hasEarnedHardcoreBadge(badgeId)

	@pyqtProperty(bool, notify=loginSignal)
	def loggedIn(self):
		return self.__token != None

	@pyqtSlot()
	def login(self):
		if self.__username == None or self.__password == None:
			logging.warning("RetroAchievementUser.login: no username or password, not logging in")
			return
		try:
			response = requests.get(RETRO_URL, params={ "r": "login", "u": self.__username, "p": self.__password }, timeout=URL_TIMEOUT)
			if response.status_code == requests.codes.ok:
				data = response.json()
				if "Success" in data:
					if data["Success"]:
						logging.debug("RetroAchievementUser.login: data dump: %s" % data)
						if "Token" in data:
							self.__token = data["Token"]
							# score == total_points
							self.__score = int(data["Score"])
							logging.info("RetroAchievementUser.login: %s (%d)" % (self.__username, self.__score))
							logging.debug("RetroAchievementUser.login: token: %s" % self.__token)
							# next two items do not appear to be in the returned JSON since 18/12/2021 :-S
							#self.__totalPoints = int(data["TotalPoints"])
							#self.__totalTruePoints = int(data["TotalTruePoints"])
							self.loginSignal.emit()
							self.scoreChanged.emit()
							return True
						else:
							logging.error("RetroAchievementUser.login: could not log in - token not in response")
					elif "Error" in data:
						logging.error("RetroAchievementUser.login: could not log in - %s" % data["Error"])
					else:
						logging.error("RetroAchievementUser.login: could not log in")
			else:
				logging.error("RetroAchievementUser.login: could not log in, response code - %s" % response.status_code)
		except Exception as e:
			logging.error("RetroAchievementUser.login: could not log in")
			logging.error(e)
		return False

	@pyqtProperty(str)
	def password(self):
		return self.__password

	@pyqtProperty(int)
	def rank(self):
		return self.__rank

	@pyqtProperty(int, notify=scoreChanged)
	def score(self):
		return self.__score

	@pyqtProperty(int)
	def totalPoints(self):
		return self.__totalPoints

	@pyqtProperty(int)
	def totalTruePoints(self):
		return self.__totalTruePoints

	@pyqtProperty(str, constant=True)
	def username(self):
		return self.__username

class RetroAchievementThread(QThread):

	# cache of game IDs we have already looked up
	__gameIdCache = []
	# signals
	progressSignal = pyqtSignal(float, arguments=["progress"])

	def __init__(self, parent=None):
		super(RetroAchievementThread, self).__init__(parent)
		logging.debug("RetroAchievementThred.__init__: created")
		self.__gameId = None
		self.__retroGameId = None
		self.__retroGame = None
		self.__badges = []
		self.__retroUser = None
		self.__progress = 0.0

	@pyqtProperty(int)
	def gameId(self):
		return self.__gameId

	@gameId.setter
	def gameId(self, id):
		self.__gameId = id

	@pyqtSlot(result=list)
	def getBadges(self):
		return self.__badges

	@pyqtSlot(result=QVariant)
	def getRetroGame(self):
		return self.__retroGame.getDict()

	@pyqtProperty(int)
	def progress(self):
		return self.__progress

	@pyqtProperty(int)
	def retroGameId(self):
		return self.__retroGameId

	@retroGameId.setter
	def retroGameId(self, id):
		self.__retroGameId = id

	def run(self):
		# note: QThread will emit finished signal for us
		self.__badges = []
		self.__progress = 0.0
		logging.debug("RetroAchievementThread.run: started for RetroAchievement game: %d" % self.__gameId)
		engine = pes.sql.connect()
		session = sqlalchemy.orm.sessionmaker(bind=engine)()
		self.__retroGame = session.query(pes.sql.RetroAchievementGame).get(self.__retroGameId)
		if not self.__retroGame:
			logging.error("RetroAchievementThread.run: could not find RetroAchievementGame with id: %d" % self.__retroGameId)
			return
		game = session.query(pes.sql.Game).get(self.__gameId)
		if not game:
			logging.error("RetroAchievementThread.run: could not find Game with id: %d" % game.id)
			return
		# create badge dir (if needed)
		badgeDir = os.path.join(pes.userBadgeDir, str(self.__retroGameId))
		pes.common.mkdir(badgeDir)
		if self.__retroGameId in RetroAchievementThread.__gameIdCache:
			logging.debug("RetroAchievementThread.run: game ID cached")
		elif len(self.__retroGame.badges) == 0 or (game.lastPlayed and self.__retroGame.syncDate < game.lastPlayed) or not game.lastPlayed:
			logging.debug("RetroAchievementThread.run: loading live data from the Internet")
			score = 0
			maxScore = 0
			rslt = self.__retroUser.getGameInfoAndProgress(self.__retroGameId)
			if 'Achievements' in rslt and len(rslt['Achievements']) > 0:
				count = 0
				total = len(rslt['Achievements'])
				for id, data in rslt['Achievements'].items():
					id = int(id)
					badge = session.query(pes.sql.RetroAchievementBadge).get(id)
					if badge:
						badge.title = data["Title"]
						badge.description = data["Description"]
						badge.points = int(data["Points"])
					else:
						badge = pes.sql.RetroAchievementBadge(
							id=id,
							name=data["BadgeName"],
							retroGameId=self.__retroGameId,
							title=data["Title"],
							description=data["Description"],
							points=int(data["Points"]),
							lockedPath=os.path.join(badgeDir, "%s_lock.png" % data["BadgeName"]),
							unlockedPath=os.path.join(badgeDir, "%s.png" % data["BadgeName"]),
							displayOrder=int(data["DisplayOrder"]),
							totalAwarded=int(data["NumAwarded"]),
							totalAwardedHardcore=int(data["NumAwardedHardcore"])
						)
					maxScore += badge.points
					if "DateEarned" in data:
						badge.earned = datetime.strptime(data["DateEarned"], "%Y-%m-%d %H:%M:%S")
					if "DateEarnedHardcore" in data:
						badge.earned = datetime.strptime(data["DateEarnedHardcore"], "%Y-%m-%d %H:%M:%S")
					if "DateEarned" in data or "DateEarnedHardcore" in data:
						score += badge.points
					self.__saveBadge(badge)
					session.add(badge)
					count += 1
					self.__progress = float(count) /float(total)
					self.progressSignal.emit(self.__progress)
				self.__retroGame.score = score
				self.__retroGame.maxScore = maxScore
				self.__retroGame.totalPlayers = int(rslt["NumDistinctPlayersCasual"])
				self.__retroGame.totalPlayersHardcore = int(rslt["NumDistinctPlayersHardcore"])
				self.__retroGame.syncDate = datetime.now()
				session.add(self.__retroGame)
				session.commit()
			else:
				logging.deug("RetroAchievementThread.run: no achievements found for %d" % self.__retroGameId)
				self.__progress = 100
				return
		badges = session.query(pes.sql.RetroAchievementBadge).filter(pes.sql.RetroAchievementBadge.retroGameId == self.__retroGameId).order_by(pes.sql.RetroAchievementBadge.displayOrder)
		if badges:
			for badge in badges:
				self.__saveBadge(badge)
				self.__badges.append(badge.getDict())
		RetroAchievementThread.__gameIdCache.append(self.__retroGameId)
		self.__progress = 100

	@staticmethod
	def __saveBadge(badge):
		tasks = [
			{"url": "%s/%s_lock.png" % (RETRO_BADGE_URL, badge.name), "path": badge.lockedPath},
			{"url": "%s/%s.png" % (RETRO_BADGE_URL, badge.name), "path": badge.unlockedPath}
		]
		for t in tasks:
			if not os.path.exists(t["path"]):
				logging.debug("RetroAchievementThread.__saveBadge: saving %s to %s" % (t["url"], t["path"]))
				response = requests.get(t["url"], headers=HEADERS, timeout=URL_TIMEOUT)
				if response.status_code == requests.codes.ok:
					with open(t["path"], "wb") as f:
						f.write(response.content)
				else:
					logging.warning("RetroAchievementThread.__saveBadge: unable to download %s" % t["url"])

	@pyqtProperty(RetroAchievementUser)
	def user(self):
		return self.__retroUser

	@user.setter
	def user(self, user):
		self.__retroUser = user
