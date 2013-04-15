#!/usr/bin/env python
import MySQLdb as mdb
import helper as helper

def getGroupID(group):
	'''Get the binaryID of a group from mysql'''
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT ID FROM groups WHERE name = %s LIMIT 1', (group,))
	resp = c.fetchone()
	conn.close()
	return int(resp[0])


def getLastArticle(group):
	'''Get the latest article for a group in the db. Arguments:
	- sqldb: the sqlite3 file (str)
	- group: the group name (str)
	Returns:
	- int'''
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT last_record FROM parts WHERE binaryID = %s ORDER BY last_record DESC LIMIT 1', (group,))
	resp = c.fetchone()
	conn.close()
	try:
		return int(resp[0])
	except TypeError:
		return 0
