#!/usr/bin/env python
import MySQLdb
import MySQLdb.cursors
import helper, sys

class DB:
	def __init__(self):
		mysqlInfo = helper.getMySQLInfo()
		try:
			self.conn = MySQLdb.connect(*mysqlInfo, cursorclass=MySQLdb.cursors.DictCursor)
			self.c = self.conn.cursor()
		except MySQLdb.Error, e:
			print 'Unable to connect to database', e
			sys.exit(-1)

	def __del__(self):
		self.conn.close()
		del self.conn

	def queryInsert(self, query, kargs={}, returnlastid=True):
		if query == '':
			return False

		self.c.execute(query, kargs)
		return self.conn.insert_id() if returnlastid else c.fetchall()

	def escapeString(self, str):
		return "'"+self.conn.escape_string(str)+"'"

	def getInsertID(self):
		return self.conn.insert_id()

	def getAffectedRows(self):
		return self.conn.affected_rows()

	def queryOneRow(self, query, kargs={}):
		rows = self.query(query, kargs)

		if rows == None:
			return False

		try:
			return rows[0]
		except IndexError:
			return None

	def query(self, query, kargs={}):
		if query == '':
			return False

		self.c.execute(query, kargs)
		return self.c.fetchall()

	def queryDirect(self, query, kargs={}):
		return false if query == '' else self.query(query, kargs)

	def getNumRows(self):
		#self.c.execute(query)
		return self.c.rowcount

	def setAutoCommit(self, enabled):
		self.conn.autocommit(enabled)

	def commit(self):
		self.conn.commit()

	def rollback(self):
		self.conn.rollback()

	def close(self):
		self.conn.commit()
		self.conn.close()
