#!/usr/bin/env python
from dateutil.parser import parse
import backfill
import groups, helper
import namecleaning
from db import DB
import MySQLdb
import hashlib
import nntplib
import time
import sys
import re

BLACKLIST_FIELD_SUBJECT = 1
BLACKLIST_FIELD_FROM = 2
BLACKLIST_FIELD_MESSAGEID = 3

class Binaries():
	def __init__(self):
		self.n = "\n"
		self.compressedHeaders = False
		self.messagebuffer = 20000
		self.NewGroupScanByDays = False
		self.NewGroupMsgsToScan = 300000 # 5000
		self.NewGroupDaysToScan = 3
		self.DoPartRepair = True
		self.partrepairlimit = 15000

		self.blackLlist = dict()
		self.message = dict()
		self.blackListLoaded = False

	def updateAllGroups(self):
		res = groups.getActive()
		counter = 1
	
		if res:
			alltime = time.time()
			print 'Updating: ', len(res), 'group(s)'
	
			nntp = nntplib.connect()
	
			for groupArr in res:
				message = dict()
				print 'Starting group', counter, 'of', len(res)
				self.updateGroup(nntp, groupArr)
				counter += 1
	
			nntp.quit()
			print 'Updating completed in', int(time.time() - alltime), 'seconds.'
	
		else:
			print 'No groups specified. Ensure groups are added to usepy\'s database for updating.'
	
	def updateGroup(self, nntp, groupArr):
		mdb = DB()
		n = self.n
		b = backfill.Backfill()
		self.startGroup = time.time()

		print 'Processing', groupArr['name']

		data = nntp.group(groupArr['name'])

		if self.DoPartRepair:
			print 'Part repair enabled... Repairing...'
			# self.partRepair(nntp, groupArr)
		else:
			print 'Part repair disabled.... skipping...'

		last = grouplast = data['last']

		# for new newsgroups - determine here how far you want to go back
		if groupArr['last_record'] == 0:
			if data['first'] > data['last'] - self.NewGroupMsgsToScan:
				first = data['first']
			else:
				first = data['last'] - self.NewGroupMsgsToScan
			first_record_postdate = b.postdate(nntp, first, True)
			mdb.query("UPDATE groups SET first_record = %s, first_record_postdate = FROM_UNIXTIME(%s) WHERE ID = %s", (first, first_record_postdate, groupArr['ID']))
		else:
			first = groupArr['last_record'] + 1

		# deactivate empty groups
		if (data['last'] - data['first']) <= 5:
			mdb.query('UPDATE groups SET active = 0, last_updated = now() WHERE ID = %d', (groupArr['ID'],))
	 
		# calculate total number of parts
		total = grouplast - first + 1

		# if total is bigger than 0 it means we have new parts in the newsgroup
		if total > 0:
			print 'Group %s has %d new articles.' % (data['name'], int(total))
			print 'Server oldest: %s Server newest: %s Local newest: %s\n' % (data['first'], data['last'], groupArr['last_record'])
			if groupArr['last_record'] == 0:
				out = self.NewGroupDaysToScan + ' days' if self.NewGroupScanByDays else str(self.NewGroupMsgsToScan) + ' messages'
				print 'New group starting with ', out, 'worth.'

			done = False

			# get all the parts (in portions of self.messagebuffer to use not too much memory)
			while (done == False):
				self.startLoop = time.time()

				if total > self.messagebuffer:
					if (first + self.messagebuffer) > grouplast:
						last = grouplast
					else:
						last = first + self.messagebuffer

				print 'Getting %d articles (%d to %d) from %s - %d in queue.' % ((last-first+1), first, last, data['name'], (grouplast-last))
				sys.stdout.flush()

				# get headers from newsgroup
				lastId = self.scan(nntp, groupArr, first, last)
				if lastId == False:
					# scan filed, skip group
					return
	
				mdb.query("UPDATE groups SET last_record = %s, last_updated = now() WHERE ID = %s", (lastId, groupArr['ID']))
	
				if last == grouplast:
					done = True
				else:
					last = lastId
					first = last +1

			last_record_postdate = b.postdate(nntp, last, False)
			mdb.query('UPDATE groups SET last_record_postdate = FROM_UNIXTIME(%s), last_updated = now() WHERE ID = %s', (last_record_postdate, groupArr['ID']))
			timeGroup = int(time.time() - self.startGroup)
			print data['name'], 'processed in', timeGroup, 'seconds.'
		
		else:
			print 'No new articles for %s (first %d last %d total %d) grouplast %d%s' % (data['name'], first, last, total, groupArr['last_record'], n)

	def scan(self, nntp, groupArr, first, last, stype='update'):
		mdb = DB()
		self.startHeaders = time.time()
		resp, overviews = nntp.over((first, last))

		rangerequested = range(first, last)
		msgsreceived = list()
		msgsblacklisted = list()
		msgsignored = list()
		msgsnotinserted = list()

		timeHeaders = int(time.time() - self.startHeaders)

		self.startCleaning = time.time()
		if type(overviews) is list:
			# loop articles, figure out files/parts
			for msg in overviews:
				try:
					msg[0]
				except IndexError:
					continue

				msgsreceived.append(msg[0])

				# for part count
				pattern = '\((\d+)\/(\d+)\)$'

				# not a binary post most likely.. continue
				try:
					pRegex = re.compile(pattern, re.IGNORECASE)
					matches = pRegex.search(msg[1]['subject'])
					if matches is None:
						continue
				except KeyError:
					continue

				# filter subject based on black/white list
				if self.isBlackListed(msg, groupArr['name']):
					msgsblacklisted.append(msg[0])
					continue

				# attempt to get file count
				cRegex = re.compile('(\[|\(|\s)(\d{1,4})(\/|(\s|_)of(\s|_)|\-)(\d{1,4})(\]|\)|\s)(?!"?$)')
				filecnt = cRegex.search(msg[1]['subject'])
				if filecnt is None:
					filecnt = list()
					filecnt = ['0' for x in range(0,6)]
				else:
					filecnt = [x for x in filecnt.groups()]

				matches = [str(x).strip() for x in matches.groups()]
				if matches[0].isdigit() and matches[0].isdigit():
					subject = re.sub(pattern, '', msg[1]['subject']).strip().encode('utf-8', 'ignore')
					cleansubject = namecleaning.collectionsCleaner(msg[1]['subject'])

					try:
						self.message[subject]
					except KeyError:
						self.message[subject] = msg[1]
						self.message[subject]['MaxParts'] = int(matches[1])
						self.message[subject]['Date'] = parse(self.message[subject]['date']).strftime('%s')
						self.message[subject]['CollectionHash'] = hashlib.md5(cleansubject+msg[1]['from']+str(groupArr['ID'])+str(filecnt[5])).hexdigest()
						self.message[subject]['MaxFiles'] = int(filecnt[5])
						self.message[subject]['File'] = int(filecnt[1])

					if int(matches[0]) > 0:
						try:
							self.message[subject]['Parts']
						except KeyError:
							self.message[subject]['Parts'] = dict()
			
						self.message[subject]['Parts'][int(matches[0])] = {'Message-ID' : msg[1]['message-id'][1:-1], 'number' : msg[0], 'part' : int(matches[0]), 'size' : msg[1][':bytes']}

			timeCleaning = int(time.time() - self.startCleaning)
			try:
				del msg
			except UnboundLocalError:
				pass
			maxnum = last
			rangenotreceived = list(set(rangerequested) - set(msgsreceived))

			if stype != 'partrepair':
				print 'Received ', len(msgsreceived), 'articles of', last-first+1, 'requested,', len(msgsblacklisted), 'blacklisted,', len(msgsignored), 'not binary.'					

			if len(rangenotreceived) > 0:
				if stype == 'backfill':
					''' dont add missing articles'''
				else:
					if self.DoPartRepair:
						self.addMissingParts(rangenotreceived, groupArr['ID'])

				if stype != 'partrepair':
					print 'Server did not return %d articles.' % (len(rangenotreceived))

			self.startUpdate = time.time()
			try:
				len(self.message)
			except NameError:
				pass
			else:
				maxnum = first
				# insert binaries and parts into database. When binaries already exists; only insert new parts
				insPartsStmt = "INSERT IGNORE INTO parts (binaryID, number, messageID, partnumber, size) VALUES (%s, %s, %s, %s, %s)"

				lastCollectionHash = ''
				lastCollectionID = -1
				lastBinaryHash = ''
				lastBinaryID = -1

				mdb.setAutoCommit(False)

				for subject, data in self.message.iteritems():
					collectionHash = data['CollectionHash']
					subject = namecleaning.unfuckString(subject)

					if lastCollectionHash == collectionHash:
						collectionID = lastCollectionID
					else:
						lastCollectionHash = collectionHash
						lastBinaryHash = ''
						lastBinaryID = -1

						cres = mdb.queryOneRow("SELECT ID FROM collections WHERE collectionhash = %s", (collectionHash,))
						if cres is None:
							cleanerName = namecleaning.releaseCleaner(subject)
							csql = "INSERT INTO collections (name, subject, fromname, date, xref, groupID, totalFiles, collectionhash, dateadded) VALUES (%s, %s, %s, FROM_UNIXTIME(%s), %s, %s, %s, %s, now())"
							collectionID = int(mdb.queryInsert(csql, (cleanerName, subject, data['from'], data['Date'], data['xref'], groupArr['ID'], data['MaxFiles'], collectionHash)))
						else:
							collectionID = int(cres['ID'])
							cusql = 'UPDATE collections SET dateadded = now() where ID = %s'
							mdb.queryDirect(cusql, (collectionID,))

						lastCollectionID = collectionID
					binaryHash = hashlib.md5(subject+data['from']+str(groupArr['ID'])).hexdigest()

					if lastBinaryHash == binaryHash:
						binaryID = lastBinaryID
					else:
						lastBinaryHash = binaryHash

						bres = mdb.queryOneRow('SELECT ID FROM binaries WHERE binaryhash = %s', (binaryHash,))
						if bres is None:
							bsql = "INSERT INTO binaries (binaryhash, name, collectionID, totalParts, filenumber) VALUES (%s, %s, %s, %s, %s)"
							binaryID = mdb.queryInsert(bsql, (binaryHash, subject, collectionID, data['MaxParts'], round(data['File'])))
						else:
							binaryID = bres['ID']
						lastBinaryID = binaryID

					for partdata in data['Parts'].values():
						pBinaryID = binaryID
						pMessageID = partdata['Message-ID']
						pNumber = partdata['number']
						pPartNumber = round(partdata['part'])
						pSize = partdata['size']
						maxnum = partdata['number'] if (partdata['number'] > maxnum) else maxnum
						params = (pBinaryID, pNumber, pMessageID, pPartNumber, pSize)
						
						try:
							mdb.query(insPartsStmt, params)
						except MySQLdb.Error, e:
							msgsnotinserted.append(partdata['number'])

				if len(msgsnotinserted) > 0:
					print 'WARNING: %d parts failed to insert.' % len(msgsnotinserted)
					if self.DoPartRepair:
						self.addMissingParts(msgsnotinserted, groupArr['ID'])
				mdb.commit()
				mdb.setAutoCommit(True)
			timeUpdate = int(time.time() - self.startUpdate)
			timeLoop = int(time.time() - self.startLoop)

			if stype != 'partrepair':
				print '%ds to download articles, %ds to clean articles, %d to insert articles, %ds total.\n\n' % (timeHeaders, timeCleaning, timeUpdate, timeLoop)
			data, self.message = None, {}
			return maxnum

		else:
			if stype != 'partrepair':
				print '''Error: can't get parts from server (msgs not dict).'''
				print 'Skipping group.'
				return False

	def partRepair(self, nntp, groupArr):
		n = self.n

		mdb = DB()
		missingParts = mdb.query("SELECT * FROM partrepair WHERE groupID = %d AND attempts < 5 ORDER BY numberID ASC LIMIT %d", (groupArr['ID'], self.partrepairlimit))
		partsRepaired = partsFailed = 0

		if len(missingParts) > 0:
			print 'Attempting to repair %d parts.' % len(missingParts)

			# loop through each part to group into ranges
			ranges = dict()
			lastnum = lastpart = 0
			for part in missingParts:
				if lastnum+1 == part['numberID']:
					ranges[lastpart] = part['numberID']
				else:
					lastpart = part['numberID']
					ranges[lastpart] = part['numberID']
				lastnum = part['numberID']

			num_attempted = 0

			# download missing parts in ranges.
			for partfrom, partto in ranges.iteritems():
				self.startLoop = time.time()

				num_attempted += partto - partfrom + 1
				# print some output here

				# get article from newsgroup
				self.scan(nntp, groupArr, partfrom, partto, 'partrepair')

				# check if articles were added
				articles = ','.join("%d" % i for i in range(partfrom, partto))
				sql = "SELECT pr.ID, pr.numberID, p.number from partrepair pr LEFT JOIN parts p ON p.number = pr.numberID WHERE pr.groupID=%d AND pr.numberID IN (%s) ORDER BY pr.numberID ASC"

				result = mdb.queryDirect(sql, (groupArr['ID'], articles))
				for r in result:
					try:
						if r['number'] == r['numberID']:
							partsRepaired += 1

							# article was added, delete from partrepair
							mdb.query('DELETE FROM partrepair WHERE ID=%s', (r['ID'],))
					except KeyError:
						partsFailed += 1

						# article was not added, increment attempts:
						mdb.query('UPDATE partrepair SET attempts=attempts+1 WHERE ID = %s', (r['ID'],))

			print n
			print '%d parts repaired.' % (partsRepaired)

		# remove articles that we can't fetch after 5 attempts
		mdb.query('DELETE FROM partrepair WHERE attempts >= 5 AND groupID = %s', (groupArr['ID'],))

	def addMissingParts(self, numbers, groupID):
		mdb = DB()
		insertStr = 'INSERT INTO partrepair (numberID, groupID) VALUES '
		for number in numbers:
			insertStr += '(%s, %s), ' % (number, groupID)
		insertStr = insertStr[0:-2]
		insertStr += ' ON DUPLICATE KEY UPDATE attempts=attempts+1'
		return mdb.queryInsert(insertStr, None, False)

	def retrieveBlackList(self):
		if self.blackListLoaded:
			return self.blackList
		blackList = self.getBlacklist(True)
		self.blackList = blackList
		self.blackListLoaded = True
		return blackList

	def isBlackListed(self, msg, groupName):
		blackList = self.retrieveBlackList()
		field = dict()
		msg = msg[1]
		if 'Subject' in msg.keys():
			field[BLACKLIST_FIELD_SUBJECT] = msg['Subject']
		if 'From' in msg.keys():
			field[BLACKLIST_FIELD_FROM] = msg['From']
		if 'Message-ID' in msg.keys():
			field[BLACLIST_FIELD_MESSAGEID] = msg['Message-ID']

		omitBinary = False

		for blist in blackList:
			if re.search('/^'+blist['groupname']+'$/', groupName, re.IGNORECASE) != None:
				if blist['optype'] == 1:
					if re.search('/'+blist['regex']+'/', field[blist['msgcol']], re.IGNORECASE) != None:
						omitBinary = True
				elif blist['optype'] == 2:
					if re.search('/'+blist['regex']+'/', field[blist['msgcol']], re.IGNORECASE) == None:
						omitBinary = True

		return omitBinary

	def search(self, search, limit=1000, excludedcats={}):
		mdb = DB()

		# if the query starts with a ^ it indicates the search is looking for items which start with the term
		# still do the like match, but mandate that all items returned must start with the provided word

		words = search.split(' ')
		searchsql = ''
		intwordcount = 0
		if len(words) > 0:
			for word in words:
				# see if the first word has a caret, which indicates search must start with term
				if intwordcount == 0 and word[0] == '^':
					searchsql += ' and b.name like %s%' % (mdb.escapeString(word[1:]))
				else:
					searchsql += ' and b.name like %s' % (mdb.escapeString('%'+word+'%'))

				intwordcount += 1

		exccatlist = ''
		if len(excludedcats) > 0:
			exccatlist = 'and b.categoryID not in ('+','.join(excludedcats)+') '

		res = mdb.query('''SELECT b.*, g.name AS group_name, r.guid,
					(SELECT COUNT(ID) FROM parts p where p.binaryID = b.ID) as 'binnum'
					FROM binaries b
					INNER JOIN groups g ON g.ID = b.groupID
					LEFT OUTER JOIN releases r ON r.ID = b.releaseID
					WHERE 1=1 %s %s order by DATE DESC LIMIT %d ''', (searchsql, exccatlist, limit))

		return res

	def getForReleaseId(self, id):
		mdb = DB()
		return mdb.query('SELECT binaries.* from binaries where releaseID = %s order by relpart', (id,))

	def getById(self, id):
		mdb = DB()
		return mdb.queryOneRow('select binaries.*, collections.groupID, groups.name as groupname from binaries, collections left outer join groups on collections.groupID = groups.ID where binaries.ID = %d', (id,))

	def getBlacklist(self, activeonly=True):
		mdb = DB()
		where = ''

		if activeonly:
			where = ' where binaryblacklist.status = 1 '
		else:
			where = ''

		return mdb.query('SELECT binaryblacklist.ID, binaryblacklist.optype, binaryblacklist.status, binaryblacklist.description, binaryblacklist.groupname AS groupname, \
			binaryblacklist.regex, groups.ID AS groupID, binaryblacklist.msgcol FROM binaryblacklist \
			left outer JOIN groups ON groups.name = binaryblacklist.groupname'+where+'ORDER BY coalesce(groupname, "zzz")')

	def getBlacklistByID(self, id):
		mdb = DB()
		return mdb.queryOneRow('select * from binaryblacklist where ID = %s', (id,))

	def deleteBlacklist(self, id):
		mdb = DB()
		return mdb.query('delete from binaryblacklist where ID = %s', (id,))

	def updateBlacklist(self, regex):
		mdb = DB()

		groupname = regex['groupname']
		if groupname == '':
			groupname = 'null'
		else:
			groupname = re.sub('a\.b\.' 'alt.binaries.', groupname, re.IGNORECASE)
			groupname = mdb.escapeString(groupname)

		mdb.query("update binaryblacklist set groupname=%s, regex=%s, status=%d, description=%s, optype=%d, msgcol=%d where ID = %d ",
			(groupname, regex['regex'], regex['description'], regex['optype'], regex['msgcol'], regex['id']))

	def addBlacklist(self, regex):
		mdb = DB()

		groupname = regex['groupname']
		if groupname == '':
			groupname = 'null'
		else:
			groupname = re.sub('a\.b\.' 'alt.binaries.', groupname, re.IGNORECASE)
			groupname = mdb.escapeString(groupname)

		return mdb.queryInsert("insert into binaryblacklist (groupname, regex, status, description, optype, msgcol) values (%s, %s, %d, %s, %d, %d) ",
			(regex['regex'], regex['status'], regex['description'], regex['optype'], regex['msgcol']))

	def delete(self, id):
		mdb = DB()
		bins = mdb.query('SELECT ID FROM binaries WHERE collectionID = %d', (id,))
		for bin in bins:
			mdb.query('delete from parts where binaryID = %d', (bin['ID']))
		mdb.query('delete from binaries where collectionID = %d', (id,))
		mdb.query('delete from collections where ID = %d', (id,))
