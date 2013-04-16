#!/usr/bin/env python
import MySQLdb as mdb
import helper as helper

def activateGroup(group):
	'''Activate a group. Arguments:
	- group: group name (str)
	Returns:
	- bool'''
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	try:
		c.execute('UPDATE groups SET active = 1 WHERE name = %s', (group))
	except Exception, e:
		return False
	finally:
		conn.commit()
		conn.close()
		return True	

def getActiveGroups():
	'''Gets a list of active groups. Arguments:
	- None
	Returns:
	- list'''
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT ID FROM groups WHERE active = 1')
	ret = c.fetchall()
	conn.close()
	fmt = []
	for i in ret:
		fmt.append(int(i[0]))
	return fmt


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

def getGroupName(group):
	'''Get the group name from ID. Arguments:
	- group: group id (int)
	Returns:
	- group: group name (str)'''
	
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT name FROM groups WHERE ID = %s LIMIT 1', (group,))
	ret = c.fetchone()
	conn.close()
	return str(ret[0])

def updateGroup(group, first, last, first_date, last_date):
	'''Update the record for the group. Arguments:
	- group: the groupID of the group (int)
	- first: the first article we have locally (int)
	- last: last record received from server.
	- first_date: the date of the first article we have
	- last_date: the date of the last article we have 
	Returns:
	None'''

	# todo: add actual posted dates
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('SELECT first_record FROM groups WHERE active = 1 AND ID = %s', (group))
	ret = c.fetchone()

	if int(ret[0]) == 0:
		c.execute('UPDATE groups SET first_record = %s, last_record = %s, first_record_postdate = NOW(), last_updated = NOW(), last_record_postdate = NOW() where ID = %s', (first, last, group)) 
	else:
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
