#!/usr/bin/env python
from dateutil.parser import parse
import binaries
from db import DB
import nntplib
import groups
import time

class Backfill():
	def __init__(self):
		self.n = "\n"

	def backfillAllGroups(self, groupName=''):
		n = self.n

		if groupName != '':
			grp = groups.getByName(groupName)
			if grp:
				res = dict(grp)
		else:
			res = groups.getActive()

		counter = 1
		if res:
			nntp = nntplib.connect()

			for groupArr in res:
				left = len(res)-counter
				print '%sStarting group %d of %d.%s' % (n, counter, len(res), n)
				self.backfillGroup(nntp, groupArr, left)
				counter += 1
		else:
			print 'No groups specified. Ensure groups are added to usepy\'s database for updating.'+n

	def backfillGroup(self, nntp, groupArr, left):
		mdb = DB()
		b = binaries.Binaries()		
		n = self.n
		self.startGroup = time.time()
		
		# no compression
		data = nntp.group(groupArr['name'])

		# get targetpost based on days target
		targetpost = self.daytopost(nntp,groupArr['name'],groupArr['backfill_target'],True)
		if groupArr['first_record'] == 0 or groupArr['backfill_target'] == 0:
			print 'Group %s has invalid numbers. Have you ran update on it? Have you set the backfill days amount?%s' % (groupArr['name'], n)
			return

		print 'Group %s: server has %d - %d, or ~ %d days.' % (data['group'], data['first'], data['last'], int(self.postdate(nntp, data['last'],False) - self.postdate(nntp, data['first'],False))/86400)
		print 'Local first = %d (%d days). Backfill target of %d days is post targetpost.' % (groupArr['first_record'], (int(time.time()) - self.postdate(nntp, groupArr['first_record'],False))/86400, groupArr['backfill_target'])

		if targetpost >= groupArr['first_record']:
			print 'Nothing to do, we already have the target post.'+n+n
			return ''

		if targetpost < data['first']:
			print 'WARNING: Backfill came back as before server\'s first. Setting targetpost to server first.%sSkipping group: %s.' % (n, data['group'])
			return ''

		# calculate number of posts
		total = groupArr['first_record'] - targetpost
		done = False

		# set first and last, moving the window by maxxMssgs
		last = groupArr['first_record'] - 1

		# set the initial 'chunk'
		first = last - b.messagebuffer + 1

		# just in case this is the last chunk we needed.
		if targetpost > first:
			first = targetpost

		while done == False:
			b.startLoop = time.time()

			print 'Getting %d articles from %s. %d group(s) left. (%d articles in queue).' % (last-first+1, data['group'].replace('alt.binaries', 'a.b'), left, first-targetpost)
			b.scan(nntp, groupArr, first, last, 'backfill')

			mdb.query('UPDATE groups SET first_record = %s, last_updated = now() WHERE ID = %d', (first, groupArr['ID']))
			if first == targetpost:
				done = True

			else:
				last = first - 1
				first = last - b.messagebuffer + 1
				if targetpost > first:
					first = targetpost

		first_record_postdate = self.postdate(nntp, first, False)
		# set group's first postdate
		mdb.query('UPDATE groups SET first_record_postdate = FROM_UNIXTIME(%s), last_updated = now() WHERE ID = %d', (first_record_postdate, groupArr['ID']))
		
		timeGroup = int(time.time() - self.startGroup)
		print 'Group processed in %d seconds.' % timeGroup

	def safebackfill(self, articles=''):
		mdb = DB()
		n = self.n

		targetdate = '2012-06-04'
		groupname = mdb.queryOneRow('select name from groups where (first_record_date between %s and now()) and (active = 1) order by name asc', (targetdate,))

		if groupname == None:
			print 'No groups to backfill. They are all at the target date %s.' % targetdate
			sys.exit()
		else:
			self.backfillPostAllGroups(groupname['name'], articles)

	def backfillPostAllGroups(self, groupName = '', articles = '', stype = ''):
		n = self.n
		if groupname != '':
			grp = groups.getByName(groupName)
			if grp:
				res = dict(grp)
		else:
			if stype == 'normal':
				res = groups.getActive()
			elif stype == 'date':
				res = groups.getActiveByDate()

		counter = 1
		if res:
			for groupArr in res:
				left = len(res) - counter
				print 'Starting group %d of %d.' % (counter, len(res))
				self.backfillPostGroup(groupArr, articles, left)
				counter += 1

		else:
			print 'No groups specified. Ensure groups are added to usepy\'s database for updating.'

	def backfillPostGroup(self, groupArr, articles, left):
		mdb = DB()
		b = binaries.Binaries()
		n = self.n
		self.startGroup = time.time()

		print 'Processing %s.' % groupArr['name']
		data = nntp.group(groupArr['name'])
		
		# get targetpost based on days target
		targetpost = round(groupArr['first_record'] - articles)
		print 'Group %s\'s oldest article is %d, newewst is %d.' % (data['group'], data['first'], data['last'])
		print 'The groups retention is: %d days.' % int(self.postdate(nntp, data['last'], False) - self.postdate(nntp, data['first'],False)/86400)
		print 'Our oldest article is: %d which is %d days old.' % (groupArr['first_record'], int(time.time()) - self.postdate(nntp, groupArr['first_record'],False)/86400)
		print 'Our backfill target is article %d which is %d days old.' % (targetpost, int(time.time()) - self.postdate(nntp, targetpost, False)/86400)

		if groupArr['first_record'] <= 0 or targetpost <= 0:
			print 'You need to run update_binaries on the group. Otherwise the group is dead, you must disable it.'
			return ''

		# check if we are grabbing further than the server has
		if targetpost < data['first']:
			groups.disableForPost(groupArr['name'])
			print 'WARNING: Attempting to backfill further than usenet\'s first article, setting our first article date very high so safe backfill can skip it.'
			print 'Skipping group.'
			return ''

		# if our estimate comes back with stuff we already have, finish
		if targetpost >= groupArr['first_record']:
			print 'Nothing to do, we already have the first target post.'+n+n
			return ''

		# calculate total number of parts
		total = groupArr['first_record'] - targetpost
		done = False
		# set first and last, moving the window by maxxMssgs
		last = groupArr['first_record'] - 1
		# set the initial 'chunk'
		first = last - b.messagebuffer + 1
		# just in case this is the last chunk we needed
		if targetpost > first:
			first = targetpost
	
		while done == False:
			b.startLoop = time.time()
			print 'Getting %d articles from %s, %d group(s) left. (%d articles in queue).' % \
				(last-first+1, data['group'].replace('alt.binaries', 'a.b'), left, first-targetpost)
			b.scan(nntp, groupArr, first, last, 'backfill')

			mdb.query('UPDATE groups SET first_record = %s, last_updated = now() WHERE ID = %d', (first, groupArr['ID']))
			if first == targetpost:
				done = True
			else:
				last = first -1
				first = last - b.messagebuffer + 1
				if targetpost > first:
					first = targetpost

		first_record_postdate = self.postdate(nntp, first, False)
		nntp.quit()
		mdb.query('UPDATE groups SET first_record_postdate = FROM_UNIXTIME(%s), last_updated = now() WHERE ID = %d', (groupArr['ID'],))

		timeGroup = int(time.time() - self.startGroup)
		print 'Group processed in %d second(s).' % timeGroup

	def postdate(self, nntp, post, debug=True):
		n = self.n
		attempts = 0
		success = False

		while attempts <= 3 and success == False:
			resp, msgs = nntp.over((post, post))
			try:
				date = msgs[0][1]['date']
				date = parse(date).strftime('%s')
				success = True
			except:
				attempts += 1

		try:
			if debug: print 'DEBUG: postdate for post: %s came back %s' % (post, date)
			return date
		except UnboundLocalError:
			return ''

	def dattopost(self, nntp, group, days, debug=True):
		n = self.n
		# DEBUG EVERY POSTDATE CALL?!?!?! R U FUKN NUTS LAWL
		pddebug = False
		if debug:
			print 'INFO: Finding article for %s %d days back.' % (group, days)

		data = nntp.group(group)
		goaldate = int(time.time())-(86400*days)
		totalnumberofarticles = data['last'] - data['first']
		upperbound = data['last']
		lowerbound = data['first']
		if debug:
			print 'Total articles: %d Newest: %d Oldest: %d Goal: %d' % (totalnumberofarticles, upperbound, lowerbound, goaldate)
		firstDate = self.postdate(nntp, data['first'], pddebug)
		lastDate = self.postdate(nttp, data['last'], pddebug)

		if goaldate < firstDate:
			print 'WARNING: Backfill target of %d day(s) is older than the first article stored on your news server.' % days
			print 'Starting from the first available article (%s) or %d days.' % (time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(firstDate)), self.daysOld(firstdate))
			return data['first']

		if goaldate > lastdate:
			print 'ERROR: Backfill target of %d day(s) is newer than the last article stored on your news server.' % days
			print 'To backfill this group you need to set BackfillDays to at least %d days (%s).' % (math.ceil(self.daysOld(lastDate)+1), time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(lastDate-86400))) 
			return ''

		if debug:
			print 'DEBUG: Searching for postdate.'
			print 'Goaldate: %d (%s)' % (goaldate, time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(goaldate)))
			print 'Firstdate: %s' % time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(firstDate))
			print 'Lastdate: %s' % time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(lastDate))

		interval = math.floor(upperbound - lowerbound) * 0.5
		dateofnextone = ''
		templowered = ''

		if debug:
			print 'Start: %d' % data['first']
			print 'End: %d' % data['last']
			print 'Interval: %d' % interval

		dateofnextone = lastDate
		# match on days not timestamp to speed things up
		while self.daysOld(dateofnextone) < days:
			while True: 
				tmpdate = self.postdate(nntp, (upperbound-interval), pddebug)
				if tempdate > goaldate:
					break
				upperbound = upperbound - interval
				if debug:
					print 'New upperbound (%d) is %d days old.' % (upperbound, self.daysOld(tmpDate))
			if not templowered:
				interval = math.ceil((interval/2))
				if debug:
					print 'Set interval to %d articles.' % interval
			dateofnextone = self.postdaate(nntp, (upperbound-1), pddebug)
			while not dateofnextone:
				dateofnextone = self.postdate(nntp,(upperbound-1), pddebug)
		print 'Determined to be article %d which is %d days old (%s).' % (upperbound, self.daysold(dateofnextone), time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(dateofnextone)))
		return upperbound

	def daysOld(self, timestamp):
		return round((time.time() - timestamp)/86400, 1)
