#!/usr/bin/env python
from dateutil.parser import parse

class Backfill():
	def __init__(self):
		self.n = "\n"

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
