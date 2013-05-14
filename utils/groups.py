#!/usr/bin/env python
from db import DB

def getAll():
	mdb = DB()
	return mdb.query("SELECT groups.*, COALESCE(rel.num, 0) AS num_releases FROM groups LEFT OUTER JOIN	(SELECT groupID, COUNT(ID) AS num FROM releases group by groupID) rel ON rel.groupID = groups.ID ORDER BY groups.name")

def getByID(id):
	mdb = DB()
	return mdb.queryOneRow('SELECT * FROM groups WHERE ID = %d', (id,))

def getActive():
	mdb = DB()
	return mdb.query('SELECT * FROM groups WHERE active = 1 ORDER BY name')

def getActiveByDate():
	mdb = DB()
	return mdb.query('SELECT * FROM groups WHERE active = 1 ORDER BY first_record_postdate DESC')

def getActiveIDs():
	mdb = DB()
	return mdb.query('SELECT ID FROM groups WHERE active = 1 ORDER BY name')

def getByName(grp):
	mdb = DB()
	return mdb.queryOneRow('SELECT * FROM groups WHERE name = %s', (grp,))

def getNameByID(id):
	mdb = DB()
	res = mdb.queryOneRow('SELECT * FROM groups WHERE ID = %d', (id,))
	return res['name']

def getIDByName(name):
	mdb = DB()
	res = mdb.queryOneRow('SELECT * FROM groups WHERE name = %s', (name,))
	return res['ID']

def disableForPost(name):
	mdb = DB()
	mdb.queryOneRow("update groups set first_record_postdate = %s where name = %s", ('2000-00-00 00:00:00', mdb.escapeString(name)))

def getCount(groupname=''):
	mdb = DB()

	grpsql = ''
	if groupname != '':
		grpsql += "and groups.name like %s " % mdb.escapeString("%"+groupname+"%")

	res = mdb.queryOneRow('SELECT count(ID) as num from groups where 1=1 %s', (grpsql,))
	return res['num']

def getCountActive(groupname=''):
	mdb = DB()

	grpsql = ''
	if groupname != '':
		grpsql += "and groups.name like %s " % mdb.escapeString("%"+groupname+"%")

	res = mdb.queryOneRow('SELECT count(ID) as num from groups where 1=1 %s and active = 1' % grpsql)
	return res['num']

def getCountInactive(gropuname=''):
	mdb = DB()

	grpsql = ''
	if groupname != '':
		grpsql += "and groups.name like %s " % mdb.escapeString("%"+groupname+"%")

	res = mdb.queryOneRow('SELECT count(ID) as num from groups where 1=1 %s and active = 0', (grpsql,))
	return res['num']

def delete(id):
	mdb = DB()
	return mdb.query('delete from groups where ID = %d', (id,))

def reset(id):
	mdb = DB()
	return mdb.query('update groups set backfill_target=0, first_record=0, first_record_postdate=null, last_record=0, last_record_postdate=null, active = 0, last_updated=null where ID = %d', (id,))

def resetall():
	mdb = DB()
	return mdb.query('update groups set backfill_target=0, first_record=0, first_record_postdate=null, last_record=0, last_record_postdate=null, last_updated=null, active = 0')

def updateGroupStatus(id, status=0):
	mdb = DB()
	mdb.query('UPDATE groups SET active = %s WHERE id = %s', (status, id))
	status = 'deactivated' if status == 0 else 'activated'
	return 'Group %d has been %s' % (id, status)
