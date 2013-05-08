#!/usr/bin/env python
import re

def collectionsCleaner(subject):
	subject = subject.encode('ascii', 'ignore')
	# parts/files
	cleanSubject = re.sub('(\(|\[|\s)\d{1,4}(\/|(\s|_)of(\s|_)|\-)\d{1,4}(\)|\]|\s)|\(\d{1,3}\|\d{1,3}\)|\-\d{1,3}\-\d{1,3}\.|\s\d{1,3}\sof\s\d{1,3}\.|\s\d{1,3}\/\d{1,3}|\d{1,3}of\d{1,3}\./i', '', subject)
	# Anything between the quotes. Too much variance within the quotes, so remove it completely
	cleanSubject = re.sub('\".+\"/i', '', cleanSubject)
	# file extensions
	cleanSubject = re.sub('(\.part(\d{1,5})?)?\.(7z|\d{3}(?=(\s|"))|avi|idx|jpg|mp4|nfo|nzb|par\s?2|pdf|rar|rev|r\d\d|sfv|srs|srr|sub|txt|vol.+(par2)|zip|z{2})"?|\d{2,3}\s\-\s.+\.mp3|(\s|(\d{2,3})?\-)\d{2,3}\.mp3|\d{2,3}\.pdf|\.part\d{1,4}\./i', '', cleanSubject)
	# file sizes - non unique ones
	cleanSubject = re.sub('\d{1,3}(,|\.|\/)\d{1,3}\s(k|m|g)b|(\])?\s\d{1,}KB\s(yENC)?|"?\s\d{1,}\sbytes|(\-\s)?\d{1,}(\.|,)?\d{1,}\s(g|k|m)?B\s\-?(\s?yenc)?|\s\(d{1,3},\d{1,3}\s{K,M,G}B\)\s/i', '', cleanSubject)
	# random stuff
	cleanSubject = re.sub('AutoRarPar\d{1,5}/i', '', cleanSubject).strip()

	return cleanSubject

def releaseCleaner(subject):
	subject = subject.encode('ascii', 'ignore')
	# file and part count
	cleanerName = re.sub('(\(|\[|\s)\d{1,4}(\/|(\s|_)of(\s|_)|\-)\d{1,4}(\)|\]|\s)|\(\d{1,3}\|\d{1,3}\)|\-\d{1,3}\-\d{1,3}\.|\s\d{1,3}\sof\s\d{1,3}\.|\s\d{1,3}\/\d{1,3}|\d{1,3}of\d{1,3}\./i', '', subject)
	# size
	cleanerName = re.sub('\d{1,3}(\.|,)\d{1,3}\s(K|M|G)B|\d{1,}(K|M|G)B|\d{1,}\sbytes|(\-\s)?\d{1,}(\.|,)?\d{1,}\s(g|k|m)?B\s\-(\syenc)?|\s\(d{1,3},\d{1,3}\s{K,M,G}B\)\s/i', '', cleanerName)
	# extensions
	cleanerName = re.sub('(\.part(\d{1,5})?)?\.(7z|\d{3}(?=(\s|"))|avi|epub|idx|jpg|mobi|mp4|nfo|nzb|par\s?2|pdf|rar|rev|r\d\d|sfv|srs|srr|sub|txt|vol.+(par2)|zip|z{2})"?|(\s|(\d{2,3})?\-)\d{2,3}\.mp3|\d{2,3}\.pdf|yEnc|\.part\d{1,4}\./i', '', cleanerName)
	# unwanted shit
	cleanerName = re.sub('SECTIONED brings you|usenet\-space\-cowboys\.info|<.+https:\/\/secretusenet\.com>|> USC <|\[\d{1,}\]\-\[FULL\].+#a\.b[\w.#!@$%^&*\(\){}\|\\:"\';<>,?~` ]+\]|brothers\-of\-usenet\.info(\/\.net)?|Partner von SSL\-News\.info|AutoRarPar\d{1,5}/i', '', cleanerName)
	# remove some chars
	crapChars = '''<>"=[](){}'''
	cleanerName = cleanerName.translate(None, crapChars)
	# replace some characters with 1 space
	commonChars = ['.', '_', '-', '|']
	for i in commonChars:
		cleanerName = cleanerName.replace(i, ' ')
	# replace multiple spaces with 1 space
	cleanerName = re.sub('\s\s+/i', ' ', cleanerName).strip()

	return cleanerName

def fixerCleaner(name):
	subject = subject.encode('ascii', 'ignore')
	# extensions
	cleanerName = re.sub('(\.part(\d{1,5})?)?\.(7z|\d{3}(?=(\s|"))|avi|epub|exe|idx|jpg|mobi|mp4|nfo|nzb|par\s?2|pdf|rar|rev|r\d\d|sfv|srs|srr|sub|txt|vol.+(par2)|zip|z{2})"?|\d{2,3}\.pdf|yEnc|\.part\d{1,4}\./i', '', name)
	# remove some chars	
	crapChars = '''<>"=[](){}'''
	cleanerName = cleanerName.translate(None, crapChars)
	# replace some characters with 1 space
	commonChars = ['.', '_', '-', '|']
	for i in commonChars:
		cleanerName = cleanerName.replace(i, ' ')
	# replace multiple spaces with 1 space
	cleanerName = re.sub('\s\s+/i', ' ', cleanerName).strip()

	return cleanerName		
