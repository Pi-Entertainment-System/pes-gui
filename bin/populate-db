#!/usr/bin/env python3

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

# pylint: disable=broad-except,invalid-name,line-too-long,missing-class-docstring,missing-function-docstring,redefined-outer-name,too-many-locals,unexpected-keyword-arg

# Note: disabled unexpected-keyword-arg due to false positives, ref: https://github.com/PyCQA/pylint/issues/6550

"""
This script initialises the PES database with console and game
data for use by PES.

By creating a cache of game data this aids adding user games to
the database.
"""

import argparse
import datetime
import json
import logging
import os
import requests

import pes
import pes.retroachievement
import pes.sql

from pes.common import checkDir, checkFile, mkdir, pesExit
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

def getGamesDbImages(cacheDir):
    result = session.query(pes.sql.GamesDbGame).all()
    if not result:
        logging.warning("found no GamesDbGames!")
        return
    gameIds = []

    imageDir = os.path.join(cacheDir, "images")
    mkdir(imageDir)

    requestNumber = 1
    for game in result:
        gameIds.append(game.id)
        # get 400 ids at a time
        if len(gameIds) == 400:
            getGamesDbImageJson(gameIds, imageDir, requestNumber)
            gameIds = []
            requestNumber += 1
    if len(gameIds) > 0:
        getGamesDbImageJson(gameIds, imageDir, requestNumber)

def getGamesDbImageJson(ids, imageDir, requestNumber):
    page = 1

    while True:
        logging.info("downloading page %d from results", page)
        params = {
            'apikey': '%s' % args.tgdbKey,
            'games_id': ','.join(str(i) for i in ids),
            'filter': 'boxart,screenshot',
            'page': page
        }

        response = requests.get(
            "%s/Games/Images" % GAMESDB_API_URL,
            params=params,
            headers=HEADERS,
            timeout=URL_TIMEOUT,
            stream=True
        )
        if response.status_code == requests.codes.ok: # pylint: disable=no-member
            data = response.json()
            if data["status"] != "Success":
                pesExit("Got bad status value: %s" % data["status"])
            if "data" not in data or "images" not in data["data"]:
                pesExit("Invalid JSON: %s" % data)
            # save JSON to cache for parsing later (if needed to save API requests)
            jsonFileCache = os.path.join(imageDir, "images-%d_%s.json" % (requestNumber, page))
            logging.debug("saving JSON to: %s", jsonFileCache)
            with open(jsonFileCache, 'w') as f:
                json.dump(data, f)
            if data["pages"]["next"]:
                page += 1
            else:
                break
        else:
            pesExit("failed, status code: %s" % response.status_code)

def mkTGDBCacheDir():
    gamesDbCacheDir = os.path.join(cacheDir, "tgdb-%s" % datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
    logging.info("using %s for theGamesDb JSON cache", gamesDbCacheDir)
    mkdir(gamesDbCacheDir)
    return gamesDbCacheDir

def processGamesDbJson(newDb, session, data):
    for game in data["data"]["games"]:
        if game["platform"] in foundGamesDbConsoleIds:
            gamesDbGame = processGamesDbGame(newDb, session, game)
            session.add(gamesDbGame)
        session.commit()

def processGamesDbGame(newDb, session, game):
    logging.info("processing game: %s, %s", game["id"], game["game_title"])
    gameId = int(game["id"])
    gamesDbGame = None
    if not newDb:
        gamesDbGame = session.query(pes.sql.GamesDbGame).get(gameId)
    if gamesDbGame:
        logging.info("-> updating")
        gamesDbGame.name = game["game_title"]
        gamesDbGame.releaseDate = game["release_date"]
        gamesDbGame.overview = game["overview"]
    else:
        logging.info("-> adding")
        gamesDbGame = pes.sql.GamesDbGame(id=gameId, platformId=game["platform"], name=game["game_title"], releaseDate=game["release_date"], overview=game["overview"])

    # get coverart
    if str(gameId) in data["include"]["boxart"]["data"]:
        for image in data["include"]["boxart"]["data"][str(gameId)]:
            if image["side"] == "front":
                logging.info("-> setting cover art URLs...")
                gamesDbGame.boxArtFrontOriginal = "%s%s" % (data["include"]["boxart"]["base_url"]["original"], image["filename"])
                gamesDbGame.boxArtFrontLarge = "%s%s" % (data["include"]["boxart"]["base_url"]["large"], image["filename"])
                gamesDbGame.boxArtFrontMedium = "%s%s" % (data["include"]["boxart"]["base_url"]["medium"], image["filename"])
                break
    else:
        logging.warning("-> no cover art for game %s", game["id"])
    return gamesDbGame

def processGamesDbImageJson(newDb, session, cacheDir):
    logging.info("processing GamesDB image JSON files")
    jsonDir = os.path.join(cacheDir, "images")
    checkDir(jsonDir)
    logging.debug("using JSON files from: %s", cacheDir)
    if not newDb:
        # remove existing sceen shots
        session.query(pes.sql.GamesDbScreenshot).delete()
    requestNumber = 1
    page = 1
    newRequest = False
    while True:
        jsonPath = os.path.join(jsonDir, "images-%d_%d.json" % (requestNumber, page))
        if os.path.exists(jsonPath) and os.path.isfile(jsonPath):
            logging.debug("processing: %s", jsonPath)
            newRequest = False
            with open(jsonPath, 'r') as f:
                try:
                    data = json.load(f)["data"]
                except Exception as e:
                    pesExit("Failed to load JSON from %s due to:\n%s" % (jsonPath, e))
                for gameId, images in data["images"].items():
                    # look up game
                    gameId = int(gameId)
                    gamesDbGame = session.query(pes.sql.GamesDbGame).get(gameId)
                    if not gamesDbGame:
                        pesExit("Could not find GamesDbGame with id: %d" % gameId)
                    logging.debug("processing images for: %s", gamesDbGame.name)
                    for image in images:
                        if image["type"] == "boxart" and image["side"] == "back":
                            gamesDbGame.boxArtBackOriginal = "%s%s" % (data["base_url"]["original"], image["filename"])
                            gamesDbGame.boxArtBackMedium = "%s%s" % (data["base_url"]["medium"], image["filename"])
                            gamesDbGame.boxArtBackLarge = "%s%s" % (data["base_url"]["large"], image["filename"])
                            session.add(gamesDbGame)
                        if image["type"] == "screenshot":
                            screenshot = pes.sql.GamesDbScreenshot(
                                gameId=gameId,
                                original="%s%s" % (data["base_url"]["original"], image["filename"]),
                                medium="%s%s" % (data["base_url"]["medium"], image["filename"]),
                                large="%s%s" % (data["base_url"]["large"], image["filename"])
                            )
                            session.add(screenshot)

        elif not newRequest:
            logging.debug("finished processing batch: %d", requestNumber)
            requestNumber += 1
            page = 1
            newRequest = True
        else:
            logging.debug("no more files to process")
            break
        page += 1
    session.commit()

def processRetroAchievementsJson(newDb, session, gameHashes, consoleRetroId):
    # note: a game may appear in more than one hash file
    for gameId, data in gameHashes.items():
        logging.info("processing RetroGame: %s", data["name"])
        retroGame = session.query(pes.sql.RetroAchievementGame).get(gameId)
        if retroGame:
            logging.info("-> updating")
            retroGame.name = data["name"]
        else:
            logging.info("-> adding")
            retroGame = pes.sql.RetroAchievementGame(id=gameId, name=data["name"], retroConsoleId=consoleRetroId)
        retroGameHash = None
        for h in data['hashes']:
            if not newDb:
                retroGameHash = session.query(pes.sql.RetroAchievementGameHash).get((gameId, h))
            if not retroGameHash:
                logging.info("-> adding hash: %s", h)
                retroGameHash = pes.sql.RetroAchievementGameHash(id=gameId, rasum=h)
                session.add(retroGameHash)
            else:
                logging.info("-> skipping hash: %s", h)
        session.add(retroGame)
    session.commit()

if __name__ == "__main__":

    # Neil Munday's theGamesDb API key - rate limited per IP
    defaultTGDBKey = 'd12fb5ce1f84c6cb3cec2b89861551905540c0ab564a5a21b3e06e34b2206928'

    parser = argparse.ArgumentParser(description='Script to pre-populate PES database', add_help=True)
    parser.add_argument('-v', '--verbose', help='Turn on debug messages', dest='verbose', action='store_true')
    parser.add_argument('-d', '--data-dir', dest='dataDir', help='Path to data directory', required=True)
    parser.add_argument('-g', '--tgdb-download', dest='tgdbDownload', help='Download latest theGamesDb.net database dump', action='store_true')
    parser.add_argument('-l', '--log', help='File to log messages to', type=str, dest='logfile')
    parser.add_argument('-k', '--tgdb-key', help='theGamesDb.net API key. If not specified Neil Munday\'s key will be used', type=str, dest='tgdbKey')
    parser.add_argument('-m', '--mame', help='add MAME data', dest='mame', action='store_true')
    parser.add_argument('-r', '--retroachievements', help='update RetroAchievements data', dest='retroachievements', action='store_true')
    parser.add_argument('--retroachievements-dir', help='use the given directory of JSON dumps instead of live data from retroachievements.org', dest='retroachievementsDir', type=str)
    parser.add_argument('--match', help='match up game records between game databases', dest='match', action='store_true')
    parser.add_argument('--tgdb-dir', help='use the given directory of JSON dumps instead of live data from theGamesDb.net', dest='tgdbDir', type=str)
    args = parser.parse_args()

    logLevel = logging.INFO
    if args.verbose:
        logLevel = logging.DEBUG

    if args.logfile:
        logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel, filename=args.logfile)
    else:
        logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

    if args.tgdbKey and args.tgdbDir:
        pesExit("please specify either --tgdb-key or --tdgb-dir not both")

    if args.retroachievements and args.retroachievementsDir:
        pesExit("please specify either --retroachievements or --retroachievements-dir not both")

    GAMESDB_API_URL = "https://api.thegamesdb.net/v1"
    GAMESDB_DUMP_URL = "https://cdn.thegamesdb.net/json/database-latest.json"
    HEADERS = { "accept": "application/json", 'User-Agent': 'PES Scraper'}
    URL_TIMEOUT = 30

    checkDir(args.dataDir)
    cacheDir = os.path.join(args.dataDir, 'cache')
    mkdir(cacheDir)

    pesDb = os.path.join(args.dataDir, 'pes.db')

    newDb = not os.path.exists(pesDb)
    if newDb:
        logging.info("new database: %s will be created", pesDb)
    else:
        logging.info("using existing database: %s", pesDb)

    consoleJSON = os.path.join(args.dataDir, "consoles.json")
    checkFile(consoleJSON)

    engine = pes.sql.connect(pesDb)
    session = sessionmaker(bind=engine)()
    pes.sql.createAll(engine)

    logging.info("loading console definitions from: %s", consoleJSON)
    with open(consoleJSON, 'r') as consoleJSONFile:
        consoleData = json.load(consoleJSONFile)
        foundGamesDbConsoleIds = []
        consoleRetroIds = []
        for c in consoleData["consoles"]:
            platformId = int(c["gamesDbId"])
            consoleId = int(c["id"])

            console = None
            if not newDb:
                console = session.query(pes.sql.Console).get(consoleId)
            if console:
                logging.info("updating Console: %s", c["name"])
                console.name = c["name"]
                console.gamesDbId = platformId
                console.nocoverart = c["nocoverart"]
                console.art = c["art"]
            else:
                logging.info("adding console: %s", c["name"])
                console = pes.sql.Console(id=consoleId, name=c["name"], gamesDbId=platformId, nocoverart=c["nocoverart"], art=c["art"])

            if "retroId" in c and c["retroId"] not in consoleRetroIds:
                console.retroId = int(c["retroId"])
                retroConsole = session.query(pes.sql.RetroAchievementConsole).get(console.retroId)
                if not retroConsole:
                    logging.debug("creating new RetroAchievementConsole record: %d", console.retroId)
                    retroConsole = pes.sql.RetroAchievementConsole(id=console.retroId)
                    session.add(retroConsole)

            session.add(console)

            gamesDbPlatform = session.query(pes.sql.GamesDbPlatform).get(platformId)
            if gamesDbPlatform:
                logging.info("updating GamesDbPlatform: %s", c["name"])
                gamesDbPlatform.name = c["name"]
            else:
                logging.info("adding GamesDbPlatform: %s", c["name"])
                gamesDbPlatform = pes.sql.GamesDbPlatform(id=platformId, name=c["name"])
            session.add(gamesDbPlatform)

            if not c["gamesDbId"] in foundGamesDbConsoleIds:
                foundGamesDbConsoleIds.append(c["gamesDbId"])
        session.commit()

    if args.mame:
        logging.info("processing MAME data")
        mameJSON = os.path.join(args.dataDir, "mame.json")
        checkFile(mameJSON)

        logging.info("loading MAME dictionary from: %s", mameJSON)
        with open(mameJSON, 'r') as f:
            data = json.load(f)
            for mame in data["games"]:
                logging.info("processing MAME game: %s", mame["shortname"])
                mameGame = None
                if not newDb:
                    mameGame = session.query(pes.sql.MameGame).get(mame["shortname"])
                if mameGame:
                    mameGame.name = mame["name"]
                    logging.info("-> updating")
                else:
                    logging.info("-> adding")
                    mameGame = pes.sql.MameGame(name=mame["name"], shortName=mame["shortname"])
                session.add(mameGame)
        session.commit()
        logging.info("MAME dictionary saved to database")

    if args.tgdbDownload:
        logging.info("downloading latest TGDB database dump from %s", GAMESDB_DUMP_URL)
        # create directory to store JSON cache
        gamesDbCacheDir = mkTGDBCacheDir()

        response = requests.get(
            GAMESDB_DUMP_URL,
            headers=HEADERS,
            timeout=URL_TIMEOUT,
            stream=True
        )
        if response.status_code == requests.codes.ok: # pylint: disable=no-member
            data = response.json()
            jsonDump = os.path.join(gamesDbCacheDir, 'tgdb.json')
            logging.debug("saving JSON to: %s", jsonDump)
            with open(jsonDump, 'w') as f:
                json.dump(data, f)
            processGamesDbJson(newDb, session, data)
        else:
            pesExit("failed, status code: %s" % response.status_code)

        # now we have the games, let's get the extra image JSON
        if not args.tgdbKey or args.tgdbKey == "default":
            args.tgdbKey = defaultTGDBKey
        logging.info("downloading GamesDB image JSON")
        getGamesDbImages(gamesDbCacheDir)
        processGamesDbImageJson(newDb, session, gamesDbCacheDir)

    if args.tgdbDir:
        checkDir(args.tgdbDir)
        logging.info("using theGamesDb.net JSON cache from: %s", args.tgdbDir)
        # look for json dump
        jsonPath = os.path.join(args.tgdbDir, 'tgdb.json')
        if os.path.exists(jsonPath) and os.path.isfile(jsonPath):
            logging.info("found TGDB database dump to process: %s", jsonPath)
            with open(jsonPath, 'r') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    pesExit("Failed to load JSON from %s due to:\n%s" % (jsonPath, e))
            processGamesDbJson(newDb, session, data)
            processGamesDbImageJson(newDb, session, args.tgdbDir)
        else:
            pesExit("No previous TGDB dump found in %s" % args.tgdbDir)
        #    logging.warning("no JSON database dump found, looking for platform downloads instead")
        #    for c in foundGamesDbConsoleIds:
        #        gamesDbPlatform = session.query(pes.sql.GamesDbPlatform).get(c)
        #        if not gamesDbPlatform:
        #            pesExit("could not find %s in GamesDbPlatform table")

        #        logging.info("processing: %s" % gamesDbPlatform.name)
        #        platformPath = os.path.join(args.tgdbDir, str(c))
        #        checkDir(platformPath)
        #        logging.debug("using data from dir: %s" % platformPath)
        #        page = 1
        #        while True:
        #            jsonPath = os.path.join(platformPath, 'games_%d.json' % page)
        #            if os.path.exists(jsonPath) and os.path.isfile(jsonPath):
        #                logging.debug("processing: %s" % jsonPath)
        #                with open(jsonPath, 'r') as f:
        #                    try:
        #                        data = json.load(f)
        #                    except Exception as e:
        #                        pesExit("Failed to load JSON from %s due to:\n%s" % (jsonPath, e))
        #                    processGamesDbJson(newDb, session, data)
        #            else:
        #                logging.debug("no more files to process")
        #                break
        #            page += 1
        #        processGamesDbImageJson(newDb, session, args.tgdbDir)

    #if args.tgdbKey:
    #    if args.tgdbKey == 'default':
    #        args.tgdbKey = defaultTGDBKey
    #        logging.info("using Neil Munday's TGDB API key - rate limited per IP")

    #    logging.info("accessing theGamesDb.net API")

        # create directory to store JSON cache
    #    gamesDbCacheDir = mkTGDBCacheDir()

    #    for c in foundGamesDbConsoleIds:
    #        gamesDbPlatform = session.query(pes.sql.GamesDbPlatform).get(c)
    #        if not gamesDbPlatform:
    #            pesExit("could not find %s in GamesDbPlatform table")

    #        logging.info("processing: %s" % gamesDbPlatform.name)
    #        jsonCacheDir = os.path.join(gamesDbCacheDir, str(gamesDbPlatform.id))
    #        mkdir(jsonCacheDir)

    #        page = 1

    #        while True:
    #            logging.info("downloading page %d from results" % page)
    #            params = {
    #                'apikey': '%s' % args.tgdbKey,
    #                'id': gamesDbPlatform.id,
    #                'fields': 'overview',
    #                'include': 'boxart',
    #                'page': page
    #            }

    #            response = requests.get(
    #                "%s/Games/ByPlatformID" % GAMESDB_API_URL,
    #                params=params,
    #                headers=HEADERS,
    #                timeout=URL_TIMEOUT,
    #                stream=True
    #            )
    #            if response.status_code == requests.codes.ok:
    #                data = response.json()
    #                if data["status"] != "Success":
    #                    pesExit("Got bad status value: %s" % data["status"])
    #                if "data" not in data or "games" not in data["data"]:
    #                    pesExit("Invalid JSON: %s" % data)
    #                # save JSON to cache for parsing later (if needed to save API requests)
    #                jsonFileCache = os.path.join(jsonCacheDir, "games_%s.json" % page)
    #                logging.debug("saving JSON to: %s" % jsonFileCache)
    #                with open(jsonFileCache, 'w') as f:
    #                    json.dump(data, f)
    #                processGamesDbJson(newDb, session, data)
    #                if data["pages"]["next"]:
    #                    page += 1
    #                else:
    #                    break
    #            else:
    #                pesExit("failed, status code: %s" % response.status_code)
    #    # now we have the games, let's get the extra image JSON
    #    logging.info("downloading GamesDB image JSON")
    #    getGamesDbImages(gamesDbCacheDir)
    #    processGamesDbImageJson(newDb, session, gamesDbCacheDir)

    if args.retroachievementsDir:
        checkDir(args.retroachievementsDir)
        logging.info("using cached RetroAchievements.org data from %s", args.retroachievementsDir)
        result = session.query(pes.sql.RetroAchievementConsole).all()
        for retroConsole in result:
            jsonPath = os.path.join(args.retroachievementsDir, "%d-hashes.json" % retroConsole.id)
            logging.debug("loading JSON from %s", jsonPath)
            checkFile(jsonPath)
            gameHashes = None
            with open(jsonPath, 'r') as f:
                try:
                    gameHashes = json.load(f)
                except Exception as e:
                    pesExit("Failed to load JSON from %s due to:\n%s" % (jsonPath, e))
            processRetroAchievementsJson(newDb, session, gameHashes, retroConsole.id)

    if args.retroachievements:
        logging.info("updating RetroAchievement records")

        # create cache dir
        retroachievementsCacheDir = os.path.join(cacheDir, "retroachievements-%s" % datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
        logging.info("using %s for RetroAchievements JSON cache", retroachievementsCacheDir)
        mkdir(retroachievementsCacheDir)

        # get all consoles with a RetroId
        result = session.query(pes.sql.RetroAchievementConsole).all()
        for retroConsole in result:
            logging.info("processing Retro console ID: %d", retroConsole.id)
            gameHashes = pes.retroachievement.getGameHashes(retroConsole.id)
            jsonPath = os.path.join(retroachievementsCacheDir, "%d-hashes.json" % retroConsole.id)
            logging.info("saving game hashes to: %s", jsonPath)
            with open(jsonPath, "w") as f:
                f.write(json.dumps(gameHashes))
            processRetroAchievementsJson(newDb, session, gameHashes, retroConsole.id)

    if args.match:
        logging.info("matching up theGamesDb records with RetroAchievements records")
        i = 0
        for console in session.query(pes.sql.Console).join(pes.sql.GamesDbPlatform).filter(pes.sql.Console.retroId != 0):
            logging.info("processing console: %s", console.platform.name)
            for gamesDbGame in console.platform.games:
                for retroGame in session.query(pes.sql.RetroAchievementGame).filter(
                    pes.sql.RetroAchievementGame.retroConsoleId == console.retroId
                ).filter(
                    func.lower(
                        func.replace(
                            func.replace(pes.sql.RetroAchievementGame.name, " ", ""), ":", ""
                        )
                    )
                    ==
                    func.lower(
                        func.replace(
                            func.replace(gamesDbGame.name, " ", ""), ":", ""
                        )
                    )
                ):
                    logging.debug("found match for: %s", retroGame.name)
                    gamesDbGame.retroId = retroGame.id
                    session.add(gamesDbGame)
                    i += 1
        logging.info("found %d matches", i)
        if i > 0:
            session.commit()
