#!/usr/bin/env python
import sys, os
import ConfigParser
from getpass import getpass
import utils.helper as helper
from utils.nntplib import NNTPError

skip_mysql = False

try:
	import MySQLdb as mdb
except ImportError:
	print 'You need to install python-mysqldb'
	sys.exit(1)


if not os.path.isfile('config.ini'):
	# Usenet configuration
	address = raw_input('Usenet address: ')
	port = raw_input('Usenet server port: ')
	ssl = raw_input('SSL? True, False: ')
	username = raw_input('Usenet username: ')
	password = getpass('Usenet password: ')
	
	config = ConfigParser.RawConfigParser()
	config.add_section('usenet')
	config.set('usenet', 'address', address)
	config.set('usenet', 'port', port)
	config.set('usenet', 'ssl', ssl)
	config.set('usenet', 'username', username)
	config.set('usenet', 'password', password)
	
	if not skip_mysql:
		# mysql configuration
		address = raw_input('MySQL server address: ')
		username = raw_input('MySQL username: ')
		password = getpass('MySQL password: ')
		database = raw_input('MySQL database name: ')
		
		config.add_section('mysql')
		config.set('mysql', 'address', address)
		config.set('mysql', 'username', username)
		config.set('mysql', 'password', password)
		config.set('mysql', 'database', database)
	
	with open('config.ini', 'wb') as configfile:
		config.write(configfile)
else:
	print 'Configuration file already exists. Skipping.'

# test usenet access
nntpInfo = helper.getUsenetInfo()
try:
	socket = helper.con(*nntpInfo)
	if socket.getwelcome().startswith('200'):
		print 'Connected to usenet server, looking good!'
except NNTPError, e:
	print e
finally:
	socket.quit()

# test/setup mysql access
def checkMySQL():
	MySQLInfo = helper.getMySQLInfo()
	try:
		con = mdb.connect(*MySQLInfo)
	except mdb.Error, e:
		if e.args[0] in [2002, 1045] :
			print 'Username/password mismatch.'
			print 'We are now going to create a new account for usepy access with mysql.'
			username = raw_input('Enter the administrator username for mysql: ')
			password = getpass('Enter the administrator password for mysql: ')
			con = mdb.connect(MySQLInfo[0], username, password)
			c = con.cursor()
			c.execute("CREATE USER %s@%s IDENTIFIED BY %s", (MySQLInfo[1], MySQLInfo[0], MySQLInfo[2]))
			c.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (MySQLInfo[3]))
			ret = c.fetchone()
			if ret == None:
				c.execute("CREATE DATABASE %s" % MySQLInfo[3])
			c.execute("GRANT ALL ON %s.* TO '%s'@'%s'" % (MySQLInfo[3], MySQLInfo[1], MySQLInfo[0]))
	finally:
		try:
			if con:
				con.close()
		except NameError:
			pass
	
try:
	checkMySQL()
	MySQLInfo = helper.getMySQLInfo()
	conn = mdb.connect(*MySQLInfo)
	c = conn.cursor()

	# create parts table if it doesn't exist
	c.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s', (MySQLInfo[3], 'parts'))
	ret = c.fetchone()
	if ret[0] != 1:
		sql = '''CREATE TABLE parts (
			`id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
			`binaryID` bigint(20) unsigned NOT NULL DEFAULT '0',
			`messageID` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
			`number` bigint(20) unsigned NOT NULL DEFAULT '0',
			`partnumber` int(10) unsigned NOT NULL DEFAULT '0',
			`size` bigint(20) unsigned NOT NULL DEFAULT '0',
			`dateadded` datetime DEFAULT NULL,
			PRIMARY KEY(`id`),
			KEY `binaryID` (`binaryID`),
			KEY `ix_parts_dateadded` (`dateadded`),
			KEY `ix_parts_number` (`number`)
			)'''
		c.execute(sql)
		print 'Parts table created.'

	# create binaries table if it doesn't exist
	c.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s', (MySQLInfo[3], 'binaries'))
	ret = c.fetchone()
	if ret[0] != 1:
		sql = '''CREATE TABLE `binaries` (
			`ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
			`name` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
			`fromname` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
			`date` datetime DEFAULT NULL,
			`xref` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
			`totalParts` int(11) unsigned NOT NULL DEFAULT '0',
			`groupID` int(11) unsigned NOT NULL DEFAULT '0',
			`procstat` int(11) DEFAULT '0',
			`procattempts` int(11) DEFAULT '0',
			`categoryID` int(11) DEFAULT NULL,
			`regexID` int(11) DEFAULT NULL,
			`reqID` int(11) DEFAULT NULL,
			`relpart` int(11) DEFAULT '0',
			`reltotalpart` int(11) DEFAULT '0',
			`binaryhash` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
			`relname` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
			`importname` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
			`releaseID` int(11) DEFAULT NULL,
			`dateadded` datetime DEFAULT NULL,
			PRIMARY KEY (`ID`),
			KEY `fromname` (`fromname`),
			KEY `date` (`date`),
			KEY `groupID` (`groupID`),
			KEY `ix_binary_relname` (`relname`),
			KEY `ix_binary_releaseID` (`releaseID`),
			KEY `ix_binary_dateadded` (`dateadded`),
			KEY `ix_binary_binaryhash` (`binaryhash`),
			KEY `ix_binary_releaseID_relpart` (`releaseID`,`relpart`)
			)'''
		c.execute(sql)
		conn.commit()
		print 'Binaries table created.'		
	# create collections table if it doesn't exist
	c.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s', (MySQLInfo[3], 'collections'))
	ret = c.fetchone()
	if ret[0] != 1:
		sql = '''CREATE TABLE `collections` (
                `ID` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
                `name` VARCHAR(255) NOT NULL DEFAULT '',
                `subject` VARCHAR(255) NOT NULL DEFAULT '',
                `fromname` VARCHAR(255) NOT NULL DEFAULT '',
                `date` DATETIME DEFAULT NULL,
                `xref` VARCHAR(255) NOT NULL DEFAULT '',
                `totalFiles` INT(11) UNSIGNED NOT NULL DEFAULT '0',
                `groupID` INT(11) UNSIGNED NOT NULL DEFAULT '0',
                `collectionhash` VARCHAR(255) NOT NULL DEFAULT '0',
                `dateadded` DATETIME DEFAULT NULL,
                `filecheck` INT(11) UNSIGNED NOT NULL DEFAULT '0',
                `filesize` BIGINT UNSIGNED NOT NULL DEFAULT '0',
                `releaseID` INT NULL,
                PRIMARY KEY  (`ID`),
                KEY `fromname` (`fromname`),
                KEY `date` (`date`),
                KEY `groupID` (`groupID`)
                )'''
		c.execute(sql)
		conn.commit()
		print 'Collections table created.'

	# create groups table if it doesn't exist
	c.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s', (MySQLInfo[3], 'groups'))
	ret = c.fetchone()
	if ret[0] != 1:
		sql = '''CREATE TABLE `groups` (
			`ID` int(11) NOT NULL AUTO_INCREMENT,
			`name` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
			`backfill_target` int(4) NOT NULL DEFAULT '1',
			`first_record` bigint(20) unsigned NOT NULL DEFAULT '0',
			`first_record_postdate` datetime DEFAULT NULL,
			`last_record` bigint(20) unsigned NOT NULL DEFAULT '0',
			`last_record_postdate` datetime DEFAULT NULL,
			`last_updated` datetime DEFAULT NULL,
			`minfilestoformrelease` int(4) DEFAULT NULL,
			`minsizetoformrelease` bigint(20) DEFAULT NULL,
			`active` tinyint(1) NOT NULL DEFAULT '0',
			`description` varchar(255) COLLATE utf8_unicode_ci DEFAULT '',
			PRIMARY KEY (`ID`),
			UNIQUE KEY `name` (`name`),
			KEY `active` (`active`)
			)'''
		c.execute(sql)
		conn.commit()
		print 'groups table created.'

		# populate groups table, even though we'll probably only enable 3 of these fuckers
		c.executemany('''INSERT INTO groups (name) VALUES (%s)''', (
		['alt.binaries.0day.stuffz', 'alt.binaries.anime', 'alt.binaries.apps.stuffz', 'alt.binaries.ath', 'alt.binaries.audio.warez', 
		'alt.binaries.b4e', 'alt.binaries.big', 'alt.binaries.bloaf', 'alt.binaries.blu-ray', 'alt.binaries.cd.image', 'alt.binaries.cd.image.linux', 
		'alt.binaries.cd.lossless', 'alt.binaries.classic.tv.shows', 'alt.binaries.comics.dcp', 'alt.binaries.comp', 'alt.binaries.console.ps3', 
		'alt.binaries.cores', 'alt.binaries.country.mp3', 'alt.binaries.dc', 'alt.binaries.dgma', 'alt.binaries.documentaries', 'alt.binaries.drummers', 
		'alt.binaries.dvd.movies', 'alt.binaries.dvdr', 'alt.binaries.e-book', 'alt.binaries.e-book.flood', 'alt.binaries.e-book.technical', 
		'alt.binaries.ebook', 'alt.binaries.erotica', 'alt.binaries.erotica.divx', 'alt.binaries.etc', 'alt.binaries.ftn', 'alt.binaries.games', 
		'alt.binaries.games.nintendods', 'alt.binaries.games.wii', 'alt.binaries.games.xbox', 'alt.binaries.games.xbox360', 'alt.binaries.ghosts', 
		'alt.binaries.global.quake', 'alt.binaries.hdtv', 'alt.binaries.hdtv.x264', 'alt.binaries.highspeed', 'alt.binaries.hou', 'alt.binaries.ijsklontje', 
		'alt.binaries.illuminaten', 'alt.binaries.inner-sanctum', 'alt.binaries.ipod.videos', 'alt.binaries.karagarga', 'alt.binaries.linux', 
		'alt.binaries.linux.iso', 'alt.binaries.mac', 'alt.binaries.misc', 'alt.binaries.mma', 'alt.binaries.mom', 'alt.binaries.moovee', 
		'alt.binaries.movies', 'alt.binaries.movies.divx', 'alt.binaries.movies.divx.french', 'alt.binaries.movies.erotica', 'alt.binaries.movies.french', 
		'alt.binaries.movies.xvid', 'alt.binaries.mp3', 'alt.binaries.mp3.audiobooks', 'alt.binaries.mp3.bootlegs', 'alt.binaries.mp3.full_albums', 
		'alt.binaries.mpeg.video.music', 'alt.binaries.multimedia', 'alt.binaries.multimedia.anime', 'alt.binaries.multimedia.anime.highspeed', 
		'alt.binaries.multimedia.anime.repost', 'alt.binaries.multimedia.cartoons', 'alt.binaries.multimedia.classic-films', 
		'alt.binaries.multimedia.comedy.british', 'alt.binaries.multimedia.disney', 'alt.binaries.multimedia.documentaries', 
		'alt.binaries.multimedia.erotica.amateur', 'alt.binaries.multimedia.sitcoms', 'alt.binaries.multimedia.sports', 'alt.binaries.multimedia.tv', 
		'alt.binaries.music.flac', 'alt.binaries.music.opera', 'alt.binaries.nintendo.ds', 'alt.binaries.nospam.cheerleaders', 'alt.binaries.pictures.comics.complete', 
		'alt.binaries.pictures.comics.dcp', 'alt.binaries.pictures.comics.repost', 'alt.binaries.pictures.comics.reposts', 'alt.binaries.pro-wrestling', 
		'alt.binaries.scary.exe.files', 'alt.binaries.sony.psp', 'alt.binaries.sound.audiobooks', 'alt.binaries.sound.mp3', 'alt.binaries.sounds.1960s.mp3', 
		'alt.binaries.sounds.1970s.mp3', 'alt.binaries.sounds.audiobooks.repost', 'alt.binaries.sounds.country.mp3', 'alt.binaries.sounds.flac', 
		'alt.binaries.sounds.flac.jazz', 'alt.binaries.sounds.jpop', 'alt.binaries.sounds.lossless', 'alt.binaries.sounds.lossless.1960s', 'alt.binaries.sounds.lossless.classical', 
		'alt.binaries.sounds.lossless.country', 'alt.binaries.sounds.midi', 'alt.binaries.sounds.mp3', 'alt.binaries.sounds.mp3.1950s', 'alt.binaries.sounds.mp3.1970s', 
		'alt.binaries.sounds.mp3.1980s', 'alt.binaries.sounds.mp3.1990s', 'alt.binaries.sounds.mp3.2000s', 'alt.binaries.sounds.mp3.acoustic', 'alt.binaries.sounds.mp3.bluegrass', 
		'alt.binaries.sounds.mp3.christian', 'alt.binaries.sounds.mp3.classical', 'alt.binaries.sounds.mp3.comedy', 'alt.binaries.sounds.mp3.complete_cd', 
		'alt.binaries.sounds.mp3.country', 'alt.binaries.sounds.mp3.dance', 'alt.binaries.sounds.mp3.disco', 'alt.binaries.sounds.mp3.emo', 'alt.binaries.sounds.mp3.full_albums', 
		'alt.binaries.sounds.mp3.heavy-metal', 'alt.binaries.sounds.mp3.jazz', 'alt.binaries.sounds.mp3.jazz.vocals', 'alt.binaries.sounds.mp3.musicals', 
		'alt.binaries.sounds.mp3.nospam', 'alt.binaries.sounds.mp3.opera', 'alt.binaries.sounds.mp3.progressive-country', 'alt.binaries.sounds.mp3.rap-hiphop', 
		'alt.binaries.sounds.mp3.rap-hiphop.full-albums', 'alt.binaries.sounds.mp3.rock', 'alt.binaries.sounds.ogg', 'alt.binaries.sounds.radio.bbc', 'alt.binaries.sounds.radio.british', 
		'alt.binaries.sounds.utilites', 'alt.binaries.sounds.whitburn.pop', 'alt.binaries.teevee', 'alt.binaries.test', 'alt.binaries.town', 'alt.binaries.tv', 'alt.binaries.tv.deutsch', 
		'alt.binaries.tvseries', 'alt.binaries.u-4all', 'alt.binaries.u4all', 'alt.binaries.uzenet', 'alt.binaries.warez', 'alt.binaries.warez.ibm-pc.0-day', 'alt.binaries.warez.quebec-hackers', 
		'alt.binaries.warez.smartphone', 'alt.binaries.warez.uk.mp3', 'alt.binaries.wb', 'alt.binaries.wii', 'alt.binaries.wii.gamez', 'alt.binaries.wmvhd', 'alt.binaries.worms', 
		'alt.binaries.x', 'alt.binaries.x264', 'alt.binaries.xbox360.gamez', 'comp.os.linux.development.apps', 'comp.os.linux.misc', 'comp.os.linux.networking', 
		'de.alt.sources.linux.patches', 'dk.binaer.film', 'dk.binaer.tv']))
		conn.commit()
		print 'Populated groups table.'
	

except mdb.Error, e:
	print "Error: %d: %s" % (e.args[0], e.args[1])
	sys.exit(1)
finally:
	try:
		conn.close()
	except:
		pass
