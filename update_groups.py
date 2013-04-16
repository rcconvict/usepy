#!/usr/bin/env python
import utils.db as db
import utils.helper as helper
import datetime, sys
try:
	from dateutil.parser import parse
except ImportError:
	print 'Install the dateutil python package.'
	sys.exit(-1)

def main():
	NNTP_INFO = helper.getUsenetInfo()
	socket = helper.con(*NNTP_INFO)
	
	# get the welcome msg
	#print socket.getwelcome()
	
	# get list of active groups
	activeGroups = db.getActiveGroups()
	if len(activeGroups) == 0:
		print 'There are no groups activated. You can activate groups with control.py.'
		sys.exit(-1)
	
	for i in activeGroups:
		gid = i
		groupName = db.getGroupName(gid)
	
		# change group and get info
		_, _, first, last, _ = socket.group(groupName)
		
		# get last local article
		lastDBArticle = db.getLastArticle(gid)			
	
		toFetch = last - lastDBArticle
		if toFetch == 0:
			print 'No new articles for %s, skipping.' % groupName
			db.touchGroup(gid)
			continue
	
		# get last 100 articles on server if we don't have any	
		if lastDBArticle == 0:
			lastDBArticle = last - 100
		
		# get article headers and add them to the DB
		resp, overviews = socket.over((lastDBArticle, last))
		db.addParts(gid, overviews)
		
		# update the group with new info
		firstTime = parse(overviews[0][1]['date'])
		lastTime = parse(overviews[0][-1]['date'])
		db.updateGroup(gid, first, last, str(firstTime.strftime('%Y-%m-%d %H:%M:%S')), str(lastTime.strftime('%Y-%m-%d %H:%M:%S')))
	
			
		# stats
		print 'Updated group %s' % groupName
		print 'Last local article num: %s' % lastDBArticle
		print 'Last server article num: %s' % last
		print "Added %d parts.\n" % (last-lastDBArticle)
		
	
	# CLOSE THE SOCKET FOR THE LOVE OF GOD CLOSE THE FUCKING SOCKET
	socket.quit()

if __name__ == '__main__':
	main()
