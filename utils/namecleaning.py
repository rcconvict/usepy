#!/usr/bin/env python
import re, sys

def unfuckString(subject):
	try:
		return subject.decode('ascii', 'ignore').encode('ascii', 'ignore')
	except:
		try:
			return subject.encode('ascii', 'ignore')
		except:
			ans = raw_input('Unable to unfuck string. Drop into a shell? ')
			if ans.lower() in ['y', 'yes']:
				import pdb; pdb.set_trace()
			else:
				print 'Nothing else to do. Exiting.'
				sys.exit()

def collectionsCleaner(subject, type='normal'):
	subject = unfuckString(subject)
	# parts/files
	cleanSubject = re.sub('(\(|\[|\s)\d{1,4}(\/|(\s|_)of(\s|_)|\-)\d{1,4}(\)|\]|\s)|\(\d{1,3}\|\d{1,3}\)|\-\d{1,3}\-\d{1,3}\.|\s\d{1,3}\sof\s\d{1,3}\.|\s\d{1,3}\/\d{1,3}|\d{1,3}of\d{1,3}\.', '', subject, re.IGNORECASE)
	# Anything between the quotes. Too much variance within the quotes, so remove it completely
	cleanSubject = re.sub('\".+\"', '', cleanSubject, re.IGNORECASE)
	# file extensions
	cleanSubject = re.sub('(\.part(\d{1,5})?)?\.(7z|\d{3}(?=(\s|"))|avi|idx|jpg|mp4|nfo|nzb|par\s?2|pdf|rar|rev|r\d\d|sfv|srs|srr|sub|txt|vol.+(par2)|zip|z{2})"?|\d{2,3}\s\-\s.+\.mp3|(\s|(\d{2,3})?\-)\d{2,3}\.mp3|\d{2,3}\.pdf|\.part\d{1,4}\.', '', cleanSubject, re.IGNORECASE)
	# file sizes - non unique ones
	cleanSubject = re.sub('\d{1,3}(,|\.|\/)\d{1,3}\s(k|m|g)b|(\])?\s\d{1,}KB\s(yENC)?|"?\s\d{1,}\sbytes|(\-\s)?\d{1,}(\.|,)?\d{1,}\s(g|k|m)?B\s\-?(\s?yenc)?|\s\(d{1,3},\d{1,3}\s{K,M,G}B\)\s', '', cleanSubject, re.IGNORECASE)
	# random stuff
	cleanSubject = re.sub('AutoRarPar\d{1,5}', '', cleanSubject, re.IGNORECASE).strip()
	cleansubject = re.sub('\s\s+', '', cleanSubject)

	if type == 'split':
		one = two = ''
		matches = re.search('"(.+?)\.[a-z0-9].+?"', subject, re.IGNORECASE)
		if matches:
			one = matches.groups()[0]
		matches2 = re.search('\d{1,3}[.-_ ]?(e|d)\d{1,3}|EP[\.\-_ ]?\d{1,3}[\.\-_ ]|[a-z0-9\.\-_ \(\[\)\]{}<>,"\'\$^\&\*\!](19|20)\d\d[a-z0-9\.\-_ \(\[\)\]{}<>,"\'\$^\&\*\!]', subject, re.IGNORECASE)
		if matches2:
			two = matches2.groups()[1]
		return cleansubject+one+two
	elif type != 'split' and len(cleansubject) <= 7 or re.search('^[a-z0-9 \-\$]{1,9}$', cleansubject):
		one = two = ''
		matches = re.search('.+?"(.+?)".+?".+?".+', subject)
		if matches:
			one = matches.groups()[1]
		matches = re.search('(^|.+)"(.+?)(\d{2,3} ?\(\d{4}\).+?)?\.[a-z0-9].+?"', subject, re.IGNORECASE)
		if matches:
			one = matches.groups()[2]
		matches2 = re.search('\d{1,3}[.-_ ]?(e|d)\d{1,3}|EP[\.\-_ ]?\d{1,3}[\.\-_ ]|[a-z0-9\.\-_ \(\[\)\]{}<>,"\'\$^\&\*\!](19|20)\d\d[a-z0-9\.\-_ \(\[\)\]{}<>,"\'\$^\&\*\!]', subject)
		if matches2:
			two = matches2.groups()[0]
		if not one and not two:
			newname = re.sub('[a-z0-9]', '', subject)
			matches3 = re.search('[\!@#\$%\^&\*\(\)\-={}\[\]\|\\:;\'<>\,\?\/_ ]{1,3}', newname)
			if matches3:
				return cleansubject+matches3.groups()[0]
		else:
			return cleansubject+one+two
	else:
		return cleanSubject

def releaseCleaner(subject):
	subject = unfuckString(subject)
	# file and part count
	cleanerName = re.sub('(\(|\[|\s)\d{1,4}(\/|(\s|_)of(\s|_)|\-)\d{1,4}(\)|\]|\s)|\(\d{1,3}\|\d{1,3}\)|\-\d{1,3}\-\d{1,3}\.|\s\d{1,3}\sof\s\d{1,3}\.|\s\d{1,3}\/\d{1,3}|\d{1,3}of\d{1,3}\.', '', subject, re.IGNORECASE)
	# size
	cleanerName = re.sub('\d{1,3}(\.|,)\d{1,3}\s(K|M|G)B|\d{1,}(K|M|G)B|\d{1,}\sbytes|(\-\s)?\d{1,}(\.|,)?\d{1,}\s(g|k|m)?B\s\-(\syenc)?|\s\(d{1,3},\d{1,3}\s{K,M,G}B\)\s', '', cleanerName, re.IGNORECASE)
	# extensions
	cleanerName = re.sub('(\.part(\d{1,5})?)?\.(7z|\d{3}(?=(\s|"))|avi|epub|idx|jpg|mobi|mp4|nfo|nzb|par\s?2|pdf|rar|rev|r\d\d|sfv|srs|srr|sub|txt|vol.+(par2)|zip|z{2})"?|(\s|(\d{2,3})?\-)\d{2,3}\.mp3|\d{2,3}\.pdf|yEnc|\.part\d{1,4}\.', '', cleanerName, re.IGNORECASE)
	# unwanted shit
	cleanerName = re.sub('SECTIONED brings you|usenet\-space\-cowboys\.info|<.+https:\/\/secretusenet\.com>|> USC <|\[\d{1,}\]\-\[FULL\].+#a\.b[\w.#!@$%^&*\(\){}\|\\:"\';<>,?~` ]+\]|brothers\-of\-usenet\.info(\/\.net)?|Partner von SSL\-News\.info|AutoRarPar\d{1,5}', '', cleanerName, re.IGNORECASE)
	# remove some chars
	crapChars = '''<>"=[](){}'''
	cleanerName = cleanerName.translate(None, crapChars)
	# replace some characters with 1 space
	commonChars = ['.', '_', '-', '|']
	for i in commonChars:
		cleanerName = cleanerName.replace(i, ' ')
	# replace multiple spaces with 1 space
	cleanerName = re.sub('\s\s+', ' ', cleanerName, re.IGNORECASE).strip()

	return cleanerName

def fixerCleaner(name):
	subject = unfuckString(subject)
	# extensions
	cleanerName = re.sub('(\.part(\d{1,5})?)?\.(7z|\d{3}(?=(\s|"))|avi|epub|exe|idx|jpg|mobi|mp4|nfo|nzb|par\s?2|pdf|rar|rev|r\d\d|sfv|srs|srr|sub|txt|vol.+(par2)|zip|z{2})"?|\d{2,3}\.pdf|yEnc|\.part\d{1,4}\.', '', name, re.IGNORECASE)
	# remove some chars	
	crapChars = '''<>"=[](){}'''
	cleanerName = cleanerName.translate(None, crapChars)
	# replace some characters with 1 space
	commonChars = ['.', '_', '-', '|']
	for i in commonChars:
		cleanerName = cleanerName.replace(i, ' ')
	# replace multiple spaces with 1 space
	cleanerName = re.sub('\s\s+', ' ', cleanerName, re.IGNORECASE).strip()

	return cleanerName		
