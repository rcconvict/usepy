#!/usr/bin/env python
from optparse import OptionParser
import utils.helper as helper
import utils.groups as groups
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
	(options, args) = parser.parse_args()


	if options.activate != False:
		group = getFullName(options.activate)
		try:
			gid = int(groups.getIDByName(group))
		except TypeError:
			print 'Group does not exist.'
			sys.exit(-1)
		groups.updateGroupStatus(gid, 1)
		print '%s activated.' % group

	if options.deactivate != False:
		group = getFullName(options.deactivate)
		try:
			gid = groups.getIDByName(group)
		except TypeError:
			print 'Group does not exist.'
			sys.exit(-1)
		groups.updateGroupStatus(gid, 0)
		print '%s deactivated.' % group

if __name__ == '__main__':
	main()
