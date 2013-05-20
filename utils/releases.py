#!/usr/bin/env python
from time import gmtime, strftime
import sites, db, re, page, os
import consoletools
import time
import groups
import nzb
import namecleaning
import category

class Releases():
	def __init__(self):
		self.PASSWD_NONE = 0
		self.PASSWD_POTENTIAL = 1
		self.PASSWD_RAR = 2
		s = sites.Sites()
		self.site = s.get()
		try:
			self.stage5limit = self.site['maxnzbsprocessed']
		except KeyError:
			self.site['maxnzbsprocessed'] = 1000
		try:
			self.completion = self.site['releasecompletion']
		except KeyError:
			self.site['releasecompletion'] = 0
		try:
			self.crosspostt = self.site['crossposttime']
		except KeyError:
			self.site['crosspostttime'] = 2
		try:
			if self.site['grabstatus'] == 0:
				self.updategrabs = False
			else:
				self.updategrabs = True
		except KeyError:
			slef.updategrabs = False

	def get(self):
		mdb = db.DB()
		return mdb.query('select releases.*, g.name as group_name, c.title as category_name  from releases left outer join category c on c.ID = releases.categoryID left outer join groups g on g.ID = releases.groupID')

	def getRange(self, start, num):
		mdb = db.DB()
		if start == False:
			limit = ''
		else:
			limit = ' LIMIT %s,%s' % (str(start), str(num))
		return mdb.query(' SELECT releases.*, concat(cp.title, ' > ', c.title) as category_name from releases left outer join category c on c.ID = releases.categoryID left outer join category cp on cp.ID = c.parentID order by postdate desc'+limit)

	def getBrowseCount(self, cat, maxage=-1, excludedcats=list(), grp=''):
		mdb = db.DB()
		catsrch = ''
		if len(cat) > 0 and cat[0] != -1:
			catsrch = ' and ('
			for category in cat:
				if category != -1:
					categ = category.Category()
					if categ.isParent(category):
						children = categ.getChildren(category)
						chlist = '-99'
						for child in children:
							chlist += ', '+child['ID']
						if chlist != '-99':
							catsrch += ' releases.categoryID in ('+chlist+') or '
					else:
						catsrc += ' releases.categoryID = %d or ' % (category)
			catsrc += '1=1 )'

		if maxage > 0:
			maxage = ' and postdate > now() - interval %d day ' % maxage
		else:
			maxage = ''

		grpsql = ''
		if grp != '':
			grpsql = ' and groups.name = %s ' % mdb.escapeString(grp)
		exccatlist = ''
		if len(excludedcats) > 0:
			exccatlist = ' and categoryID not in ('+','.join(excludedcats)+')'

		res = mdb.queryOneRow("select count(releases.ID) as num from releases left outer join groups on groups.ID = releases.groupID where releases.passwordstatus <= (select value from site where setting='showpasswordedrelease') %s %s %s %s", (catsrch, maxage, exccatlist, grpsql))
		return res['num']

	def getBrowseRange(self, cat, start, num, orderby, maxage=-1, excludedcats=list(), grp=''):
		mdb = db.DB()
		catsrch = ''
		if len(cat) > 0 and cat[0] != -1:
			catsrch = ' and ('
			for category in cat:
				if category != -1:
					categ = category.Category()
					if categ.isParent(category):
						children = categ.getChildren(category)
						chlist = '-99'
						for child in children:
							chlist += ', '+child['ID']
						if chlist != '-99':
							catsrch += ' releases.categoryID in ('+chlist+') or '
					else:
						catsrc += ' releases.categoryID = %d or ' % (category)
			catsrc += '1=1 )'

		if maxage > 0:
			maxage = ' and postdate > now() - interval %d day ' % maxage
		else:
			maxage = ''

		grpsql = ''
		if grp != '':
			grpsql = ' and groups.name = %s ' % mdb.escapeString(grp)

		exccatlist = ''
		if len(excludedcats) > 0:
			exccatlist = ' and categoryID not in ('+','.join(excludedcats)+')'

		order = self.getBrowseOrder(orderby)
		return mdb.query(" SELECT releases.*, concat(cp.title, ' > ', c.title) as category_name, concat(cp.ID, ',', c.ID) as category_ids, groups.name as group_name, rn.ID as nfoID, re.releaseID as reID from releases left outer join groups on groups.ID = releases.groupID left outer join releasevideo re on re.releaseID = releases.ID left outer join releasenfo rn on rn.releaseID = releases.ID and rn.nfo is not null left outer join category c on c.ID = releases.categoryID left outer join category cp on cp.ID = c.parentID where releases.passwordstatus <= (select value from site where setting='showpasswordedrelease') %s %s %s %s order by %s %s", (limit, catsrch, maxagesql, exccatlist, grpsql, order[0], order[1]))

	def getBrowseOrder(self, orderby):
		order = 'posted_desc' if orderby == '' else orderby
		orderArr = order.split('_')

		if orderArr[0] == 'cat':
			orderfield = 'categeoryID'
		elif orderArr[0] == 'name':
			orderfield = 'searchname'
		elif orderArr[0] == 'size':
			orderfield = 'size'
		elif orderArr[0] == 'files':
			orderfield = 'totalpart'
		elif orderArr[0] == 'stats':
			orderfield = 'grabs'
		elif orderArr[0] == 'posted':
			orderfield = 'posted'
		else:
			orderfield = 'postdate'

		try:
			ordersort = orderArr[1] if orderArr[1] and re.search('^asc|desc$', orderArr[1], re.IGNORECASE) else 'desc'
		except IndexError:
			ordersort = 'desc'
		return [orderfield, ordersort]

	def getBrowseOrdering(self):
		return ['name_asc', 'name_desc', 'cat_asc', 'cat_desc', 'posted_asc', 'posted_desc', 'size_asc', 'size_desc', 'files_asc', 'files_desc', 'stats_asc', 'stats_desc']

	def getForExport(self, postfrom, postto, group):
		mdb = db.DB()
		if postfrom != '':
			dateparts = postfrom.split('/')
			if len(dateparts) == 3:
				postfrom = ' and postdate > %s ' % (mdb.escapeString(dateparts[2]+'-'+dateparts[1]+'-'+dateparts[0]+' 00:00:00'))
			else:
				postfrom = ''

		if postto != '':
			dateparts = postto.split('/')
			if len(dateparts) == 3:
				postto = ' and postdate < %s ' % (mdb.escapeString(dateparts[2]+'-'+dateparts[1]+'-'+dateparts[0]+' 23:59:59'))
			else:
				postto = ''

		if group != '' and group != '-1':
			group = ' and groupID = %d ' % group
		else:
			group = ''

		return mdb.query("SELECT searchname, guid, CONCAT(cp.title,'_',category.title) as catName FROM releases INNER JOIN category ON releases.categoryID = category.ID LEFT OUTER JOIN category cp ON cp.ID = category.parentID where 1 = 1 %s %s %s", (postfrom, postto, group))

	def getEarliestUsenetPostDate(self):
		mdb = db.DB()
		row = mdb.queryOneRow("SELECT DATE_FORMAT(min(postdate), '%d/%m/%Y') as postdate from releases")
		return row['postdate']

	def getLatestUsenetPostDate(self):
		mdb = db.DB()
		row = mdb.queryOneRow("SELECT DATE_FORMAT(max(postdate), '%d/%m/%Y') as postdate from releases")
		return row['postdate']

	def getReleasedGroupsForSelect(self, b1nIncludeAll = True):
		mdb = db.DB()
		groups = mdb.query("select distinct groups.ID, groups.name from releases inner join groups on groups.ID = releases.groupID")
		tmp_list = dict()

		if b1nIncludeAll:
			tmp_list[-1] = '--All Groups--'

		for group in groups:
			tmp_list[group['ID']] = group['name']

		return tmp_list

	def getCount(self):
		mdb = db.DB()
		res = mdb.queryOneRow("select count(ID) as num from releases")
		return res['num']

	def categorizeRelease(self, type, where = '', echo = False):
		mdb = db.DB()
		cat = category.Category()
		ct = consoletools.Consoletools()
		relcount = 0

		resrel = mdb.queryDirect("SELECT ID, "+type+", groupID FROM releases "+where)
		for rowrel in resrel:
			catId = cat.determineCategory(rowrel['type'], rowrel['groupID'])
			mdb.queryDirect("UPDATE releases SET categoryID = %s, relnamestatus = 1 WHERE ID = %s", (catId, rowrel['ID']))
			relcount += 1
			if echo == True:
				ct.overWrite('Categorizing:'+ct.percentString(relcount, len(resrel)))

		return relcount

	def processReleasesStage1(self, groupID):
		mdb = db.DB()
		c = consoletools.Consoletools()
		n = '\n'

		print 'Stage 1 -> Try to find complete collections.'
		stage1 = time.time()
		where = ' AND groupID = %s' % groupID if groupID else ''

		# look if we have all the files in a collection (which have the file count in the subject). Set filecheck to 1
		mdb.query("UPDATE collections SET filecheck = 1 WHERE ID IN (SELECT ID FROM (SELECT c.ID FROM collections c LEFT JOIN binaries b ON b.collectionID = c.ID WHERE c.totalFiles > 0 AND c.filecheck = 0"+where+" GROUP BY c.ID, c.totalFiles HAVING count(b.ID) >= c.totalFiles) as tmpTable)")
		
		# attempt to split bundled collections
		mdb.query("UPDATE collections SET filecheck = 10 WHERE ID IN (SELECT ID FROM (SELECT c.ID FROM collections c LEFT JOIN binaries b ON b.collectionID = c.ID WHERE c.totalFiles > 0 AND c.dateadded < (now() - interval 20 minute) AND c.filecheck = 0"+where+" GROUP BY c.ID, c.totalFiles HAVING count(b.ID) > c.totalFiles+2) as tmpTable)")
		self.splitBunchedCollections()

		# set filecheck to 16 if theres a file that starts with 0
		mdb.query("UPDATE collections c SET filecheck = 16 WHERE ID IN (SELECT ID FROM (SELECT c.ID FROM collections c LEFT JOIN binaries b ON b.collectionID = c.ID WHERE c.totalFiles > 0 AND c.filecheck = 1 AND b.filenumber = 0"+where+" GROUP BY c.ID) as tmpTable)")

		# set filecheck to 15 on everything left over
		mdb.query('UPDATE collections set filecheck = 15 where filecheck = 1')

		# if we have all the parts set partcheck to 1
		if not groupID:
			# if filecheck 15, check if we have all the files then set part check.
			mdb.query("UPDATE binaries b SET partcheck = 1 WHERE b.ID IN (SELECT p.binaryID FROM parts p, collections c WHERE p.binaryID = b.ID AND b.partcheck = 0 AND c.filecheck = 15 AND c.id = b.collectionID GROUP BY p.binaryID HAVING count(p.ID) = b.totalParts)")
			# if filecheck 16, check if we have all the files+1(because of the 0) then set part check
			mdb.query("UPDATE binaries b SET partcheck = 1 WHERE b.ID IN (SELECT p.binaryID FROM parts p, collections c WHERE p.binaryID = b.ID AND b.partcheck = 0 AND c.filecheck = 16 AND c.id = b.collectionID GROUP BY p.binaryID HAVING count(p.ID) >= b.totalParts+1)")
		else:
			mdb.query("UPDATE binaries b SET partcheck = 1 WHERE b.ID IN (SELECT p.binaryID FROM parts p ,collections c WHERE p.binaryID = b.ID AND b.partcheck = 0 AND c.filecheck = 15 AND c.id = b.collectionID and c.groupID = "+groupID+" GROUP BY p.binaryID HAVING count(p.ID) = b.totalParts )")
			mdb.query("UPDATE binaries b SET partcheck = 1 WHERE b.ID IN (SELECT p.binaryID FROM parts p ,collections c WHERE p.binaryID = b.ID AND b.partcheck = 0 AND c.filecheck = 16 AND c.id = b.collectionID and c.groupID = "+groupID+" GROUP BY p.binaryID HAVING count(p.ID) >= b.totalParts+1 )")

		# set file check to 2 if we have all the parts
		mdb.query("UPDATE collections SET filecheck = 2 WHERE ID IN (SELECT ID FROM (SELECT c.ID FROM collections c LEFT JOIN binaries b ON c.ID = b.collectionID WHERE b.partcheck = 1 AND c.filecheck = 1 GROUP BY c.ID, c.totalFiles HAVING count(b.ID) >= c.totalFiles) as tmp)")

		# if a collection has not been updated in two hours, set filecheck to 2
		mdb.query("UPDATE collections c SET filecheck = 2, totalFiles = (SELECT COUNT(b.ID) FROM binaries b WHERE b.collectionID = c.ID) WHERE c.dateadded < (now() - interval 2 hour) AND c.filecheck < 2 "+where)

		print c.convertTime(int(time.time() - stage1))

	def processReleasesStage2(self, groupID):
		mdb = db.DB()
		c = consoletools.Consoletools()
		n = '\n'
		where = ' AND groupID = %s' % groupID if groupID else ''

		print 'Stage 2 -> Get the size in bytes of the collection.'

		stage2 = time.time()
		# get the total size in bytes of the collection for collections where filecheck = 2
		mdb.query("UPDATE collections c SET filesize = (SELECT SUM(size) FROM parts p LEFT JOIN binaries b ON p.binaryID = b.ID WHERE b.collectionID = c.ID), c.filecheck = 3 WHERE c.filecheck = 2 AND c.filesize = 0 "+where)

		print c.convertTime(int(time.time() - stage2))

	def processReleasesStage3(self, groupID):
		mdb = db.DB()
		c = consoletools.Consoletools()
		n = '\n'
		minsizecounts = 0
		maxsizecounts = 0
		minfilecounts = 0

		print 'Stage 3 -> Delete collections smaller/larger than minimum size/file count from group/site setting.'

		stage3 = time.time()

		if groupID == '':
			groupIDs = groups.getActiveIDs()

			for groupID in groupIDs:
				if mdb.queryDirect("SELECT ID from collections where filecheck = 3 and filesize > 0"):
					mdb.query("UPDATE collections c LEFT JOIN (SELECT g.ID, coalesce(g.minsizetoformrelease, s.minsizetoformrelease) as minsizetoformrelease FROM groups g INNER JOIN ( SELECT value as minsizetoformrelease FROM site WHERE setting = 'minsizetoformrelease' ) s ) g ON g.ID = c.groupID SET c.filecheck = 5 WHERE g.minsizetoformrelease != 0 AND c.filecheck = 3 AND c.filesize < g.minsizetoformrelease and c.filesize > 0 AND groupID = "+str(int(groupID["ID"])))
					
					minsizecount = mdb.getAffectedRows()
					if minsizecount < 0:
						minsizecount = 0
					minsizecounts = minsizecount+minsizecounts

					maxfilesizeres = mdb.queryOneRow("select value from site where setting = 'maxsizetoformrelease'")
					if maxfilesizeres['value'] != 0:
						mdb.query("UPDATE collections SET filecheck = 5 WHERE filecheck = 3 AND groupID = %s AND filesize > %s " % (str(int(groupID['ID'])), str(int(maxfilesizeres['value']))))

						maxsizecount = mdb.getAffectedRows()
						if maxsizecount < 0:
							maxsizecount = 0
						maxsizecounts = maxsizecount+maxsizecounts

					mdb.query("UPDATE collections c LEFT JOIN (SELECT g.ID, coalesce(g.minfilestoformrelease, s.minfilestoformrelease) as minfilestoformrelease FROM groups g INNER JOIN ( SELECT value as minfilestoformrelease FROM site WHERE setting = 'minfilestoformrelease' ) s ) g ON g.ID = c.groupID SET c.filecheck = 5 WHERE g.minfilestoformrelease != 0 AND c.filecheck = 3 AND c.totalFiles < g.minfilestoformrelease AND groupID = "+str(int(groupID["ID"])))
					
					minfilecount = mdb.getAffectedRows()
					if minfilecount < 0:
						minfilecount = 0
					minfilecounts = minfilecounts+minfilecount
		else:
			if mdb.queryDirect("SELECT ID from collections where filecheck = 3 and filesize > 0"):
				mdb.query("UPDATE collections c LEFT JOIN (SELECT g.ID, coalesce(g.minsizetoformrelease, s.minsizetoformrelease) as minsizetoformrelease FROM groups g INNER JOIN ( SELECT value as minsizetoformrelease FROM site WHERE setting = 'minsizetoformrelease' ) s ) g ON g.ID = c.groupID SET c.filecheck = 5 WHERE g.minsizetoformrelease != 0 AND c.filecheck = 3 AND c.filesize < g.minsizetoformrelease and c.filesize > 0 AND groupID = "+groupID)

				minsizecount = mdb.getAffectedRows()
				if minsizecount < 0:
					minsizecount = 0
				minsizecounts = minsizecount+minsizecounts
				maxfilesizeres = mdb.queryOneRow("select value from site where setting = maxsizetoformrelease")

				if maxfilesizeres['value'] != 0:
					mdb.query("UPDATE collections SET filecheck = 5 WHERE filecheck = 3 AND groupID = %d AND filesize > %d " % (groupID['ID'], maxfilesizeres['value']))
					maxsizecount = mdb.getAffectedRows()
					if maxsizecount < 0:
						maxsizecount = 0
					maxsizecounts = maxsizecount+maxsizecounts
					mdb.query("UPDATE collections c LEFT JOIN (SELECT g.ID, coalesce(g.minfilestoformrelease, s.minfilestoformrelease) as minfilestoformrelease FROM groups g INNER JOIN ( SELECT value as minfilestoformrelease FROM site WHERE setting = 'minfilestoformrelease' ) s ) g ON g.ID = c.groupID SET c.filecheck = 5 WHERE g.minfilestoformrelease != 0 AND c.filecheck = 3 AND c.totalFiles < g.minfilestoformrelease AND groupID = "+groupID["ID"])
				
				minfilecount = mdb.getAffectedRows()

				if minfilecount < 0:
					minfilecount = 0
				minfilecounts = minfilecounts+minefilecount
		delcount = minsizecounts+maxsizecounts+minfilecounts
		if delcount > 0:
			print '...Deleted %d collections smaller/larger than group/site settings.' % (delcount)

		print c.convertTime(int(time.time() - stage3))

	def processReleasesStage4(self, groupID):
		mdb = db.DB()
		c = consoletools.Consoletools()
		n = '\n'
		retcount = 0
		where = ' AND groupID = %s' % groupID if not groupID else ''

		print n+'Stage 4 -> Create releases.'
		stage4 = time.time()

		rescol = mdb.queryDirect("SELECT * FROM collections WHERE filecheck = 3 AND filesize > 0 " + where + " LIMIT 1000")
		if rescol:
			for rowcol in rescol:
				cleanArr = '#@$%^'+chr(214)+chr(169)+chr(167)
				cleanSearchName = rowcol['name'].translate(string.maketrans('', ''), cleanArr)
				cleanRelName = rowcol['subject'].translate(string.maketrans('', ''), cleanArr)
				relguid = hashlib.md5(str(uuid.uuid1())).hexdigest()
				if mdb.queryInsert("INSERT INTO releases (name, searchname, totalpart, groupID, adddate, guid, rageID, postdate, fromname, size, passwordstatus, haspreview, categoryID, nfostatus) \
							VALUES (%s, %s, %d, %d, now(), %s, -1, %s, %s, %s, %d, -1, 7010, -1)", (cleanrelName, cleanSearchName, rowcol['totalFiles'], rowcol['groupID'], relguid, rowcol['date'], rowcol['fromname'], \
							rowcol['filesize'], 0)):
					relid = mdb.getInsertID()
					# udpate collections table to say we inserted the release
					mdb.queryDirect("UPDATE collections SET filecheck = 4, releaseID = %d WHERE ID = %d", (relid, rowcol['ID']))
					retcount += 1
					print 'Added release %s.' % cleanRelName
				else:
					print 'Error inserting release: %s' % cleanRelName

		timing = c.convertTime(int(time.time() - stage4))
		print '%d releases added in %s' % (retcount, timing)
		return retcount

	def processReleasesStage4_loop(self, groupID):
		tot_retcount = 0

		while tot_retcount > 0:
			retcount = self.processReleasesStage4(groupID)
			tot_retcount = tot_retcount + retcount

		return tot_retcount

	def processReleasesStage4dot5(self, groupID):
		mdb = db.DB()
		c = consoletools.Consoletools()
		n = '\n'
		minsizecount = 0
		maxsizecount = 0
		minfilecount = 0

		print 'Stage 4.5 -> Delete releases smaller/larger than the minimum size/file count from group/site settings.'
		stage4dot5 = time.time()

		if groupID == '':
			groupIDs = groups.getActiveIDs()
			for groupID in groupIDs:
				resrel = mdb.query("SELECT r.ID, r.guid FROM releases r LEFT JOIN \
							(SELECT g.ID, coalesce(g.minsizetoformrelease, s.minsizetoformrelease) \
							as minsizetoformrelease FROM groups g INNER JOIN ( SELECT value as minsizetoformrelease \
							FROM site WHERE setting = 'minsizetoformrelease' ) s ) g ON g.ID = r.groupID WHERE \
							g.minsizetoformrelease != 0 AND r.size < minsizetoformrelease AND groupID = "+str(int(groupID["ID"])))
				if resrel:
					for rowrel in resrel:
						self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
						minsizecount += 1
				maxfilesizeres = mdb.queryOneRow("SELECT value FROM site WHERE setting = 'maxsizetoformrelease'")
				if maxfilesizeres['value'] != 0:
					# where did they get filesize column from? 
					resrel = mdb.query("SELECT ID, guid from releases where groupID = %s AND size > %s " % (str(int(groupID["ID"])), str(int(maxfilesizeres["value"]))))
					if resrel:
						for rowrel in resrel:
							self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
							maxsizecount += 1

				resrel = mdb.query("SELECT r.ID, r.guid FROM releases r LEFT JOIN \
							(SELECT g.ID, coalesce(g.minfilestoformrelease, s.minfilestoformrelease) \
							as minfilestoformrelease FROM groups g INNER JOIN ( SELECT value as minfilestoformrelease \
							FROM site WHERE setting = 'minfilestoformrelease' ) s ) g ON g.ID = r.groupID WHERE \
							g.minfilestoformrelease != 0 AND r.totalpart < minfilestoformrelease AND groupID = "+str(int(groupID["ID"])))
				if resrel:
					for rowrel in resrel:
						self.fastDelete(rowrel['ID'], rowrel['guide'], self.site)
						minfilecount += 1
		else:
			resrel = mdb.query("SELECT r.ID FROM releases r LEFT JOIN \
						(SELECT g.ID, guid, coalesce(g.minsizetoformrelease, s.minsizetoformrelease) \
						as minsizetoformrelease FROM groups g INNER JOIN ( SELECT value as minsizetoformrelease \
						FROM site WHERE setting = 'minsizetoformrelease' ) s ) g ON g.ID = r.groupID WHERE \
						g.minsizetoformrelease != 0 AND r.size < minsizetoformrelease AND groupID = "+groupID)
			if resrel:
				for rowrel in resrel:
					self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
					minsizecount += 1

			maxfilesizeres = mdb.query("SELECT value FROM site WHERE setting = maxsizetoformrelease")
			if maxfilesizeres['value'] != 0:
				resrel = mdb.query("SELECT ID, guid from releases where groupID = %d AND filesize > %d " % (groupID, maxfilesizeres["value"]))
				if resrel:
					for rowrel in resrel:
						self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
						maxsizecount += 1

			resrel = mdb.query("SELECT r.ID, guid FROM releases r LEFT JOIN \
						(SELECT g.ID, coalesce(g.minfilestoformrelease, s.minfilestoformrelease) \
						as minfilestoformrelease FROM groups g INNER JOIN ( SELECT value as minfilestoformrelease \
						FROM site WHERE setting = 'minfilestoformrelease' ) s ) g ON g.ID = r.groupID WHERE \
						g.minfilestoformrelease != 0 AND r.totalpart < minfilestoformrelease AND groupID = "+groupID)
			if resrel:
				for rowrel in resrel:
					self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
					minfilecount += 1

		delcount = minsizecount + maxsizecount + minfilecount
		if delcount > 0:
			print '...Deleted %d releases smaller/larger than group/site settings.' % (delcount)
		print c.convertTime(int(time.time() - stage4dot5))

	def processReleasesStage5(self, groupID):
		mdb = db.DB()
 		nzbs = nzb.NZB()
		c = consoletools.Consoletools()
		n = '\n'
		nzbcount = 0
		where = ' AND groupID = %s' % groupID if groupID else ''

		# create nzb.
		print 'Stage 5 -> Create the NZB, mark collections as ready for deletion.'
		stage5 = time.time()

		start_nzbcount = nzbcount
		resrel = mdb.queryDirect("SELECT ID, guid, name, categoryID FROM releases WHERE nzbstatus = 0 "+where+" LIMIT "+self.stage5limit)
		if resrel:
			for rowrel in resrel:
				if nzb.writeNZBforReleaseId(rowrel['ID'], rowrel['guid'], rowrel['name'], rowrel['categoryID'], nzb.getNZBPath(rowrel['guid'], page.site().nzbpath, True, page.site().nzbsplitlevel)):
					mdb.queryDirect("UPDATE releases SET nzbstatus = 1 WHERE ID = %s", (rowrel['ID'],))
					mdb.queryDirect("UPDATE collections SET filecheck = 5 WHERE releaseID = %s", (rowrel['ID'],))
					nzbcount += 1
					c.overWrite('Creating NZBs:'+c.percentString(nzbcount,len(resrel)))

		timing = c.convertTime(int(time.time() - stage5))
		print n+'%d NZBs created in %s.' % (nzbcount, timing)
		return nzbcount

	def processReleasesStage5_loop(self, groupID):
		tot_nzbcount = 0
		nzbcount = 1
		while nzbcount > 0:
			nzbcount = self.processReleasesStage5(groupID)
			tot_nzbcount = tot_nzbcount + nzbcount

		return tot_nzbcount

	def processReleasesStage6(self, categorize, postproc, groupID):
		mdb = db.DB()
		c = consoletools.Consoletools()
		n = '\n'
		where = ' WHERE relnamestatus = 0 AND groupID = %s' % groupID if groupID else 'WHERE relnamestatus = 0'

		# categorize releases
		print 'Stage 6 -> Categorize and post process releases.'
		stage6 = time.time()
		if categorize == 1:
			self.categorizeRelease('name', where)
		if postproc == 1:
			#pp = postprocess.PostProcess(True)
			#pp.processAll()
			print 'Postprocessing not completed.'
		else:
			print 'Post-processing disabled.'+n
		print c.convertTime(int(time.time() - stage6))

	def processReleasesStage7(self, groupID):
		mdb = db.DB()
		cat = category.Category()
		console = consoletools.Consoletools()
		n = '\n'
		remcount = 0
		passcount = 0
		dupecount = 0
		relsizecount = 0
		completioncount = 0
		disabledcount = 0

		where = ' AND collections.groupID = %s' % groupID if groupID else ''

		# delete old releases and finished collections

		print n+'Stage 7 -> Delete old releases, finished collections and passworded releases.'
		stage7 = time.time()

		# old collections that were missed somehow
		mdb.queryDirect("DELETE collections, binaries, parts \
						FROM collections LEFT JOIN binaries ON collections.ID = binaries.collectionID LEFT JOIN parts on binaries.ID = parts.binaryID \
						WHERE (collections.filecheck = 5 OR (collections.dateadded < (now() - interval 72 hour))) "+where)
		reccount = mdb.getAffectedRows()

		where = ' AND groupID = %s' % groupID if not groupID else ''
		# releases past retention
		if page.site().releaseretentiondays != 0:
			result = mdb.query("SELECT ID, guid FROM releases WHERE postdate < now() - interval %s day " % page.site().releaseretentiondays)
			for rowrel in result:
				self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
				remcount += 1

		# passworded releases
		if page.site().deletepasswordedrelease == 1:
			result = mdb.query("SELECT ID, guid FROM releases WHERE passwordstatus > 0")
			for rowrel in result:
				self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
				passcount += 1

		# crossposted releases
		resrel = mdb.query("SELECT ID, guid FROM releases WHERE adddate > (now() - interval %s hour) GROUP BY name HAVING count(name) > 1" % self.crosspostt)
		for rowrel in resrel:
			self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
			dupecount += 1

		# releases below completion %
		if self.completion > 0:
			resrel = mdb.query("SELECT ID, guid FROM releases WHERE completion < %s and completion > 0" % self.completion)
			for rowrel in resrel:
				self.fastDelet(rowrel['ID'], rowrel['guid'], self.site)
				completioncount += 1

		# disabled categories
		catlist = cat.getDisabledIDs()
		if catlist:
			for dicks in catlist:
				rels = mdb.query("select ID, guid from releases where categoryID = %d", (dicks['ID'],))
				for rel in rels:
					disabledcount += 1
					self.fastDelete(rel['ID'], rel['guid'], self.site)

		print 'Removed releses: %d past rentention, %d passworded, %d crossposted, %d from disabled categories.' % (remcount, passcount, dupecount, disabledcount)
		if self.completion > 0:
			print 'Removed %d under %d%% completion. Removed %d parts/binaries/collection rows.' % (int(completioncount), int(self.completion), int(reccount))
		else:
			print 'Removed %d parts/binaries/collection rows.' % (reccount)

		print console.convertTime(int(time.time() - stage7))

	def processReleases(self, categorize, postproc, groupName):
		mdb = db.DB()
		console = consoletools.Consoletools()
		n = '\n'
		groupID = ''
		if groupName:
			groupInfo = groups.getByName(groupName)
			groupID = groupInfo['ID']

		self.processReleases = time.time()
		print 'Starting release update process %s' % strftime("%Y-%m-%d %H:%M:%S", gmtime())
		if not os.path.isdir(page.site().nzbpath):
			print 'Bad or missing nzb directory - %s' % page.site().nzbpath
			return

		self.processReleasesStage1(groupID)

		self.processReleasesStage2(groupID)

		self.processReleasesStage3(groupID)

		releasesAdded = self.processReleasesStage4_loop(groupID)

		self.processReleasesStage4dot5(groupID)

		self.processReleasesStage5_loop(groupID)

		self.processReleasesStage6(categorize, postproc, groupID)

		deletedCount = self.processReleasesStage7(groupID)

		# print amount of added releases and time it took

		timeUpdate = console.convertTime(int(time.time() - self.processReleases))
		where = ' WHERE groupID = %s' % groupID if groupID else ''

		cremain = mdb.queryOneRow("select count(ID) as ID from collections "+where)
		print 'Completed adding %d releases in %s. %d collections waiting to be created (still incomplete or in queue for creation.' % (releasesAdded, timeUpdate, cremain['ID'])
		return releasesAdded

	def splitBunchedCollections(self):
		mdb = db.DB()
		# namecleaner = namecleaning
		res = mdb.queryDirect("SELECT b.ID as bID, b.name as bname, c.* FROM binaries b LEFT JOIN collections c ON b.collectionID = c.ID where c.filecheck = 10")
		if res:
			if len(res) > 0:
				print 'Extracting bunched up collections.'
				bunchedcnt = 0
				cIDS = list()
				for row in res:
					cIDS.append(row['ID'])
					newMD5 = hashlib.md5(namecleaning.collectionsCleaner(row['bname'], 'split')+row['fromname']+row['groupID']+row['totalFiles']).hexdigest()
					cres = mdb.queryOneRow("SELECT ID FROM collections WHERE collectionhash = %s", (newMD5,))
					if not cres:
						bunchedcnt += 1
						csql = "INSERT INTO collections (name, subject, fromname, date, xref, groupID, totalFiles, collectionhash, filecheck, dateadded) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 11, now())"
						collectionID = mdb.queryInsert(csql, (namecleaning.releaseCleaner(row['bname']), row['bname'], row['fromname'], row['date'], row['xref'], row['groupID'], row['totalFiles'], newMD5))
					else:
						collectionID = cres['ID']
						# update the collection table with the last seen date for the collection
						mdb.queryDirect("UPDATE collections set dateadded = now() where ID = %s", (collectionID,))
					# update the parts/binaries with new info
					mdb.query("UPDATE binaries SET collectionID = %s where ID = %s", (collectionID, row['bID'],))
					mdb.query("UPDATE parts SET binaryID = %s where binaryID = %s", (row['bID'], row['bID'],))
				# remove the old collections
				for cID in list(set(cIDS)):
					mdb.query("DELETE FROM collections WHERE ID = %s", (cID,))

				# update the collections to say we are done
				mdb.query("UPDATE collections SET filecheck = 0 WHERE filecheck = 11")
				print 'Extracted %d bunched collections.' % bunchedcnt
