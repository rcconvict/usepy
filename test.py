#!/usr/bin/env python
import utils.db as db
gid = db.getGroupID('alt.binaries.x264')
ret = db.getLastArticle(gid)
print ret
