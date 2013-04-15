#!/usr/bin/env python
import utils.db as db
import utils.helper as helper
from pprint import pprint

NNTP_INFO = helper.getUsenetInfo()
socket = helper.con(*NNTP_INFO)

# get the welcome msg
print socket.getwelcome()

_, _, first, last, _ = socket.group('alt.binaries.x264')
# update groups table here
gid = db.getGroupID('alt.binaries.x264')
lastDBArticle = db.getLastArticle(gid)

if lastDBArticle == 0:
	lastDBArticle = last - 100

resp, overviews = socket.over((lastDBArticle, last))
db.addParts(gid, overviews)
db.updateGroup(gid, last)

# CLOSE THE SOCKET FOR THE LOVE OF GOD CLOSE THE FUCKING SOCKET
socket.quit()

print 'Last local article num: %s' % lastDBArticle
print 'Last server article num: %s' % last
print 'Added %d parts.' % (last-lastDBArticle)
