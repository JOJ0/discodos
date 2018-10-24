#!/usr/local/bin/python3
# pip install discogs_client

from discodos import log, db
import discogs_client
import csv
import time
import datetime
import argparse
import sys

def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")
    parser.add_argument(
		"-i", "--import", dest="release_import",
        action="store_true",
        help="should collection be imported from discogs")
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -v.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

args=argparser(sys.argv)
print("This script sets up db tables and eventually imports from Discogs into DISCOBASE")

# DB setup 
conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")
sql_settings = "PRAGMA foreign_keys = ON;"
sql_create_release_table = """ CREATE TABLE IF NOT EXISTS release (
                                        discogs_id LONG PRIMARY KEY ON CONFLICT REPLACE,
                                        discogs_title TEXT NOT NULL,
                                        import_timestamp TEXT
                                    ); """
sql_create_mix_table = """ CREATE TABLE IF NOT EXISTS mix (
                                        mix_id INTEGER PRIMARY KEY,
                                        name TEXT,
                                        created TEXT,
                                        updated TEXT,
                                        played TEXT,
                                        venue TEXT
                                    ); """
sql_create_mix_track_table = """ CREATE TABLE IF NOT EXISTS mix_track (
                                        mix_track_id INTEGER PRIMARY KEY,
                                        mix_id INTEGER,
                                        d_release_id INTEGER NOT NULL,
                                        track_no TEXT NOT NULL,
                                        track_pos INTEGER NOT NULL,
                                        track_key TEXT,
                                        track_key_notes TEXT,
                                        FOREIGN KEY (mix_id) REFERENCES mix(mix_id)
                                    ); """
sql_create_track_table = """ CREATE TABLE IF NOT EXISTS track (
                                        track_id INTEGER PRIMARY KEY,
                                        d_release_id LONG NOT NULL,
                                        d_track_no TEXT NOT NULL,
                                        import_timestamp TEXT,
                                        d_track_name TEXT,
                                        FOREIGN KEY (d_release_id)
                                            REFERENCES release(d_discogs_id)
                                    ); """
# extend discogs track info with these fields
sql_create_track_ext_table = """ CREATE TABLE IF NOT EXISTS track_ext (
                                        track_id INTEGER PRIMARY KEY,
                                        key TEXT,
                                        key_notes TEXT,
                                        notes TEXT,
                                        FOREIGN KEY (track_id)
                                            REFERENCES track(track_id)
                                    ); """
db.create_table(conn, sql_settings)
db.create_table(conn, sql_create_release_table)
db.create_table(conn, sql_create_mix_table)
db.create_table(conn, sql_create_mix_track_table)
db.create_table(conn, sql_create_track_table)
db.create_table(conn, sql_create_track_ext_table)

# only import if we really want to, FIXME import takes quite some time
if args.release_import:
    # discogs api connection
    userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
    d = discogs_client.Client("J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                              user_token=userToken)
    
    print("Gathering collection and putting necessary fields into DISCOBASE")
    me = d.identity()
    #itemsInCollection = [r.release for r in me.collection_folders[0].releases]
    
    insert_count = 0
    for r in me.collection_folders[0].releases:

        if int(d._fetcher.rate_limit_remaining) < 5:
            log.info("Discogs request rate limit is about to exceed,\
                      let's wait a bit: %s\n",
                         d._fetcher.rate_limit_remaining)
            time.sleep(2)

        print("Release ID:", r.release.id, ", Title:", r.release.title)
        #vars(r.release)
        #for track in r.release.tracklist:
        #    log.debug("Track:", track)
            #time.sleep(0.2)
        last_row_id = db.create_release(conn, r)
        # FIXME I don't know if cur.lastrowid is False if unsuccessful
        if last_row_id:
            #log.info("last_row_id: %s", last_row_id)
            insert_count = insert_count + 1
            print("Created so far:", insert_count, "")
            log.info("discogs-rate-limit-remaining: %s\n", d._fetcher.rate_limit_remaining)
        else:
            print_help("Something wrong while importing \""+r.release.title+"\"")
    
    #db.all_releases(conn)
    
    conn.commit()
    conn.close()
    print("Done!")



################# old stuff ####################
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

