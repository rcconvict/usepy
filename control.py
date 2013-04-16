#!/usr/bin/env python
from optparse import OptionParser
import utils.db as db
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
	(options, args) = parser.parse_args()

	if options.activate != False:
		group = getFullName(options.activate)
		try:
			gid = db.getGroupID(group)
		except TypeError:
			print 'Group does not seem to exist.'
			sys.exit(-1)
		db.activateGroup(group)		
		print '%s activated.' % group

	if options.deactivate != False:
		group = getFullName(options.deactivate)
		try:
			gid = db.getGroupID(group)
		except TypeError:
			print 'Group does not seem to exist.'
			sys.exit(-1)
		db.deactivateGroup(group)
		print '%s deactivated.' % group

	if options.list == True:
		list = db.getActiveGroups()
		for i in list:
			print db.getGroupName(i)

if __name__ == '__main__':
	main()
