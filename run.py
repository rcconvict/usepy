#!/usr/bin/env python
import utils.db as db
import utils.helper as helper
from pprint import pprint

NNTP_INFO = helper.getUsenetInfo()
socket = helper.con(*NNTP_INFO)

# get the welcome msg
print socket.getwelcome()

# change group and get info
_, _, first, last, _ = socket.group('alt.binaries.x264')

# get groupID and last local article
gid = db.getGroupID('alt.binaries.x264')
lastDBArticle = db.getLastArticle(gid)

# get last 100 articles on server if we don't ahve any
if lastDBArticle == 0:
	lastDBArticle = last - 100

# get article headers and add them to the DB
resp, overviews = socket.over((lastDBArticle, last))
db.addParts(gid, overviews)

# update the group with new info
db.updateGroup(gid, last)

# CLOSE THE SOCKET FOR THE LOVE OF GOD CLOSE THE FUCKING SOCKET
socket.quit()

# stats
print 'Last local article num: %s' % lastDBArticle
print 'Last server article num: %s' % last
print 'Added %d parts.' % (last-lastDBArticle)
