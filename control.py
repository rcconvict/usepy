#!/usr/bin/env python
from optparse import OptionParser
import utils.db as db
import sys

def main():
	parser = OptionParser(usage="usage: %prog [options]")
	parser.add_option('-a', '--activate', dest='activate',
		default=False, help='activate a group') 
	parser.add_option('-d', '--deactivate', dest='deactivate',
		default=False, help='deactivate a group')
	parser.add_option('-l', '--list', dest='list',
		default=False, action='store_true', help='get list of active groups')
	(options, args) = parser.parse_args()

	if options.activate != False:
		try:
			gid = db.getGroupID(options.activate)
		except TypeError:
			print 'Group does not seem to exist.'
			sys.exit(-1)
		db.activateGroup(options.activate)		
		print '%s activated.' % options.activate

	if options.deactivate != False:
		try:
			gid = db.getGroupID(options.deactivate)
		except TypeError:
			print 'Group does not seem to exist.'
			sys.exit(-1)
		db.deactivateGroup(options.deactivate)
		print '%s deactivated.' % options.deactivate

	if options.list == True:
		list = db.getActiveGroups()
		for i in list:
			print db.getGroupName(i)

if __name__ == '__main__':
	main()
