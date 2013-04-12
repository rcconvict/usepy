#!/usr/bin/env python
import sys, socket, db
import sqlite3
from datetime import datetime
import nntplib
import ConfigParser

def getUsenetInfo(configFile='config.ini'):
	config = ConfigParser.ConfigParser()
	config.read(configFile)
	address = config.get('usenet', 'address')
	port = config.getint('usenet', 'port')
	ssl = config.getboolean('usenet', 'ssl')
	username = config.get('usenet', 'username')
	password = config.get('usenet', 'password')
	return address, port, ssl, username, password

def getMySQLInfo(configFile='config.ini'):
	try:
		config = ConfigParser.ConfigParser()
		config.read(configFile)
		address = config.get('mysql', 'address')
		username = config.get('mysql', 'username')
		password = config.get('mysql', 'password')
		database = config.get('mysql', 'database')
		return address, username, password, database
	except ConfigParser.NoSectionError:
		print 'Could not locate the mysql portion of your config.ini. Please delete it and re-run setup.py.'

def _check_sock(socket):
	if not isinstance(socket, (nntplib.NNTP, nntplib.NNTP_SSL)):
		raise TypeError('Wrapper handed is not a valid NNTP wrapper.')

def con(host, port, ssl, username, password):
	'''Connect to UNS and return socket. Arguments:
	- host: valid UNS hostname (str)
	- port: valid UNS port (str)
	- ssl: (boolean)
	- username: UNS username (str)
	- password: UNS password (str)
	Returns:
	- UNS NNTP socket (object)'''
	if ssl == True:
		socket = nntplib.NNTP_SSL(host, port, username, password)
	else:
		socket = nntplib.NNTP(host, port, username, password)
	return socket

def groupOverview(socket, group):
	'''Process Group Overview. Arguments:
	- socket: valid NNTP socket (object)
	- group: valid group name (str)
	Returns:
	- string'''
	_check_sock(socket)
	resp, count, first, last, name = socket.group(group)
	count = "{:,}".format(int(count))
	return 'Group %s has a total of %s articles. The oldest article is %s and the newest article is %s.' % (name, count, first, last)

def groupLast(socket, group):
	'''Get last group article number. Arguments:
	- socket: valid NNTP socket (object)
	- group: valid group name (str)
	Returns:
	- integer'''
	_check_sock(socket)
	resp, count, first, last, name = socket.group(group)
	return int(last)

def groupFirst(socket, group):
	'''Get first group article number. Arguments:
	- socket: valid NNTP socket (object)
	- group: valid group name (str)
	Returns:
	- integer'''
	_check_sock(socket)
	resp, count, first, last, name = socket.group(group)
	return int(first)

def updateGroup(socket, sqldb, group, articles=100):
	# Only updates headers for now
	'''Update group and dump info into sql. Arguments:
	- socket: valid nntp socket (obj)
	- sqldb: valid sqlite3 location (str)
	- group: valid gropu (str)
	- articles: num articles to fetch (int)
	Returns:
	- ???'''
	_check_sock(socket)
	reach = 1000
	# Get the last article we have in the DB
	last_id = db.get_last_article(sqldb, group)
	if last_id == 0:
		# if we haven't indexed this group then go back var(reach) articles
		last_id = group_last(socket, group) - reach

	# The last article on the server
	last_article = group_last(socket, group)
	total = last_article - last_id
	if total == 0:
		return 'No articles to fetch. Up to date.'

	conn = sqlite3.connect(sqldb)
	c = conn.cursor()
	# Set the group
	socket.group(group)

	print 'Getting %s articles starting at article ID #%d in %s.' % (total, last_id, group)
	multiple_rows = []
	errors = 0
	startTime = datetime.now()
	resp, overviews = socket.over((str(last_id), str(last_article)))
	print 'Time to fetch articles: %s.' % (datetime.now() - startTime)
	for article_num, over in overviews:
		multiple_rows.append([group, article_num, over['message-id'], over['subject']])
	
	print 'Grabbed all headers, inserting %d rows into DB' % (len(multiple_rows))
	startTime = datetime.now()
	c.executemany('INSERT INTO parts (group_name, article_id, message_id, subject) VALUES (?, ?, ?, ?)', multiple_rows)
	print 'Time to insert articles into DB: %s.' % (datetime.now() - startTime)
	conn.commit()
	conn.close()
	return 'Server replied %d articles out of %d articles.' % ((total - errors), total)
