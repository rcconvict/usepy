#!/usr/bin/env python
import db, os

class Sites():
	def __init__(self):
		REGISTER_STATUS_OPEN = 0
		REGISTER_STATUS_INVITE = 1
		REGISTER_STATUS_CLOSED = 0
		REGISTER_STATUS_API_ONLY = 3

		ERR_BADUNRARPATH = -1
		ERR_BADFFMPEGPATH = -2
		ERR_BADMEDIAINFOPATH = -3
		ERR_BADNZBPATH = -4
		ERR_DEEPNOUNRAR = -5
		ERR_BADTMPUNRARPATH = -6

	def version(self):
		return '0.0.1'

	def update(self, form):
		mdb = db.DB()
		site = self.row2Object(form)

		if site['nzbpath'][-1] != '/':
			site['nzbpath'] = site['nzbpath']+'/'

		# validate site settings
		if site['mediainfopath'] != '' and not os.path.isfile(site['mediainfopath']):
			return self.ERR_BADMEDIAINFOPATH

		if site['ffmpegpath'] != '' and not os.path.isfile(site['mediainfopath']):
			return self.ERR_BADFFMPEGPATH

		if site['unrarpath'] != '' and not os.path.isfile(site['unrarpath']):
			return self.ERR_BADUNRARPATH

		if site['nzbpath'] != '' and not os.path.isdir(site['nzbpath']):
			return self.ERR_BADNZBPATH

		if site['checkpasswordedrar'] == 1 and not os.path.isfile(site['unrarpath']):
			return self.ERR_BADTMPUNRARPATH

		if site['tmpunrarpath'] != '' and not os.path.isfile(site['tmpunrarpath']):
			return self.ERR_BADTMPUNRARPATH

		sql = sqlKeys = dict()

		for settingK, settingV in form.iteritems():
			sql.append('WHEN %s THEN %s' % (mdb.escapeString(settingK), mdb.escapeString(settingV)))
			sqlKeys.append(mdb.escapeString(settingK))

		mdb.query('UPDATE site SET value = CASE setting %s END WHERE setting IN (%s)', (' '.join(sql), ', '.join(sqlKeys)))

		return site

	def get(self):
		mdb = db.DB()
		rows = mdb.query('SELECT * FROM site')

		if rows is None:
			return False

		return self.rows2Object(rows)

	def rows2Object(self, rows):
		# becuase objects are better than arrays I guess
		obj = dict()
		for row in rows:
			obj[row['setting']] = row['value']

		obj['version'] = self.version()
		return obj

	def row2Object(self, row):
		obj = dict()
		for key in rows.keys():
			obj[key] = row[key]

		return obj

	def getLicense(self, html=False):
		n = '\r\n' if not html else '<br/>'
		return n+'usepy '+self.version()+n+'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation.".$n."

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.'''+n
