#!/usr/local/bin/python3
# pip install discogs_client

import discogs_client
import csv
import time
import sqlite3
from sqlite3 import Error
import datetime

def db_create_conn(db_file):
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
        return conn
    except Error as e:
        print(e)
    return None

def db_create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def db_create_release(conn, release):
    #sql  = "INSERT INTO releases(discogs_id, discogs_title)"
    #sql += "    VALUES("+str(r.release.id)+", '"+str(r.release.title)+"')"
    sql  = '''INSERT INTO releases(discogs_id, discogs_title, update_date)
                    VALUES('?', '?')'''
    cur = conn.cursor()
    cur.execute('''INSERT INTO releases(discogs_id, discogs_title) VALUES(?, ?)''', (release.release.id, release.release.title))
    print("INFO: "+str(cur.rowcount))
    return cur.lastrowid

def db_all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM releases''')
    rows = cur.fetchall()
    for row in rows:
        print(row)

# DB setup 
conn = db_create_conn("/Users/jojo/git/discobar/discobar.db")
sql_create_releases_table = """ CREATE TABLE IF NOT EXISTS releases (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        discogs_id LONG,
                                        discogs_title TEXT NOT NULL,
                                        update_timestamp TEXT
                                    ); """
db_create_table(conn, sql_create_releases_table)

# discogs api connection
userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
d = discogs_client.Client("CollectionGenreClassifier/0.1 +http://github.com/JOJ0",
                          user_token=userToken)

print("Gathering collection and putting into discobar.db")
me = d.identity()
#itemsInCollection = [r.release for r in me.collection_folders[0].releases]

for r in me.collection_folders[4].releases:
    print("INSERT ID:", r.release.id, "Title:", r.release.title) 
    #release_tuple = (r.release.id,  r.release.title)
    #db_create_release(conn, release_tuple)
    last_row_id = db_create_release(conn, r)
    print("DEBUG: last_row_id:", last_row_id)
    
    #time.sleep(0.001)

db_all_releases(conn)

#rows = []

#print("Crunching data...")
#for r in itemsInCollection:
#    row = {}
#
##    try:
#    row['primaryGenre'] = r.genres[0]
#    if len(r.genres) > 1:
#        row['secondaryGenres'] = ", ".join(r.genres[1:])
#
#    row['primaryStyle'] = r.styles[0]
#    if len(r.styles) > 1:
#        row['secondaryStyles'] = ", ".join(r.styles[1:])
#
#    row['catalogNumber'] = r.labels[0].data['catno']
#    row['artists'] = ", ".join(a.name for a in r.artists)
#    row['format'] = r.formats[0]['descriptions'][0]
#
#    rows.append(row)

#    except (IndexError, TypeError):
#        None
#        # @todo: normally these exceptions only happen if there's missing data
#        # but ideally the program should check if values are missing, rather than
#        # ignoring any exception resulting from trying
#
#    row['title'] = r.title
#
#    if r.year > 0:
#        row['year'] = r.year
#
#    rows.append(row)

#print("Writing CSV...")
## Write to CSV
#with open('collection.csv', 'w') as csvfile:
#    csvfile.write('\ufeff')  # utf8 BOM needed by Excel
#
#    fieldnames = ['format', 'primaryGenre', 'primaryStyle', 'secondaryGenres',
#                  'secondaryStyles', 'catalogNumber', 'artists', 'title', 'year']
#    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='')
#
#    writer.writeheader()
#    for row in rows:
#        writer.writerow(row)

conn.close()
print("Done!")
