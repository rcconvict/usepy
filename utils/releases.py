#!/usr/bin/env python
import site, db, re
from time import gmtime, strftime

class Releases():
	def __init__(self):
		self.PASSWD_NONE = 0
		self.PASSWD_POTENTIAL = 1
		self.PASSWD_RAR = 2

	def get(self):
		s = site.Sites()
		self.site = s.get()
		self.stage5limit = self.site['maxnzbsprocessed'] if self.site['maxnzbsprocessed'] else 1000
		self.completion = self.site['releasecompletion'] if self.site['releasecompletion'] else 0
		self.crosspostt = self.site['coressposttime'] if self.site['crosspostttime'] else 2
		self.updategrabs = False if self.site['grabstatus'] == 0 else True

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

	def processReleasesStage1(self, groupID):
		mdb = db.DB()
		c = consoletools.ConsoleTools()
		n = '\n'

		print 'Stage 1 -> Try to find complete collections.'
		stage1 = time.time()
		where = ' AND groupID = %s' % groupID if not groupID else ''

		# look if we have all the files in a collection (which have the file count in the subject). Set filecheck to 1
		mdb.query("UPDATE collections SET filecheck = 1 WHERE ID IN (SELECT ID FROM (SELECT c.ID FROM collections c LEFT JOIN binaries b ON b.collectionID = c.ID WHERE c.totalFiles > 0 AND c.filecheck = 0"+where+" GROUP BY c.ID, c.totalFiles HAVING count(b.ID) >= c.totalFiles) as tmpTable)" % where)
		
		# if we have all the parts set partcheck to 1
		if not groupID:
			mdb.query("UPDATE binaries b SET partcheck = 1 WHERE b.ID IN (SELECT p.binaryID FROM parts p WHERE p.binaryID = b.ID AND b.partcheck = 0 GROUP BY p.binaryID HAVING count(p.ID) >= b.totalParts)")
		else:
			mdb.query("UPDATE binaries b SET partcheck = 1 WHERE b.ID IN (SELECT p.binaryID FROM parts p ,collections c WHERE p.binaryID = b.ID AND b.partcheck = 0 and c.id = b.collectionid and c.groupid = "+groupID+" GROUP BY p.binaryID HAVING count(p.ID) >= b.totalParts )" % groupID)		

		# set file check to 2 if we have all the parts
		mdb.query("UPDATE collections SET filecheck = 2 WHERE ID IN (SELECT ID FROM (SELECT c.ID FROM collections c LEFT JOIN binaries b ON c.ID = b.collectionID WHERE b.partcheck = 1 AND c.filecheck = 1 GROUP BY c.ID, c.totalFiles HAVING count(b.ID) >= c.totalFiles) as tmp)")

		# if a collection has not been updated in two hours, set filecheck to 2
		mdb.query("UPDATE collections c SET filecheck = 2, totalFiles = (SELECT COUNT(b.ID) FROM binaries b WHERE b.collectionID = c.ID) WHERE c.dateadded < (now() - interval 2 hour) AND c.filecheck < 2 "+where)

		print c.convertTime(int(time.time() - stage1))

	def processReleaseStage2(self, groupID):
		mdb = db.DB()
		c = consoletools.ConsoleTools()
		n = '\n'
		where = ' AND groupID = %s' % groupID if not groupID else ''

		print 'Stage 2 -> Get the size in bytes of the collection.'

		stage2 = time.time()
		# get the total size in bytes of the collection for collections where filecheck = 2
		mdb.query("UPDATE collections c SET filesize = (SELECT SUM(size) FROM parts p LEFT JOIN binaries b ON p.binaryID = b.ID WHERE b.collectionID = c.ID), c.filecheck = 3 WHERE c.filecheck = 2 AND c.filesize = 0 "+where)

		print c.convertTime(int(time.time() - stage2))

	def processReleasesStage3(self, groupID):
		mdb = db.DB()
		c = consoletools.ConsoleTools()
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
					mdb.query("UPDATE collections c LEFT JOIN (SELECT g.ID, coalesce(g.minsizetoformrelease, s.minsizetoformrelease) as minsizetoformrelease FROM groups g INNER JOIN ( SELECT value as minsizetoformrelease FROM site WHERE setting = 'minsizetoformrelease' ) s ) g ON g.ID = c.groupID SET c.filecheck = 5 WHERE g.minsizetoformrelease != 0 AND c.filecheck = 3 AND c.filesize < g.minsizetoformrelease and c.filesize > 0 AND groupID = "+groupID["ID"])
					
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
		c = consoletools.ConsoleTools()
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
		c = consoletools.ConsoleTools()
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
							g.minsizetoformrelease != 0 AND r.size < minsizetoformrelease AND groupID = "+groupID["ID"])
				if resrel:
					for rowrel in resrel:
						self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
						minsizecount += 1
				maxfilesize = mdb.queryOneRow("SELECT value FROM site WHERE setting = maxsizetoformrelease")
				if maxfilesizeres['value'] != 0:
					resrel = mdb.query("SELECT ID, guid from releases where groupID = %d AND filesize > %d " % (groupID["ID"], maxfilesizeres["value"]))
					if resrel:
						for rowrel in resrel:
							self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
							maxsizecount += 1

				resrel = mdb.query("SELECT r.ID FROM releases r LEFT JOIN \
							(SELECT g.ID, guid, coalesce(g.minfilestoformrelease, s.minfilestoformrelease) \
							as minfilestoformrelease FROM groups g INNER JOIN ( SELECT value as minfilestoformrelease \
							FROM site WHERE setting = 'minfilestoformrelease' ) s ) g ON g.ID = r.groupID WHERE \
							g.minfilestoformrelease != 0 AND r.totalpart < minfilestoformrelease AND groupID = "+groupID["ID"])
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
		nzb = nzb.NZB()
		page = page.Page()
		c = consoletools.ConsoleTools()
		n = '\n'
		nzbcount = 0
		where = ' AND groupID = %s' % groupID if not groupID else ''

		# create nzb.
		print 'Stage 5 -> Create the NZB, mark collections as ready for deletion.'
		stage5 = time.time()

		start_nzbcount = nzbcount
		resrel = mdb.queryDirect("SELECT ID, guid, name, categoryID FROM releases WHERE nzbstatus = 0 "+where+" LIMIT "+self.stage5limit)
		if resrel:
			for rowrel in resrel:
				if nzb.writeNZBforReleaseId(rowrel['ID'], rowrel['guid'], rowrel['name'], rowrel['categoryID'], nzb.getNZBPath(rowrel['guid'], page.site.nzbpath, True, page.site.nzbsplitlevel)):
					mdb.queryDirect("UPDATE releases SET nzbstatus = 1 WHERE ID = %s", (rowrel['ID'],))
					mdb.queryDirect("UPDATE collections SET filecheck = 5 WHERE releaseID = %s", (rowrel['ID'],))
					nzbcount += 1
					c.overWrite('Creating NZBs:'+c.percentString(nzbcount,len(resrel)))

		timing = c.convertTime(int(time.time() - stage5))
		print n+'%d NZBs created in %s.' % (nzbcount, timing)
		return nzbcount

	def processReleasesStage5_loop(self, groupID):
		tot_nzbcount = 0
		while nzbcount > 0:
			nzbcount = self.processReleasesStage5(groupID)
			tot_nzbcount = tot_nzbcont + nzbcount

		return tot_nzbcount

	def processReleasesStage6(self, categorize, postproc, groupID):
		mdb = db.DB()
		c = consoletools.ConsoleTools()
		n = '\n'
		where = ' WHERE relnamestatus = 0 AND groupID = %s' % groupID if not groupID else 'WHERE relnamestatus = 0'

		# categorize releases
		print 'Stage 6 -> Categorize and post process releases.'
		stage6 = time.time()
		if categorize == 1:
			self.categorizeReleases('name', where)
		if postproc == 1:
			postprocess = postprocess.PostProcess(True)
			postprocess.processAll()
		else:
			print 'Post-processing disabled.'+n
		print c.convertTime(int(time.time() - stage6))

	def processReleasesStage7(self, groupID):
		mdb = db.DB()
		page = page.Page()
		cat = category.Category()
		console = consoletools.ConsoleTools()
		n = '\n'
		remcount = 0
		passcount = 0
		dupecount = 0
		relsizecount = 0
		completioncount = 0
		disabledcount = 0

		where = ' AND collections.groupID = %s' % groupID if not groupID else ''

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
		if page.site.releaseretentiondays != 0:
			result = mdb.query("SELECT ID, guid FROM releases WHERE postdate < now() - interval %d day " % page.site.releaseretentiondays)
			for rowrel in result:
				self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
				remcount += 1

		# passworded releases
		if page.site.deletepasswordedreleases == 1:
			result = mdb.query("SELECT ID, guid FROM releases WHERE passwordstatus > 0")
			for rowrel in result:
				self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
				passcount += 1

		# crossposted releases
		resrel = mdb.query("SELECT ID, guid FROM releases WHERE adddate > (now() - interval %d hour) GROUP BY name HAVING count(name) > 1" % self.crosspostt)
		for rowrel in resrel:
			self.fastDelete(rowrel['ID'], rowrel['guid'], self.site)
			dupecount += 1

		# releases below completion %
		if self.completion > 0:
			resrel = mdb.query("SELECT ID, guid FROM releases WHERE completion < %d and completion > 0" % self.completion)
			for rowrel in reslrel:
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
			print 'Removed %d under %d% completion. Removed %d parts/binaries/collection rows.' % (completioncount, self.completion, reccount)
		else:
			print 'Removed %d parts/binaries/collection rows.' % (reccount)

		print c.convertTime(int(time.time() - stage7))

	def processReleases(self, postproc, groupName):
		mdb = db.DB()
		page = page.Page()
		console = consoletools.ConsoleTools()
		n = '\n'
		groupID = ''
		if groupName:
			groupInfo = groups.getByName(groupName)
			groupID = groupInfo['ID']

		self.processReleases = time.time()
		print 'Starting release update process %s' % strftime("%Y-%m-%d %H:%M:%S", gmtime())
		if not os.path.isdir(page.site.nzbpath):
			print 'Bad or missing nzb directory - %s' % page.site.nzbpath
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

		cremain = mdb.queryOneRow("select count(ID) from collections "+where)
		print 'Completed adding %d releases in %s. %d collections waiting to be created (still incomplete or in queue for creation.' % (releasesAdded, timeUpdate, cremain)
		return releasesAdded


