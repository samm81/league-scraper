import sqlite3
import json

def dict_factory(cursor, row):
    return {header: data for header, data in zip([head[0] for head in cursor.description], row)}

db_connection = sqlite3.connect('league.db')
db_connection.row_factory = dict_factory
db_cursor = db_connection.cursor()

if __name__ == '__main__':
	db_cursor.execute('select * from Summoners')
	print json.dumps(db_cursor.fetchall())
