#!/usr/bin/env python
from optparse import OptionParser
import utils.db as db
import sys

def main():
	parser = OptionParser(usage="usage: %prog [options]")
	parser.add_option('-a', '--activate', dest='activate',
		default=False, help='activate a group') 
	(options, args) = parser.parse_args()

	if options.activate != False:
		try:
			gid = db.getGroupID(options.activate)
		except TypeError:
			print 'Group does not seem to exist.'
			sys.exit(-1)
		db.activateGroup(options.activate)		
		print '%s activated.' % options.activate

if __name__ == '__main__':
	main()
