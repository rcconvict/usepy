#!/usr/bin/env python
import sys

class Consoletools():
	def __init__(self):
		self.lastMessageLength = 0

	def overWrite(self, message, reset=False):
		if reset:
			self.lastMessageLength = 0

		sys.stdout.flush()

		self.lastMessageLength = len(message)
		sys.stdout.write('\r'+message)

	def percentString(self, cur, total):
		percent = 100 * cur / total
		formatString = ' %d/%d (%2d%%)' % (cur, total, percent)

		if cur == total:
			formatString = formatString+'\n'

		return formatString

	def convertTime(self, seconds):
		if seconds < 60:
			return '%d second(s)' % seconds
		if seconds > 60 and seconds < 3600:
			return '%d minute(s)' % round(seconds/60)
		if seconds > 3600:
			return '%d hour(s)' % round(seconds/3600)
