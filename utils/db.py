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

	def queryInsert(self, query, returnlastid=True):
		if query == '':
			return False

		self.c.execute(query)
		return self.conn.insert_id() if returnlastid else c.fetchall()

	def escapeString(self, str):
		return "'"+self.conn.escape_string(str)+"'"

	def getInsertID(self):
		return self.conn.insert_id()

	def getAffectedRows(self):
		return self.conn.affected_rows()

	def queryOneRow(self, query):
		rows = self.query(query)

		if rows == None:
			return False

		return rows[0]

	def query(self, query):
		if query == '':
			return False

		self.c.execute(query)
		return self.c.fetchall()

	def queryDirect(self, query):
		return false if query == '' else self.query(query)

	def getNumRows(self):
		#self.c.execute(query)
		return self.c.rowcount		

	def setAutoCommit(self):
		self.conn.autocommit(True)

	def commit(self):
		self.conn.commit()

	def rollback(self):
		self.conn.rollback()

	def close(self):
		self.conn.commit()
		self.conn.close()
