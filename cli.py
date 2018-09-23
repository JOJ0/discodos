#!/usr/local/bin/python3

from discodos import db
import discogs_client
import csv
import time
#import sqlite3
#from sqlite3 import Error
import datetime

conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")


# discogs api connection
userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
d = discogs_client.Client("CollectionGenreClassifier/0.1 +http://github.com/JOJ0",
                          user_token=userToken)

# DEBUG: show all releases from sqlite
db.all_releases(conn)

# discogs stuff
me = d.identity()
#itemsInCollection = [r.release for r in me.collection_folders[0].releases]

#for r in me.collection_folders[4].releases:


conn.commit()
conn.close()
print("DB closed.")
