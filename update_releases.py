#!/usr/bin/env python
import sys
sys.path.append('utils')

import category, releases, groups, db, consoletools

try:
	groupName = sys.argv[3]
except IndexError:
	groupName = ''

def printHelp():
	print 'update_releases.py 1 true		...: Creates releases and attempts to categorize new releases.'
	print 'update_releases.py 2 true		...: Creates releases and leaves new releases in other -> misc'
	print 'You must pass a second argument whether to post process or not, true/false.'
	print 'You can pass a third option argument, a group name(ex: alt.binaries.multimedia).'
	print 'Extra commands:'
	print 'update_releases.py 4 true		...: Puts all releases in other -> misc (also resets to look like the have never been categorized).'
	print 'update_releases.py 5 true		...: Categorizes all releases in other -> misc (which ahve not been categorized already).'
	print 'update_releases.py 6 false		...: Categorizes releases in misc sections using the search name.'
	print 'update_releases.py 7 true		...: Categorizes releases in all sections using the search name.'
	sys.exit(-1)

def main():
	try:
		arg1 = int(sys.argv[1])
		arg2 = sys.argv[2]
	except IndexError:
		print 'ERROR: You must supply arguments.'
		printHelp()
	
	r = releases.Releases()
	
	if arg1 == 1 and arg2 == 'true':
		r.processReleases(1, 1, groupName)
	elif arg1 == 1 and arg2 == 'false':
		r.processReleases(1, 2, groupName)
	elif arg1 == 2 and arg2 == 'true':
		r.processReleases(2, 1, groupName)
	elif arg1 == 2 and arg2 == 'false':
		r.processReleases(2, 2, groupName)
	elif arg1 == 4 and (arg2 == 'true' or arg2 == 'false'):
		print 'Moving all releases to other -> misc, this can take a while, be patient.'
		r.resetCategorize()
	elif arg1 == 5 and (arg2 == 'true' or arg2 == 'false'):
		print 'Categorizing all non-categorized releases in other->misc using usenet subject. This can take a while. Be patient.'
		timestart = time.time()
		relcount = r.categorizeRelease('name', 'WHERE relnamestatus = 0 and categoryID = 7010', True)
		c = consoletools.ConsoleTools()
		etime = c.convertTime(int(time.time() - timestart))
		print 'Finished categorizing %d releases in %s, using the usenet subject' % (relcount, etime)
	elif arg1 == 6 and arg2 == 'true':
		print 'Categorizing releases in all sections using the searchname. This can take a while, be patient.'
		timestart = time.time()
		relcount = r.categorizeRelease('searchname', '', True)
		c = consoletools.ConsoleTools()
		etime = c.convertTime(int(time.time() - timestart))
		print 'Finsihed categorizing %d releases in %s, using the search name.' % (relcount, etime)
	elif arg1 == 6 and arg2 == 'false':	
		print 'Categorizing releases in misc sections using the searchname. This can take a while, be patient.'
		timestart = time.time()
		relcount = r.categorizeRelease('searchname', 'WHERE categoryID in (1090, 2020, 3050, 5050, 6050, 7010)', True)
		c = consoletools.ConsoleTools()
		etime = c.convertTime(int(time.time() - timestart))
		print 'Finished categorizing %d releases in %s, using the search name.' % (relcount, etime)
	else:
		print 'Wrong argument.'
		printHelp()

if __name__ == '__main__':
	main()
