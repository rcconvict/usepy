#!/usr/bin/env python
from optparse import OptionParser
import utils.helper as helper
import utils.db as db
import MySQLdb as mdb
import sys

def getFullName(group):
	if group.startswith('a.b'):
		return 'alt.binaries.%s' % group[4:]
	else:
		return group

def main():
	parser = OptionParser(usage="usage: %prog [options]")
	parser.add_option('-a', '--activate', dest='activate',
		default=False, help='activate a group') 
	parser.add_option('-d', '--deactivate', dest='deactivate',
		default=False, help='deactivate a group')
	parser.add_option('-l', '--list', dest='list',
		default=False, action='store_true', help='get list of active groups')
	parser.add_option('-i', '--info', dest='info',
		default=False, help='get info from a group')
	(options, args) = parser.parse_args()

	if options.activate != False:
		group = getFullName(options.activate)
		try:
			gid = db.getGroupID(group)
		except TypeError:
			print 'Group does not exist.'
			sys.exit(-1)
		db.activateGroup(group)		
		print '%s activated.' % group

	if options.deactivate != False:
		group = getFullName(options.deactivate)
		try:
			gid = db.getGroupID(group)
		except TypeError:
			print 'Group does not exist.'
			sys.exit(-1)
		db.deactivateGroup(group)
		print '%s deactivated.' % group

	if options.list == True:
		list = db.getActiveGroups()
		for i in list:
			print db.getGroupName(i)

	if options.info != False:
		group = getFullName(options.info)
		try:
			gid = db.getGroupID(group)
		except TypeError:
			print 'Group does not exist.'
			sys.exit(-1)
		mysqlInfo = helper.getMySQLInfo()
		conn = mdb.connect(*mysqlInfo)
		c = conn.cursor()
		c.execute('SELECT ID, active, first_record, first_record_postdate, last_record, last_record_postdate, last_updated FROM groups WHERE name = %s', (group))
		ret = c.fetchone()
		conn.close()
		print 'Group ID: %s' % ret[0]
		print 'Group is %s' % ('active.' if bool(ret[1]) else 'deactivated.')
		print 'First record and postdate: %s - %s' % (ret[2], ret[3])
		print 'Last record and postdate: %s - %s' % (ret[4], ret[5])
		print 'Last updated on %s' % ret[6]


if __name__ == '__main__':
	main()
