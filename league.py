import sqlite3
import signal
import sys
from random import randint
from requests import ConnectionError
from riotwatcher import RiotWatcher, LoLException

max_id = 1000000

tierToPoints = { "BRONZE":0, "SILVER":500, "GOLD":1000, "PLATINUM":1500, "DIAMOND":2000, "CHALLENGER":2500, "MASTER":3000 }
divisionToPoints = { "V":0, "IV":100, "III":200, "II":300, "I":400 }

w = RiotWatcher('b45d3cc2-65fd-4748-989a-f1ee16f1e039')

db_connection = sqlite3.connect('league.db')
db_cursor = db_connection.cursor()

def exit(signal, frame):
	db_connection.close()
	sys.exit(1)
signal.signal(signal.SIGINT, exit)

def instantiateTable():
	db_cursor.execute('create table Summoners(id INT PRIMARY KEY, games INT, wins INT, losses INT, minion_kills INT, champion_kills INT, turret_kills INT, assists INT, win_ratio FLOAT, avg_minion_kills FLOAT, avg_champion_kills FLOAT, avg_turret_kills FLOAT, avg_assists FLOAT, points INT, tier VARCHAR(10), division VARCHAR(2), league_points INT)')

def get_modes_data(summoner_ids):
	return w.get_league_entry(summoner_ids=summoner_ids)

def get_player_data(modes_data, summoner_id):
	return modes_data[str(summoner_id)]

def get_mode_data(player_data, mode):
	for mode_data in player_data:
		if mode_data['queue'] == mode:
			return mode_data
	return {}

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
	except (LoLException, ConnectionError) as e:
		print e
		return

	print "data found!"

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

	print "inserting item: {}".format(item);

	db_cursor.execute('INSERT OR REPLACE INTO Summoners VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', item)
	db_connection.commit()

if __name__ == '__main__':
	while True:
		while w.can_make_request():
			summoner_id = randint(1, max_id)
			#summoner_id = 20132258
			print "checking id {}..... ".format(summoner_id),
			collect_data(summoner_id)
