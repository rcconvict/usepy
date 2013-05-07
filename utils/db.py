#!/usr/bin/env python
import MySQLdb as mdb
import helper as helper
import datetime, re

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

def deactivateGroup(group):
	'''Deactivate a group. Arguments:
	- group: group name (str)
	Returns:
	- bool'''
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	try:
		c.execute('UPDATE groups SET active = 0 WHERE name = %s', (group))
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

	#params = [(binaryID, i[1]['message-id'], i[0], '1', i[1][':bytes']) for i in over]
	params = list()
	pattern = "(\d{1,4})of(\d{1,4})"
	regex = re.compile(pattern, re.IGNORECASE)

	for i in over:
		message = i[1]['message-id'][1:-1]
		number = i[0]
		r = regex.search(message)
		try:
			file = r.groups()[0]
			maxFiles = r.groups()[1]
		except AttributeError:
			file = 1
		size = i[1][':bytes']
		params.append([binaryID, message, number, file, size])

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

def touchGroup(group):
	'''Touch the timestamp of last updated. Arguments:
	- group: the groupID of the group (int)
	Returns:
	None'''
	
	mysqlInfo = helper.getMySQLInfo()
	conn = mdb.connect(*mysqlInfo)
	c = conn.cursor()
	c.execute('UPDATE groups SET last_updated = NOW() WHERE ID = %s', (group))
	conn.commit()
	conn.close()
	

def addArticles(group, first, last, first_date, last_date):
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
		c.execute('UPDATE groups SET first_record = %s, last_record = %s, last_updated = NOW(), first_record_postdate = %s, last_record_postdate = %s where ID = %s', (first, last, first_date, last_date, group)) 
	else:
		c.execute('UPDATE groups SET last_record = %s, last_record_postdate = %s,  last_updated = NOW() where ID = %s', (last, last_date, group))

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
