#!/usr/bin/env python
from dateutil.parser import parse
import groups, helper
import namecleaning
from db import DB
import MySQLdb
import hashlib
import nntplib
import time
import sys
import re

class Binaries():
	def __init__(self):
		self.n = "\n"
		self.compressedHeaders = False
		self.messagebuffer = 20000
		self.NewGroupScanByDays = False
		self.NewGroupMsgsToScan = 10 # 5000
		self.NewGroupDaysToScan = 3
		self.DoPartRepair = False
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
			# first_record_postdate = backfill.postdate(nntp, first, False)
			# mdb.query(update groups)
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
	
				# mdb.query('UPDATE groups SET last_record blah
	
				if last == grouplast:
					done = True
				else:
					last = lastId
					first = last +1

			#last_record_postdate = backfill.postdate(nntp, last, False)
			# mdb.query('UPDATE GROUPS balh
			timeGroup = int(time.time() - self.startGroup)
			print data['name'], 'processed in', timeGroup, 'seconds.'
		
		else:
			print 'No new articles for %s (first %d last %d total %d) grouplast %d' % (data['name'], first, last, total, groupArr['last_record'])

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
				#if self.isBlackListed(msg, groupArr['name']):
					#msgsblacklisted.append(msg[0])
					#continue

				# attempt to get file count
				cRegex = re.compile('(\[|\(|\s)(\d{1,4})(\/|(\s|_)of(\s|_)|\-)(\d{1,4})(\]|\)|\s)(?!"?$)')
				filecnt = cRegex.search(msg[1]['subject'])
				filecnt = [x for x in filecnt.groups()]
				if filecnt is None:
					filecnt = list()
					filecnt[1] = '0'
					filecnt[5] = '0'

				matches = [str(x).strip() for x in matches.groups()]
				if matches[0].isdigit() and matches[0].isdigit():
					subject = re.sub(pattern, '', msg[1]['subject']).strip().encode('utf-8', 'ignore')
					cleansubject = namecleaning.collectionsCleaner(msg[1]['subject'])

					# if msg['subject']:
					self.message[subject] = msg[1]
					self.message[subject]['MaxParts'] = int(matches[1])
					self.message[subject]['Date'] = parse(self.message[subject]['date']).strftime('%s')
					self.message[subject]['CollectionHash'] = hashlib.md5(cleansubject+msg[1]['from']+str(msg[0])+str(filecnt[5])).hexdigest()
					self.message[subject]['MaxFiles'] = int(filecnt[5])
					self.message[subject]['File'] = int(filecnt[1])

					if int(matches[0]) > 0:
						self.message[subject]['Parts'] = dict()
						self.message[subject]['Parts'][int(matches[0])] = {'Message-ID' : msg[1]['message-id'][1:-1], 'number' : msg[0], 'part' : int(matches[0]), 'size' : msg[1][':bytes']}

			timeCleaning = int(time.time() - self.startCleaning)
			del msg
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
							collectionID = mdb.queryInsert(csql, (cleanerName, subject, data['from'], data['Date'], data['xref'], groupArr['ID'], data['MaxFiles'], collectionHash))
						else:
							collectionID = cres['ID']
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


