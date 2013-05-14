#!/usr/bin/env python
import utils.db as db
import utils.helper as helper
from update_groups import updateGroup
import datetime, sys, threading, Queue
try:
	from dateutil.parser import parse
except ImportError:
	print 'Install the dateutil python package.'
	sys.exit(-1)

print 'this file needs to be updated to run with the new binaries setup. exiting.'
sys.exit()

def worker():
	#while True:
		item = q.get()
		updateGroup(item)
		q.task_done()

q = Queue.Queue()

activeGroups = db.getActiveGroups()
if len(activeGroups) == 0:
	print 'There are no active groups. You can activate some with control.py.'
	sys.exit()

for i in xrange(len(activeGroups)):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

for item in activeGroups:
	q.put(item)

q.join() # block until all groups are updated
