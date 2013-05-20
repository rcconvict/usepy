#!/usr/bin/env python
# this file is completely temporary
import sites

s = sites.Sites()

class site():
	def __init__(self):
		data = s.get()
		for setting, value in data.iteritems():
			setattr(self, setting, value)
