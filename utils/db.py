#!/usr/bin/env python
import MySQLdb as mdb
import helper as helper

def addParts(binaryID, over):
	'''Add header info to parts. Arguments:
	- binaryID : the group id (int)
	- over: the overview info from nntp.over() (tuple)
	Returns:
	None'''

	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	sql = 'INSERT INTO parts (binaryID, messageID, number, partnumber, size, dateadded) VALUES (%s, %s, %s, %s, %s, NOW())'
	params = [(binaryID, i[1]['message-id'], i[0], '1', i[1][':bytes']) for i in over]
	c.executemany(sql, params)
	conn.commit()
	conn.close()
	
def getGroupID(group):
	'''Get the binaryID of a group from mysql. Arguments:
	- group: group name (str)
	Returns:
	- groupID: id associated with the group (int)'''

	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT ID FROM groups WHERE name = %s LIMIT 1', (group,))
	resp = c.fetchone()
	conn.close()
	return int(resp[0])

def updateGroup(group, last):
	'''Update the record for the group. Arguments:
	- group: the groupID of the group (int)
	- last: last record received from server.
	Returns:
	None'''

	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('UPDATE groups SET last_record = %s, last_updated = NOW() where ID = %s', (last, group))
	conn.commit()
	conn.close()

def getLastArticle(group):
	'''Get the latest article for a group in the db. Arguments:
	- sqldb: the sqlite3 file (str)
	- group: the group name (str)
	Returns:
	- int'''

	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT last_record FROM groups WHERE ID = %s ORDER BY last_record DESC LIMIT 1', (group,))
	resp = c.fetchone()
	conn.close()
	try:
		return int(resp[0])
	except TypeError:
		return 0
