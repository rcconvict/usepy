#!/usr/bin/env python
import utils.db as db
import utils.binaries as binaries
import utils.nntplib as nntplib
import sys, threading, Queue

def worker():
	b = binaries.Binaries()
	groupArr = q.get()
	nntp = nntplib.connect()
	b.partRepair(nntp, groupArr)
	nntp.quit()
	q.task_done()

q = Queue.Queue()

def main():
	mdb = db.DB()
	ret = mdb.query('SELECT groupID, g.name FROM partrepair pr LEFT JOIN groups g ON pr.groupID = g.ID GROUP BY groupID')
	for i in xrange(len(ret)):
		t = threading.Thread(target=worker)
		t.daemon = True
		t.start()

	for row in ret:
		q.put({'ID' : int(row['groupID']), 'name' : row['name']})

	q.join()

if __name__ == '__main__':
	main()
