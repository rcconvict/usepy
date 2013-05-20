#!/usr/bin/env python
import sites
import db

CAT_GAME_NDS = 1010
CAT_GAME_PSP = 1020
CAT_GAME_WII = 1030
CAT_GAME_XBOX = 1040
CAT_GAME_XBOX360 = 1050
CAT_GAME_WIIWARE = 1060
CAT_GAME_XBOX360DLC = 1070
CAT_GAME_PS3 = 1080
CAT_GAME_OTHER = 1090
CAT_MOVIE_FOREIGN = 2010
CAT_MOVIE_OTHER = 2020
CAT_MOVIE_SD = 2030
CAT_MOVIE_HD = 2040
CAT_MOVIE_3D = 2050
CAT_MOVIE_BLURAY = 2060
CAT_MOVIE_DVD = 2070
CAT_MUSIC_MP3 = 3010
CAT_MUSIC_VIDEO = 3020
CAT_MUSIC_AUDIOBOOK = 3030
CAT_MUSIC_LOSSLESS = 3040
CAT_MUSIC_OTHER = 3050
CAT_PC_0DAY = 4010
CAT_PC_ISO = 4020
CAT_PC_MAC = 4030
CAT_PC_PHONE_OTHER = 4040
CAT_PC_GAMES = 4050
CAT_PC_PHONE_IOS = 4060
CAT_PC_PHONE_ANDROID = 4070
CAT_TV_WEBDL = 5010
CAT_TV_FOREIGN = 5020
CAT_TV_SD = 5030
CAT_TV_HD = 5040
CAT_TV_OTHER = 5050
CAT_TV_SPORT = 5060
CAT_TV_ANIME = 5070
CAT_TV_DOCUMENTARY = 5080
CAT_XXX_DVD = 6010
CAT_XXX_WMV = 6020
CAT_XXX_XVID = 6030
CAT_XXX_X264 = 6040
CAT_XXX_OTHER = 6050
CAT_XXX_IMAGESET = 6060
CAT_XXX_PACKS = 6070
CAT_MISC = 7010
CAT_BOOKS_EBOOK = 8010
CAT_BOOKS_COMICS = 8020
CAT_BOOKS_MAGAZINES = 8030
CAT_BOOKS_TECHNICAL = 8040
CAT_BOOKS_OTHER = 8050

CAT_PARENT_GAME = 1000
CAT_PARENT_MOVIE = 2000
CAT_PARENT_MUSIC = 3000
CAT_PARENT_PC = 4000
CAT_PARENT_TV = 5000
CAT_PARENT_XXX = 6000
CAT_PARENT_MISC = 7000
CAT_PARENT_BOOKS = 8000

STATUS_INACTIVE = 0
STATUS_ACTIVE = 1
STATUS_DISABLED = 2

class Category():
	def __init__(self):
		s = sites.Sites()
		sdata = s.get()
		#self.categorizeforeign = False if site.categorizeforeign == '0' else True
		try:
			self.catlanguage = self.catlanguage
		except:
			self.catlanguage = '0'

	def get(self, activeonly=False, excludedcats=[]):
		mdb = db.DB()

		excatlist = ''
		if len(excludedcats) > 0:
			exccatlist = ' and c.ID not in (%s)' % ','.join(excludedcats)

		act = ''
		if activeonly:
			act = ' where c.status = %d %s ' % (STATUS_ACTIVE, exccatlist)

		return mdb.query("select c.ID, concat(cp.title, ' > ',c.title) as title, cp.ID as parentID, c.status from category c inner join category cp on cp.ID = c.parentID %s ORDER BY c.ID" % (act))

	def isParent(self, cid):
		mdb = db.DB()
		ret = mdb.queryOneRow('select * from category where ID = %s and parentID is null', (cid,))
		if ret:
			return True
		else:
			return False

	def getFlat(self, activeonly=False):
		mdb = db.DB()
		act = ''
		if activeonly:
			act = ' where c.status = %d ' % STATUS_ACTIVE
		return mdb.query('select c.*, (SELECT title FROM category WHERE ID=c.parentID) AS parentName from category c %s ORDER BY c.ID', (act,))

	def getChildren(self, cid):
		mdb = db.DB()
		return mdb.query('SELECT c.* from category c where parentID = %s', (cid,))

	def getDisabledIDs(self):
		mdb = db.DB()
		return mdb.queryDirect('select ID from category WHERE status = 2')

	def getById(self, id):
		mdb = db.DB()
		return mdb.queryOneRow("SELECT c.disablepreview, c.ID, CONCAT(COALESCE(cp.title,''), CASE WHEN cp.title IS NULL THEN '' ELSE ' > ' END, c.title) as title, c.status, c.parentID from category c left outer join category cp on cp.ID = c.parentID where c.ID = %s", (id,))

	def getByIds(self, ids=[]):
		mdb = db.DB()
		return mdb.query("SELECT concat(cp.title, ' > ',c.title) as title from category c inner join category cp on cp.ID = c.parentID where c.ID in (%s)", (','.join(ids),))

	def update(self, id, status, desc, disablepreview):
		mdb = db.DB()
		return mdb.query("UPDATE category set disablepreview = %s, status = %s, description = %s WHERE ID = %s", (disablepreview, status, desc, id))

	def getForMenu(self, excludedcats=[]):
		mdb = db.DB()
		ret = list()

		exccatlist = ''
		if len(excludedcats) > 0:
			exccatlist = ' and ID not in (%s)' % (','.join(excludedcats))

		arr = mdb.query('SELECT * from category where status = %s %s' % (STATUS_ACTIVE, exccatlist))
		for a in arr:
			if a['parentID'] == '':
				ret.append(a)
		
		for key, parent in ret:
			subcatlist = list()
			subcatnames = list()
			for a in arr:
				if a['parentID'] == parent['ID']:
					subcatlist.append(a)
					subcatnames.append(a['title'])

			if len(subcatlist) > 0:
				# how do you sort a sortless dict? Switch to tuples?
				ret[key]['subcatlist'] = subcatlist
			else:
				del ret[key]

		return ret

	def getForSelect(self, blnIncludeNoneSelected = True):
		categories = self.get()
		temp_dict = dict()

		if blnIncludeNoneSelected:
			temp_dict[-1] = '--Please Select--'

		for category in categories:
			temp_dict[int(category['ID'])] = category['title']

		return temp_dict

	def getNameByID(self, ID):
		mdb = db.DB()
		parent = mdb.queryOneRow('SELECT title FROM category WHERE ID = %s000' %(ID[0],))
		cat = mdb.queryOneRow('SELECT title FROM category WHERE ID = %s', (ID,))
		return parent['title'] + ' ' +  cat['title']

	def determineCategory(self, releasename, groupID):
		'''0 : English
		1 : Danish
		2 : French
		3 : German'''

		if self.catlanguage == 0:
			if self.determineCategoryNormal(releasename, groupID):
				return self.tmpCat
		elif self.catlanguage == 1:
			cg = CategoryGerman()
			if cg.determineCategory(releasename, groupID):
				return CAT_MISC
		elif self.catlanguage == 2:
			cd = CategoryDanish()
			if cd.determineCategory(releasename, groupID):
				return CAT_MISC
		elif self.catlanguage == 3:
			cf = CategoryFrench()
			if cf.determineCategory(releasename, groupID):
				return CAT_MISC

	def determineCategoryNormal(self, releasename, groupID):
		if self.isHashed(releasename):
			return self.tmpCat
		if self.byGroup(releasename, groupID):
			return self.tmpCat
		if self.isPC(releasename):
			return self.tmpCat
		if self.isTV(releasename):
			return self.tmpCat
		if self.isMovie(releasename):
			return self.tmpCat
		if self.isXXX(releasename):
			return self.tmpCat
		if self.isConsole(releasename):
			return self.tmpCat
		if self.isMusic(releasename):
			return self.tmpCat
		if self.isBook(releasename):
			return self.tmpCat
	#
	# Beginning of functions to determine category by release name
	#

	# 
	# groups
	#

	def byGroup(self, releasename, groupID):
		groups = Groups()

		groupRes = groups.getByID(groupID)

		if type(groupRes) == type(dict()):
			for groupRows in groupRes:
				if re.search('alt\.binaries\.0day\.stuffz', groupRes['name']):
					if self.isEBook(releasename): return self.tmpCat
					if self.isPC(releasename): return self.tmpCat
					self.tmpCat = CAT_PC_0DAY
					return True
				if re.search('alt\.binaries\.audio\.warez', groupRes['name']):
					self.tmpCat = CAT_PC_0DAY
					return True
				if re.search('alt\.binaries\.(multimedia\.)?anime(\.(highspeed|repost))?', groupRes['name']):
					self.tmpCat = CAT_TV_ANIME
					return True
				if self.categorizeforeign:
					if re.search('alt\.binaries\.cartoons\.french', groupRes['name']):
						self.tmpCat = CAT_TV_FOREIGN
						return True
				if re.search('alt\.binaries\.cd\.image\.linux', groupRes['name']):
					self.tmpCat = CAT_PC_0DAY
					return True
				if re.search('alt\.binaries\.cd\.lossless', groupRes['name']):
					self.tmpCat = CAT_MUSIC_LOSSLESS
					return True
				if re.search('alt\.binaries\.classic\.tv\.shows', groupRes['name'], re.IGNORECASE):
					self.tmpCat = CAT_TV_SD
					return True
				if re.search('alt\.binaries\.(comics\.dcp|pictures\.comics\.(complete|dcp|reposts?))', groupRes['name']):
					self.tmpCat = CAT_BOOKS_COMICS
					return True
				if re.search('alt\.binaries\.console\.ps3', groupRes['name']):
					self.tmpCat = CAT_GAME_PS3
					return True
				if re.search('alt\.binaries\.cores', groupRes['name']):
					if self.isXXX(releasename): return self.tmpCat
					return False
				if re.search('alt\.binaries(\.(19\d0s|country|sounds?(\.country|\.19\d0s)?))?\.mp3(\.[a-z]+)?', groupRes['name'], re.IGNORECASE):
					if self.isMusicLossless(releasename): return self.tmpCat
					self.tmpCat = CAT_MUSIC_MP3
					return True
				if re.search('/alt\.binaries\.dvd(\-?r)?(\.(movies|))?$', groupRes['name'], re.IGNORECASE):
					self.tmpCat = CAT_MOVIE_DVD
					return True
				if self.categorizeforeign:
					if re.search('alt\.binaries\.(dvdnordic\.org|nordic\.(dvdr?|xvid))|dk\.(binaer|binaries)\.film(\.divx)?', groupRes['name']):
						self.tmpCat = CAT_MOVIE_DVD
						return True
				if re.search('alt\.binaries\.documentaries', groupRes['name']):
					self.tmpCat = CAT_TV_DOCUMENTARY
					return True
				if re.search('alt\.binaries\.e\-?books?((\.|\-)(technical|textbooks))', groupRes['name']):
					self.tmpCat = CAT_BOOKS_TECHNICAL
					return True
				if re.search('alt\.binaries\.e\-?book(\.[a-z]+)?', groupRes['name']):
					self.tmpCat = CAT_BOOKS_EBOOK
					return True
				if re.search('alt\.binaries\.((movies|multimedia)\.)?(erotica(\.(amateur|divx))?|ijsklontje)', groupRes['name']):
					self.tmpCat = CAT_XXX_OTHER
					return True
				if re.search('alt\.binaries(\.games)?\.nintendo(\.)?ds', groupRes['name']):
					self.tmpCat = CAT_GAME_NDS	
					return True
				if re.search('alt\.binaries\.games\.wii', groupRes['name']):
					if self.isGameWiiWare(releasename): return self.tmpCat
					self.tmpCat = CAT_GAME_WII
					return True
				if re.search('alt\.binaries\.games\.xbox$', groupRes['name']):
					if self.isGameXBOX360DLC(releasename): return self.tmpCat
					if self.isGameXBOX360(releasename): return self.tmpCat
					self.tmpCat = CAT_GAME_XBOX
					return True
				if re.search('alt\.binaries\.games\.xbox360'):
					if self.isGameXBOX360DLC(releasename): return self.tmpCat
					self.tmpCat = CAT_GAME_XBOX360
					return True
				if re.search('alt\.binaries\.ipod\.videos\.tvshows', groupRes['name']):
					self.tmpCat = CAT_TV_OTHER
					return True
				if re.search('alt\.binaries\.mac$', groupRes['name']):
					self.tmpCat = CAT_PC_MAC
					return true
				if re.search('alt\.binaries\.mma$', groupResp['name']):
					if self.is0day(releasename): return self.tmpCat
					self.tmpCat = CAT_TV_SPORT
					return true
				if re.search('alt\.binaries\.moovee', groupRes['name']):
					self.tmpCat = CAT_MOVIE_SD
					return true
				if re.search('alt\.binaries\.mpeg\.video\.music', groupRes['name']):
					self.tmpCat = CAT_MUSIC_VIDEO
					return True
				if re.search('alt\.binaries\.multimedia\.documentaries', groupRes['name']):
					self.tmpCat = CAT_TV_DOCUMENTARY
					return True
				if re.search('alt\.binaries\.multimedia\.sports(\.boxing)?', groupRes['name']):
					self.tmpCat = CAT_TV_SPORT
					return True
				if re.search('alt\.binaries\.music\.opera', groupRes['name']):
					if re.search('720p|[\.\-_ ]mkv', releasename, re.IGNORECASE):
						self.tmpCat = CAT_MUSIC_VIDEO
						return True
					self.tmpCat = CAT_MUSIC_MP3
					return True
				if re.search('alt\.binaries\.(mp3|sounds?)(\.mp3)?\.audiobook(s|\.repost)?', groupRes['name']):
					self.tmpCat = CAT_MUSIC_AUDIOBOOK
					return True
				if re.search('alt\.binaries\.pro\-wrestling', groupRes['name']):
					self.tmpCat = CAT_TV_SPORT
					return True
				if re.search('alt\.binaries\.sounds\.(flac(\.jazz)|jpop|lossless(\.[a-z0-9]+)?)|alt\.binaries\.(cd\.lossless|music\.flac)', groupRes['name'], re.IGNORECASE):
					self.tmpCat = CAT_MUSIC_LOSSLESS
					return True
				if re.search('alt\.binaries\.sounds\.whitburn\.pop', groupRes['name'], re.IGNORECASE):
					if not re.search('[\.\-_ ]scans[\.\-_ ]', releasename, re.IGNORECASE):
						self.tmpCat = CAT_MUSIC_MP3
						return True
				if re.search('alt\.binaries\.sony\.psp', groupRes['name']):
					self.tmpCat = CAT_GAME_PSP
					return True
				if re.search('alt\.binaries\.warez$', groupRes['name']):
					self.tmpCat = CAT_PC_0DAY
					return True
				if re.search('alt\.binaries\.warez\.smartphone', groupRes['name']):
					if self.isPhone(releasename): return self.tmpCat
					self.tmpCat = CAT_PC_PHONE_OTHER
					return True
				if self.categorizeforeign:
					if re.search('dk\.binaer\.tv', groupRes['name']):
						self.tmpCat = CAT_TV_FOREGIN
						return True

				return False

	#
	# TV
	#

	def isTV(self, releasename, assumeTV=True):
		looksLikeTV = re.search('[\.\-_ ](\dx\d\d|s\d{1,3}[.-_ ]?(e|d)\d{1,3}|C4TV|Complete[\.\-_ ]Season|DSR|(D|H|P)DTV|EP[\.\-_ ]?\d{1,3}|S\d{1,3}.+Extras|SUBPACK|Season[\.\-_ ]\d{1,2}|WEB\-DL|WEBRip)[\.\-_ ]|TV[\.\-_ ](19|20)\d\d|TrollHD', releasename, re.IGNORECASE)
		looksLikeSportTV = re.search('[\.\-_ ]((19|20)\d\d[\.\-_ ]\d{1,2}[\.\-_ ]\d{1,2}[\.\-_ ]VHSRip|Indy[\.\-_ ]?Car|(iMPACT|Smoky[\.\-_ ]Mountain|Texas)[\.\-_ ]Wrestling|Moto[\.\-_ ]?GP|NSCS[\.\-_ ]ROUND|NECW[\.\-_ ]TV|(Per|Post)\-Show|PPV|WrestleMania|WCW|WEB[\.\-_ ]HD|WWE[\.\-_ ](Monday|NXT|RAW|Smackdown|Superstars|WrestleMania))[\.\-_ ]', releasename, re.IGNORECASE)
		
		if looksLikeTV and not re.search('[\.\-_ ](flac|imageset|mp3|xxx)[\.\-_ ]', releasename, re.IGNORECASE):
			if self.isOtherTV(releasename): return True
			if self.categorizeforeign:
				if self.isForeignTV(releasename): return True
			if self.isSportTV(releasename): return True
			if self.isDocumentaryTV(releasename): return True
			if self.isWEBDL(releasename): return True
			if self.isHDTV(releasename): return True
			if self.isSDTV(releasename): return True
			if self.isAnimeTV(releasename): return True
			if self.isOtherTV2(releasename): return True
			self.tmpCat = CAT_TV_OTHER
			return True

		if looksLikeSportTV:
			if self.isSportTV(releasename): return True
			self.tmpCat = CAT_TV_OTHER
			return True

		return False

	def isOtherTV(self, releasename):
		if not re.search('[\.\-_ ](S\d{1,3}.+Extras|SUBPACK)[\.\-_ ]', releasename, re.IGNORECASE):
			if re.search('[\.\-_ ](chinese|dk|fin|french|ger|heb|ita|jap|kor|nor|nordic|nl|pl|swe)[\.\-_ ]?(sub|dub)(ed|bed|s)?|<German>', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_FOREIGN
				return True
			if re.search('[\.\-_ ](brazilian|chinese|croatian|danish|deutsch|dutch|estonian|flemish|finnish|french|german|greek|hebrew|icelandic|italian|ita|latin|mandarin|nordic|norwegian|polish|portuguese|japenese|japanese|russian|serbian|slovenian|spanish|spanisch|swedish|thai|turkish).+(720p|1080p|Divx|DOKU|DUB(BED)?|DLMUX|NOVARIP|RealCo|Sub(bed|s)?|Web[\.\-_ ]?Rip|WS|Xvid|x264)[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_FOREIGN
				return True
			if re.search('[\.\-_ ](720p|1080p|Divx|DOKU|DUB(BED)?|DLMUX|NOVARIP|RealCo|Sub(bed|s)?|Web[\.\-_ ]?Rip|WS|Xvid).+(brazilian|chinese|croatian|danish|deutsch|dutch|estonian|flemish|finnish|french|german|greek|hebrew|icelandic|italian|ita|latin|mandarin|nordic|norwegian|polish|portuguese|japenese|japanese|russian|serbian|slovenian|spanish|spanisch|swedish|thai|turkish)[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_FOREIGN
				return True
			if re.search('(S\d\dE\d\d|DOCU(MENTAIRE)?|TV)?[\.\-_ ](FRENCH|German|Dutch)[\.\-_ ](720p|1080p|dv(b|d)r(ip)?|LD|HD\-?TV|TV[\.\-_ ]?RIP|x264)[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_FOREIGN
				return True
			if re.search('[\.\-_ ]FastSUB|NL|nlvlaams|patrfa|RealCO|Seizoen|slosinh|Videomann|Vostfr|xslidian[\.\-_ ]|x264\-iZU', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_FOREIGN
				return True

		return False

	def isSportTV(self, releasename):
		if not re.search('s\d{1,2}[.-_ ]?e\d{1,2}', releasename, re.IGNORECASE):
			if re.search('[\.\-_ ]?(Bellator|bundesliga|EPL|ESPN|FIA|la[\.\-_ ]liga|MMA|motogp|NFL|NCAA|PGA|red[\.\-_ ]bull.+race|Sengoku|Strikeforce|supercup|uefa|UFC|wtcc|WWE)[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_SPORT
				return True
			if re.search('[\.\-_ ]?(DTM|FIFA|formula[\.\-_ ]1|indycar|Rugby|NASCAR|NBA|NHL|NRL|netball[\.\-_ ]anz|ROH|SBK|Superleague|The[\.\-_ ]Ultimate[\.\-_ ]Fighter|TNA|V8[\.\-_ ]Supercars|WBA|WrestleMania)[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_SPORT
				return True
			if re.search('[\.\-_ ]?(DTM|FIFA|formula[\.\-_ ]1|indycar|Rugby|NASCAR|NBA|NHL|NRL|netball[\.\-_ ]anz|ROH|SBK|Superleague|The[\.\-_ ]Ultimate[\.\-_ ]Fighter|TNA|V8[\.\-_ ]Supercars|WBA|WrestleMania)[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_SPORT
				return True
			if re.search('[\.\-_ ]?(Horse)[\.\-_ ]Racing[\.\-_ ]', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_SPORT

		return False

	def isDocumentaryTV(self, releasename):
		if re.search('[\.\-_ ](Docu|Documentary)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_TV_DOCUMENTARY
			return True
		return False

	def isWEBDL(self, releasename):
		if re.search('web[\.\-_ ]dl', releasename, re.IGNORECASE):
			self.tmpCat = CAT_TV_DOCUMENTARY
			return True
		return False

	def isHDTV(self, releasename):
		if re.search('1080(i|p)|720p', releasename, re.IGNORECASE):
			self.tmpCat = CAT_TV_HD
			return True
		return False

	def isSDTV(releasename):
		if re.search('(360|480|576)p|Complete[\.\-_ ]Season|dvdr|dvd5|dvd9|SD[\.\-_ ]TV|TVRip|xvid', releasename, re.IGNORECASE):
			self.tmpCat = CAT_TV_SD
			return True

		if re.search('((H|P)D[\.\-_ ]?TV|DSR|WebRip)[\.\-_ ]x264', releasename, re.IGNORECASE):
			self.tmpCat = CAT_TV_SD
			return True

		if re.search('s\d{1,2}[.-_ ]?e\d{1,2}|\s\d{3,4}\s', releasename, re.IGNORECASE):
			if re.search('(H|P)D[\.\-_ ]?TV|BDRip[\.\-_ ]x264', releasename, re.IGNORECASE):
				self.tmpCat = CAT_TV_SD
				return True

		return False

	def isAnimeTV(self, releasename):
		if re.search('[\.\-_ ]Anime[\.\-_ ]|^\(\[AST\]\s|\[HorribleSubs\]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_TV_OTHER
			return True

	#
	# Movie
	#

	def isMovie(self, releasename):
		regex = dict()
		regex[0] = '[\.\-_ ]AVC|[\.\-_ ]|(B|H)(D|R)RIP|Bluray|BD[\.\-_ ]?(25|50)?|BR|Camrip|[\.\-_ ]\d{4}[\.\-_ ].+(720p|1080p|Cam)|DIVX|[\.\-_ ]DVD[\.\-_ ]|DVD-?(5|9|R|Rip)|Untouched|VHSRip|XVID|[\.\-_ ](DTS|TVrip)[\.\-_ ]'
		regex[1] = 'auto(cad|desk)|divx[\.\-_ ]plus|[\.\-_ ]exe$|[\.\-_ ](jav|XXX)[\.\-_ ]|\wXXX(1080p|720p|DVD)|Xilisoft'
		if re.search(regex[0], releasename, re.IGNORECASE) and not re.search(regex[1], releasename, re.IGNORECASE):
			if self.categorizeforeign:
				if self.isMovieForeign(releasename): return True
			if self.isMovieDVD(releasename): return True
			if self.isMovieSD(releasename): return True
			if self.isMovie3D(releasename): return True
			if self.isMovieBluRay(releasename): return True
			if self.isMovieHD(releasename): return True
			if self.isMovieOther(releasename): return True

		return False

	def isMovieForeign(self, releasename):
		if re.search('(danish|flemish|Deutsch|dutch|french|german|nl[\.\-_ ]?sub(bed|s)?|\.NL|norwegian|swedish|swesub|spanish|Staffel)[\.\-_ ]|\(german\)', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_FOREIGN
			return True
		if re.search('Castellano', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_FOREIGN
			return True
		if re.search('(720p|1080p|AC3|AVC|DIVX|DVD(5|9|RIP|R)|XVID)[\.\-_ ](Dutch|French|German|ITA)|\(?(Dutch|French|German|ITA)\)?[\.\-_ ](720P|1080p|AC3|AVC|DIVX|DVD(5|9|RIP|R)|HD[\.\-_ ]|XVID)', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_FOREIGN
			return True
		return False

	def isMovieDVD(self, releasename):
		if re.search('(dvd\-?r|[\.\-_ ]dvd|dvd9|dvd5|[\.\-_ ]r5)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_DVD
			return True
		return False

	def isMovieSD(self, releasename):
		if re.search('(bdrip|divx|dvdscr|extrascene|dvdrip|\.CAM|vhsrip|xvid)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_SD
			return True
		return False

	def isMovie3D(self, releasename):
		if re.search('[\.\-_ ]3D\s?[\.\-_\[ ](1080p|(19|20)\d\d|AVC|BD(25|50)|Blu[\.\-_ ]?ray|CEE|Complete|GER|MVC|MULTi|SBS)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_3D
			return True
		return False

	def isMovieBluRay(self, releasename):
		if re.search('bluray\-|[\.\-_ ]bd?[\.\-_ ]?(25|50)|blu-ray|Bluray\s\-\sUntouched|[\.\-_ ]untouched[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_BLURAY
			return True
		return False

	def isMovieHD(self, releasename):
		if re.search('720p|1080p|AVC|VC1|VC\-1|web\-dl|wmvhd|x264|XvidHD', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_HD
			return True
		return False

	def isMovieOther(self, releasename):
		if re.search('[\.\-_ ]cam[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MOVIE_OTHER
			return True
		return False

	#
	# PC
	#

	def isPC(self, releasename):
		if not re.search('[\.\-_ ]PDTV[\.\-_ ]|x264|[\.\-_ ]XXX[\.\-_ ]|Imageset', releasename, re.IGNORECASE):
			if self.isPhone(releasename): return True
			if self.isMac(releasename): return True
			if self.is0day(releasename): return True
			if self.isPCGame(releasename): return True
		return False

	def isPhone(self, releasename):
		if re.search('[\.\-_ ]?(IPHONE|ITOUCH|IPAD)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_PHONE_IOS
			return True
		if re.search('[\.\-_ ]?(ANDROID)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_PHONE_ANDROID
			return True
		if re.search('[\.\-_ ]?(symbian|xscale|wm5|wm6)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_PHONE_OTHER
			return True
		return False

	def is0day(self, releasename):
		if re.search('[\.\-_ ]exe$|[\.\-_ ](utorrent|Virtualbox)[\.\-_ ]|incl.+crack', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_0DAY
			return True
		if re.search('[\.\-_ ](32bit|64bit|x32|x64|x86|i\d86|win64|winnt|win9x|win2k|winxp|winnt2k2003serv|win9xnt|win9xme|winnt2kxp|win2kxp|win2kxp2k3|keygen|regged|keymaker|winall|win32|template|Patch|GAMEGUiDE|unix|irix|solaris|freebsd|hpux|linux|windows|multilingual|software|Pro v\d{1,3})[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_0DAY
			return True
		if re.search('Adobe|auto(cad|desk)|\-BEAN|Cracked|Cucusoft|CYGNUS|Divx[\.\-_ ]Plus|\.deb|DIGERATI|FOSI|Keyfilemaker|Keymaker|Keygen|Lynda\.com|lz0|MULTiLANGUAGE|MultiOS|\-iNViSiBLE|\-SPYRAL|\-SUNiSO|\-UNION|\-TE|v\d{1,3}.*?Pro|[\.\-_ ]v\d{1,3}[\.\-_ ]|WinAll|\(x(64|86)\)|Xilisoft', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_0DAY
			return True
		return False

	def isMac(self, releasename):
		if re.search('mac(\.|\s)?osx', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_MAC
			return True
		return False

	def isPCGame(self, releasename):
		if re.search('FASDOX|games|PC GAME|RIP\-unleashed|Razor1911', releasename, re.IGNORECASE) and not re.search('[\.\-_ ]PSP|WII|XBOX', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_GAMES
			return True
		if re.search('[\.\-_ ](0x0007|ALiAS|BACKLASH|BAT|CPY|FASiSO|FLT([\.\-_ ]|COGENT)|GENESIS|HI2U|JAGUAR|MAZE|MONEY|OUTLAWS|PPTCLASSiCS|PROPHET|RAiN|RELOADED|RiTUELYPOGEiOS|SKIDROW|TiNYiSO)', releasename, re.IGNORECASE):
			self.tmpCat = CAT_PC_GAMES
			return True
		return False

	#
	# XXX
	#

	def isXxx(self, releasename):
		if re.search('[\.\-_ ](XXX|PORNOLATiON)', releasename):
			if self.isXxx264(releasename): return True
			if self.isXxxXvid(releasename): return True
			if self.isXxxImageset(releasename): return True
			if self.isXxxWMV(releasename): return True
			if self.isXxxDVD(releasename): return True
			if self.isXxxOther(releasename): return True
			self.tmpCat = CAT_XXX_OTHER
			return True
		elif re.search('a\.b\.erotica|Imageset|Lesbian|Squirt|Transsexual', releasename, re.IGNORECASE):
			if self.isXxx264(releasename): return True
			if self.isXxxXvid(releasename): return True
			if self.isXxxImageset(releasename): return True
			if self.isXxxWMV(releasename): return True
			if self.isXxxDVD(releasename): return True
			if self.isXxxOther(releasename): return True
			self.tmpCat = CAT_XXX_OTHER
			return True
		return False

	def isXxxX264(self, releasename):
		if re.search('720p|1080(hd|p)|x264', releasename, re.IGNORECASE) and not re.search('wmv', releasename, re.IGNORECASE):
			self.tmpCat = CAT_XXX_X264
			return True
		return False

	def isXxxWMV(self, releasename):
		if re.search('(\d{2}\.\d{2}\.\d{2})|(e\d{2,})|f4v|flv|isom|(issue\.\d{2,})|mov|mp4|mpeg|multiformat|pack\-|realmedia|uhq|wmv', releasename, re.IGNORECASE):
			self.tmpCat = CAT_XXX_WMV
			return True
		return False

	def isXxxXvid(self, releasename):
		if re.search('dvdrip|bdrip|brrip|detoxication|divx|nympho|pornolation|swe6|tesoro|xvid', releasename, re.IGNORECASE):
			self.tmpCat = CAT_XXX_XVID
			return True
		return False

	def isXxxDVD(self, releasename):
		if re.search('dvdr[^ip]|dvd5|dvd9', releasename, re.IGNORECASE):
			self.tmpCat = CAT_XXX_DVD
			return True
		return False

	def isXxxImageset(self, releasename):
		if re.search('IMAGESET', releasename, re.IGNORECASE):
			self.tmpCat = CAT_XXX_IMAGESET
			return True
		return False

	def isXxxOther(self, releasename):
		if re.search('[\.\-_ ]Brazzers|Creampie|[\.\-_ ]JAV[\.\-_ ]|North\.Pole|She[\.\-_ ]?Male|Transsexual', releasename, re.IGNORECASE):
			self.tmpCat = CAT_XXX_OTHER
			return True
		return False

	#
	# console
	#

	def isConsole(self, releasename):
		if self.isGameNDS(releasename): return True
		if self.isGamePS3(releasename): return True
		if self.isGamePSP(releasename): return True
		if self.isGameWiiWare(releasename): return True
		if self.isGameWii(releasename): return True
		if self.isGameXBOX360DLC(releasename): return True
		if self.isGameXBOX360(releasename): return True
		if self.isGameXBOX(releasename): return True
		return False

	def isGameNDS(self, releasename):
		if re.search('NDS|[\. ]nds|nintendo.+3ds', releasename, re.IGNORECASE):
			if re.search('\((DE|DSi(\sEnhanched)?|EUR?|FR|GAME|HOL|JP|NL|NTSC|PAL|KS|USA?)\)', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_NDS
				return True
		return False

	def isGamePS3(self, releasename):
		if re.search('PS3', releasename, re.IGNORECASE):
			if re.search('ANTiDOTE|DLC|DUPLEX|EUR?|Googlecus|GOTY|\-HR|iNSOMNi|JPN|KONDIOS|\[PS3\]|PSN', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_PS3
				return True
			if re.search('AGENCY|APATHY|Caravan|MULTi|NRP|NTSC|PAL|SPLiT|STRiKE|USA?|ZRY', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_PS3
				return True
		return False

	def isGamePSP(self, releasename):
		if re.search('PSP', releasename, re.IGNORECASE):
			if re.search('[\.\-_ ](BAHAMUT|Caravan|EBOOT|EMiNENT|EUR?|EvoX|GAME|GHS|Googlecus|HandHeld|\-HR|JAP|JPN|KLOTEKLAPPERS|KOR|NTSC|PAL)', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_PSP
				return True
			if re.search('[\.\-_ ](Dynarox|HAZARD|ITALIAN|KLB|KuDoS|LIGHTFORCE|MiRiBS|POPSTATiON|(PLAY)?ASiA|PSN|SPANiSH|SUXXORS|UMD(RIP)?|USA?|YARR)', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_PSP
				return True
	def isGameWiiWare(self, releasename):
		if re.search('(Console|DLC|VC).+[\.\-_ ]WII|(Console|DLC|VC)[\.\-_ ]WII|WII[\.\-_ ].+(Console|DLC|VC)|WII[\.\-_ ](Console|DLC|VC)|WIIWARE', releasename, re.IGNORECASE):
			self.tmpCat = CAT_GAME_WIIWARE
			return True
		return False

	def isGameWii(self, releasename):
		if re.search('WII', releasename, re.IGNORECASE):
			if re.search('[\.\-_ ](Allstars|BiOSHOCK|dumpTruck|DNi|iCON|JAP|NTSC|PAL|ProCiSiON|PROPER|RANT|REV0|SUNSHiNE|SUSHi|TMD|USA?)', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_WII
				return True
			if re.search('[\.\-_ ](APATHY|BAHAMUT|DMZ|ERD|GAME|JPN|LoCAL|MULTi|NAGGERS|OneUp|PLAYME|PONS|Scrubbed|VORTEX|ZARD|ZER0)', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_WII
				return True
			if re.search('/[\.\-_ ](ALMoST|AMBITION|Caravan|CLiiCHE|DRYB|HaZMaT|KOR|LOADER|MARVEL|PROMiNENT|LaKiTu|LOCAL|QwiiF|RANT)', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_WII
				return True
		return False

	def isGameXBOX360DLC(self, releasename):
		if re.search('DLC.+xbox360|xbox360.+DLC|XBLA.+xbox360|xbox360.+XBLA', releasename, re.IGNORECASE):
			self.tmpCat = CAT_GAME_XBOX360DLC
			return True
		return False

	def isGameXBOX360(self, releasename):
		if re.search('XBOX360', releasename, re.IGNORECASE):
			self.tmpCat = CAT_GAME_XBOX360
		if re.search('x360', releasename, re.IGNORECASE):
			if re.search('Allstars|ASiA|CCCLX|COMPLEX|DAGGER|GLoBAL|iMARS|JAP|JPN|MULTi|NTSC|PAL|REPACK|RRoD|RF|SWAG|USA?', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_XBOX360
				return True
			if re.search('DAMNATION|GERMAN|GOTY|iNT|iTA|JTAG|KINECT|MARVEL|MUX360|RANT|SPARE|SPANISH|VATOS|XGD', releasename, re.IGNORECASE):
				self.tmpCat = CAT_GAME_XBOX360
				return True
		return False

	def isGameXBOX(self, releasename):
		if re.search('XBOX', releasename, re.IGNORECASE):
			self.tmpCat = CAT_GAME_XBOX
			return True
		return False

	#
	# Music
	#

	def isMusic(self, releasename):
		if self.isMusicVideo(releasename): return True
		if self.isMusicLossless(releasename): return True
		if self.isMusicMP3(releasename): return True
		if self.isMusicOther(releasename): return True

		return False

	def isMusicvideo(self, releasename):
		if re.search('(720P|x264)\-(19|20)\d\d\-[a-z0-9]{1,12}', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MUSIC_VIDEO
			return True
		if re.search('[a-z0-9]{1,12}\-(19|20)\d\d\-(720P|x264)', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MUSIC_VIDEO
			return True
		return False

	def isMusicLossless(self, releasename):
		if re.search('\[(19|20)\d\d\][\.\-_ ]\[FLAC\]|(\(|\[)flac(\)|\])|FLAC\-(19|20)\d\d\-[a-z0-9]{1,12}|\.flac"|(19|20)\d\d\sFLAC|[\.\-_ ]FLAC.+(19|20)\d\d[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MUSIC_LOSSLESS
			return True
		return False

	def isMusicMP3(self, releasename):
		if re.search('[a-z0-9]{1,12}\-(19|20)\d\d\-[a-z0-9]{1,12}|[\.\-\(\[_ ]\d{2,3}k[\.\-\)\]_ ]|\((192|256|320)\)|(320|cd|eac|vbr).+mp3|(cd|eac|mp3|vbr).+320|FIH\_INT|\s\dCDs|[\.\-_ ]MP3[\.\-_ ]|MP3\-\d{3}kbps|\.(m3u|mp3)"|NMR\s\d{2,3}\skbps|\(320\)\.|\-\((Bootleg|Promo)\)|\.mp3$|\-\sMP3\s(19|20)\d\d|\(vbr\)|rip(192|256|320)|[\.\-_ ](CDR|WEB).+(19|20)\d\d', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MUSIC_MP3
			return True
		if re.search('\s(19|20)\d\d\s([a-z0-9]{3}|[a-z]{2,})$|\-(19|20)\d\d\-(C4|MTD)(\s|\.)|[\.\-_ ]FM.+MP3[\.\-_ ]|\-web\-(19|20)\d\d(\.|\s)|[\.\-_ ](SAT|WEB).+(19|20)\d\d[\.\-_ ]|[\.\-_ ](19|20)\d\d.+(SAT|WEB)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MUSIC_MP3
			return True
		return False

	def isMusicOther(self, releasename):
		if re.search('(19|20)\d\d\-(C4)$|[\.\-_ ]\d?CD[\.\-_ ](19|20)\d\d|\(\d\-?CD\)|\-\dcd\-|\d[\.\-_ ]Albums|Albums.+(EP)|Bonus.+Tracks|Box.+?CD.+SET|Discography|D\.O\.M|Greatest\sSongs|Live.+(Bootleg|Remastered)|Music.+Vol|(\(|\[|\s)NMR(\)|\]|\s)|Promo.+CD|Reggaeton|Tiesto.+Club|Vinyl\s2496|\WV\.A\.|^\(VA\s|^VA[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_MUSIC_OTHER
			return True
		return False

	#
	# Books
	#

	def isBook(self, releasename):
		if self.isComic(releasename): return True
		if self.isTechnicalBook(releasename): return True
		if self.isMagazine(releasename): return True
		if self.isEBook(releasename): return True
		return False

	def isEBook(self, releasename):
		if re.search('^ePub|[\.\-_ ](Ebook|E?\-book|\) WW|Publishing|\[Springer\])|[\.\-_\(\[ ](epub|html|mobi|pdf|rtf|tif|txt)[\.\-_\)\] ]|[\. ](doc|epub|mobi|pdf)(?![\w .])', releasename, re.IGNORECASE):
			self.tmpCat = CAT_BOOKS_EBOOK
			return True
		return False

	def isComic(self, releasename):
		if re.search('[\. ](cbr|cbz)|[\( ]c2c[\) ]|comix|comic.+book', releasename, re.IGNORECASE):
			self.tmpCat = CAT_BOOKS_COMICS
			return True
		return False

	def isTechnicalBook(self, releasename):
		if re.search('[\.\-_ ](DIY|Service\s?Manual|Woodworking|Workshops?)[\.\-_ ]|^Wood[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_BOOKS_TECHNICAL
			return True
		return False

	def isMagazine(self, releasename):
		if re.search('[\.\-_ ](FHM|Magazine|NUTS|XXX)[\.\-_ ]|(^Club|^FHM|Hustler|Maxim|^NUTS|Penthouse|Playboy|Top[\.\-_ ]Gear)[\.\-_ ]', releasename, re.IGNORECASE):
			self.tmpCat = CAT_BOOKS_MAGAZINE
			return True
		return False

	#
	# Hashed - all hashed go in other misc.
	#

	def isHashed(self, releasename):
		if re.search('[\.\-_ ](720p|1080p|s\d{1,2}[.-_ ]?e\d{1,2})[\.\-_ ]', releasename, re.IGNORECASE):
			regexs = ['[a-z0-9]{21,}', '[A-Z0-9]{20,}', '^[A-Z0-9]{1,}$', '^[a-z0-9]{1,}$']
			for regex in regexs:
				if re.search(regex, releasename, re.IGNORECASE):
					self.tmpCat = CAT_MISC
					return True
		return False
