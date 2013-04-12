#!/usr/bin/env python
import utils.db as db
import utils.helper as helper
import config
import sqlite3 # just for the excpetions atm

# connect to the server
NNTP_INFO = [config.NNTP_Address, config.NNTP_Port, config.NNTP_SSL, config.NNTP_Username, config.NNTP_Password]
socket = helper.con(*NNTP_INFO)

# get the welcome msg
print socket.getwelcome()

# show group overview
print helper.group_overview(socket, 'alt.binaries.x264')

# update group (only does headers for now)
try:
	resp = helper.update_group(socket, config.SQLDB, 'alt.binaries.x264')
	print resp
except sqlite3.OperationalError, e:
	# create the parts table if it doesn't exist and re-run update_group
	if 'table: parts' in str(e):
		conn = sqlite3.connect(config.SQLDB)
		c = conn.cursor()
		c.execute('CREATE TABLE parts (group_name TEXT, article_id int, message_id TEXT, subject TEXT, date_posted TEXT, dt datetime default current_timestamp)')
		conn.commit()
		conn.close()
		resp = helper.update_group(socket, config.SQLDB, 'alt.binaries.x264')
		print resp
	else:
		print e
		
	

# CLOSE THE SOCKET FOR THE LOVE OF GOD CLOSE THE FUCKING SOCKET
socket.quit()
