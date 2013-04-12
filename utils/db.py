#!/usr/bin/env python
import MySQLdb as mdb
import helper as helper

def getLastArticle(group):
	'''Get the latest article for a group in the db. Arguments:
	- sqldb: the sqlite3 file (str)
	- group: the group name (str)
	Returns:
	- int'''
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	sth = c.execute('SELECT number FROM parts WHERE binaryID = %s ORDER BY number DESC LIMIT 1', (group,))
	resp = sth.fetchone()
	conn.close()
	try:
		return int(resp[0])
	except TypeError:
		return 0
