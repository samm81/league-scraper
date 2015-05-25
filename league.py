import sqlite3
import signal
import sys, getopt
import logging
from random import randint
from requests import ConnectionError
from itertools import chain
from riotwatcher import RiotWatcher, LoLException

max_id = 1000000

tierToPoints = { "BRONZE":0, "SILVER":500, "GOLD":1000, "PLATINUM":1500, "DIAMOND":2000, "CHALLENGER":2500, "MASTER":3000 }
divisionToPoints = { "V":0, "IV":100, "III":200, "II":300, "I":400 }

w = RiotWatcher('b45d3cc2-65fd-4748-989a-f1ee16f1e039')

db_connection = sqlite3.connect('league.db')
db_cursor = db_connection.cursor()

def exit(signal, frame):
	logging.info("Recieved SIGINT, closing database connection and exiting")
	db_connection.close()
	sys.exit(1)
signal.signal(signal.SIGINT, exit)

def instantiateTable():
	db_cursor.execute("create table Summoners(id INT PRIMARY KEY, games INT, wins INT, losses INT, minion_kills INT, champion_kills INT, turret_kills INT, assists INT, win_ratio FLOAT, avg_minion_kills FLOAT, avg_champion_kills FLOAT, avg_turret_kills FLOAT, avg_assists FLOAT, points INT, tier VARCHAR(10), division VARCHAR(3), league_points INT)")

def get_modes_data(summoner_ids):
	return w.get_league_entry(summoner_ids=summoner_ids)

def get_player_data(modes_data, summoner_id):
	return modes_data[str(summoner_id)]

def get_mode_data(player_data, mode):
	for mode_data in player_data:
		if mode_data['queue'] == mode:
			return mode_data
	raise LoLException("No {} mode data".format(mode))

def get_ranked_data(player_data):
	return get_mode_data(player_data, 'RANKED_SOLO_5x5')

def get_ranked_stats(summoner_id):
	stat_summaries = w.get_stat_summary(summoner_id)['playerStatSummaries']
	for stat_summary in stat_summaries:
		if stat_summary['playerStatSummaryType'] == 'RankedSolo5x5':
			return stat_summary['aggregatedStats']
	raise LoLException('No RankedSolo5x5 stats')

def calculate_points(tier, division, league_points):
	return tierToPoints[tier] + divisionToPoints[division] + league_points

def collect_data(summoner_id):
	try:
		ranked_data = get_ranked_data(get_player_data(get_modes_data([summoner_id]), summoner_id))
		ranked_stats = get_ranked_stats(summoner_id)
	except LoLException as e:
		logging.info("LoLException: {}".format(e))
		if str(e) == 'Too many requests': # ugly, but the library is written with monolithic errors
			return True
		return False
	except ConnectionError as e:
		logging.info("Connection error: {}".format(e))
		return True
	except Exception as e:
		logging.error(e)
		return True

	logging.info("data found!")

	tier = ranked_data['tier']
	division = ranked_data['entries'][0]['division']
	league_points = ranked_data['entries'][0]['leaguePoints']
	wins = ranked_data['entries'][0]['wins']
	losses = ranked_data['entries'][0]['losses']

	minion_kills = ranked_stats['totalMinionKills']
	champion_kills = ranked_stats['totalChampionKills']
	turret_kills = ranked_stats['totalTurretsKilled']
	assists = ranked_stats['totalAssists']

	games = int(wins) + int(losses)

	win_ratio = float(wins) / float(games)
	avg_minion_kills = float(minion_kills) / float(games)
	avg_champion_kills = float(champion_kills) / float(games)
	avg_turret_kills = float(turret_kills) / float(games)
	avg_assists = float(assists) / float(games)
	points = calculate_points(tier, division, league_points)

	item = (int(summoner_id), games, int(wins), int(losses), int(minion_kills), int(champion_kills), int(turret_kills), int(assists), win_ratio, avg_minion_kills, avg_champion_kills, avg_turret_kills, avg_assists, points, tier, division, int(league_points))

	logging.info("inserting item: {}".format(item))

	db_cursor.execute("INSERT OR REPLACE INTO Summoners VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", item)
	db_connection.commit()
	
	return False

def randomGenerator():
	while True:
		yield randint(1, max_id)

if __name__ == '__main__':
	summoner_ids = []
	mode = "DEFAULT"
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hi:', ['help', 'importfile=', 'lf=', 'logfile=', 'll=', 'loglevel='])
	except getopt.GetoptError:
		print "usage: league.py [-h --help] [-i file -importfile=file] [-lf=file -logfile=file] [-ll=level -loglevel=level]"
		sys.exit(2)

	logfile = ""
	loglevel = "INFO"
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			print "usage: league.py [-h --help] [-i file --importfile=file] [--lf=file --logfile=file] [--ll=level --loglevel=level]"
			sys.exit()
		elif opt in ('-i', '--import'):
			try:
				import_file = open(arg)
				for line in import_file:
					summoner_ids.append(int(line))	
			except ValueError:
				logging.error("import file is improperly formatted")
				logging.error("file should consist of one id per line")
				sys.exit(3)
			mode = "IMPORT"
		elif opt in ('--lf', '--logfile'):
			logfile = arg
		elif opt in ('--ll', '--loglevel'):
			loglevel = getattr(logging, arg.upper())
	
	if not logfile:
		logging.basicConfig(level=loglevel, format="%(asctime)s| %(module)s %(levelname)s: %(message)s")
	else:
		logging.basicConfig(level=loglevel, filename=logfile, format="%(asctime)s| %(module)s %(levelname)s: %(message)s")
	
	if not summoner_ids:
		summoner_ids = randomGenerator()
	
	logging.info("loaded up")
	logging.info("{} mode".format(mode))
	if logfile:
		logging.info("logging to file {}".format(logfile))
	logging.info("logging level {}".format(loglevel))
	logging.info("getting started")

	for summoner_id in summoner_ids:
		retry = True
		while retry:
			logging.debug("waiting for clearence from riotwatcher")
			while not w.can_make_request():
				pass
			logging.debug("cleared by riotwatcher")
			logging.info("checking id {}..... ".format(summoner_id),)
			retry = collect_data(summoner_id)
			if retry:
				logging.info("...retrying")
