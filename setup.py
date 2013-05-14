#!/usr/bin/env python
import sys, os
import ConfigParser
from subprocess import Popen, PIPE
from getpass import getpass
import utils.helper as helper
from utils.nntplib import NNTPError

skip_mysql = False

try:
	import MySQLdb as mdb
except ImportError:
	print 'You need to install python-mysqldb'
	sys.exit(1)


if not os.path.isfile('config.ini'):
	# Usenet configuration
	address = raw_input('Usenet address: ')
	port = raw_input('Usenet server port: ')
	ssl = raw_input('SSL? True, False: ')
	username = raw_input('Usenet username: ')
	password = getpass('Usenet password: ')
	
	config = ConfigParser.RawConfigParser()
	config.add_section('usenet')
	config.set('usenet', 'address', address)
	config.set('usenet', 'port', port)
	config.set('usenet', 'ssl', ssl)
	config.set('usenet', 'username', username)
	config.set('usenet', 'password', password)
	
	if not skip_mysql:
		# mysql configuration
		address = raw_input('MySQL server address: ')
		username = raw_input('MySQL username: ')
		password = getpass('MySQL password: ')
		database = raw_input('MySQL database name: ')
		
		config.add_section('mysql')
		config.set('mysql', 'address', address)
		config.set('mysql', 'username', username)
		config.set('mysql', 'password', password)
		config.set('mysql', 'database', database)
	
	with open('config.ini', 'wb') as configfile:
		config.write(configfile)
else:
	print 'Configuration file already exists. Skipping.'

# test usenet access
nntpInfo = helper.getUsenetInfo()
try:
	socket = helper.con(*nntpInfo)
	if socket.getwelcome().startswith('200'):
		print 'Connected to usenet server, looking good!'
except NNTPError, e:
	print e
finally:
	socket.quit()

# test/setup mysql access
def checkMySQL():
	MySQLInfo = helper.getMySQLInfo()
	try:
		con = mdb.connect(*MySQLInfo)
	except mdb.Error, e:
		if e.args[0] in [2002, 1045] :
			print 'Username/password mismatch.'
			print 'We are now going to create a new account for usepy access with mysql.'
			username = raw_input('Enter the administrator username for mysql: ')
			password = getpass('Enter the administrator password for mysql: ')
			con = mdb.connect(MySQLInfo[0], username, password)
			c = con.cursor()
			c.execute("CREATE USER %s@%s IDENTIFIED BY %s", (MySQLInfo[1], MySQLInfo[0], MySQLInfo[2]))
			c.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (MySQLInfo[3]))
			ret = c.fetchone()
			if ret == None:
				c.execute("CREATE DATABASE %s" % MySQLInfo[3])
			c.execute("GRANT ALL ON %s.* TO '%s'@'%s'" % (MySQLInfo[3], MySQLInfo[1], MySQLInfo[0]))
	finally:
		try:
			if con:
				con.close()
		except NameError:
			pass
	
	print 'Importing schema.sql'
	process = Popen('mysql %s -u%s -p%s' % (MySQLInfo[3], MySQLInfo[1], MySQLInfo[2]),
		stdout=PIPE, stdin=PIPE, shell=True)
	output = process.communicate('source '+ 'db/schema.sql')[0]
	print output

checkMySQL()
