#!/usr/bin/env python
import utils.db as db
import utils.helper as helper
import datetime, sys
try:
	from dateutil.parser import parse
except ImportError:
	print 'Install the dateutil python package.'
	sys.exit(-1)

def enumerateArticles(start, end, increment):
	starting = range(start, end, increment)
	ending = list()
	for i in starting:
		if (i+99) <= end:
			ending.append(i+99)
		else:
			rest = end % increment
			ending.append(i+rest)
	dictionary = dict(zip(starting, ending))
	return dictionary

def updateGroup(gid):
	NNTP_INFO = helper.getUsenetInfo()
	socket = helper.con(*NNTP_INFO)

	# get group name
	groupName = db.getGroupName(gid)

	# change group and get info
	_, _, first, last, _ = socket.group(groupName)
	
	# get last local article
	lastDBArticle = db.getLastArticle(gid)			

	toFetch = last - lastDBArticle
	if toFetch == 0:
		print 'No new articles for %s, skipping.' % groupName
		db.touchGroup(gid)
		return

	# get last 100 articles on server if we don't have any	
	if lastDBArticle == 0:
		lastDBArticle = last - 382
	
	# get article headers and add them to the DB
	# Sometimes get utf-8 decode errors, fix this later
	range = last - lastDBArticle

	# only fetch 100 articles at a time in the event that there are a lot of articles
	# so that we don't chew through memory. Maybe get this part multithreaded later.
	if range >= 100:
		toFetch = enumerateArticles(lastDBArticle, last, 100)
		for key, value in toFetch.items():
			try:
				resp, overviews = socket.over((key, value))
			except LookupError, e:
				print 'Unable to fetch article range %s-%s for %s.' % (key, value, groupName)
				pass
			db.addParts(gid, overviews)
			del overviews, resp
	else:
		try:
			resp, overviews = socket.over((lastDBArticle, last))
		except LookupError, e:
			print 'Unable to update group %s.' % (groupName)
			print e
			return
		db.addParts(gid, overviews)
	
	# update the group with new info
	firstTime = parse(overviews[0][1]['date'])
	lastTime = parse(overviews[0][-1]['date'])
	db.addArticles(gid, first, last, str(firstTime.strftime('%Y-%m-%d %H:%M:%S')), str(lastTime.strftime('%Y-%m-%d %H:%M:%S')))
		
	# stats
	print 'Updated group %s' % groupName
	print 'Last local article num: %s' % lastDBArticle
	print 'Last server article num: %s' % last
	print "Added %d parts.\n" % (last-lastDBArticle)

	# close the socket
	socket.quit()


def main():
	# get list of active groups
	activeGroups = db.getActiveGroups()
	if len(activeGroups) == 0:
		print 'There are no groups activated. You can activate groups with control.py.'
		sys.exit(-1)
	
	for i in activeGroups:
		updateGroup(i)
	

if __name__ == '__main__':
	main()
