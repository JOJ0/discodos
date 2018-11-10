#!/usr/local/bin/python3
# pip install discogs_client

from discodos import db
#from discodos.utils import *
from discodos.utils import *
import discogs_client
import csv
import time
import datetime
import argparse
import sys

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")
    parser_group1 = parser.add_mutually_exclusive_group()
    parser_group1.add_argument(
		"-i", "--import", dest="release_id",
        type=int, default=0, nargs="*",
        help="import release ID from Discogs, default is _all_ releases")
    parser_group1.add_argument(
		"-u", "--update-db", dest="update_db",
        action="store_true",
        help="update database schema FIXME randomly coded in when neeeded")
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -v.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

# main program
def main():
    args=argparser(sys.argv)
    print_help(
      "This script sets up the DISCOBASE, and imports data from Discogs")
    log.info(vars(args))
    #print(vars(args))

    # DB setup
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")
    sql_settings = "PRAGMA foreign_keys = ON;"

    if args.update_db:
        print("Updating DB schema - EXPERIMENTAL")
        sql_settings = "PRAGMA foreign_keys = OFF;"
        db.create_table(conn, sql_settings)
        #sql_alter_something = """ALTER TABLE mix_track
        #                                 FOREIGN KEY (mix_id)
        #                                    REFERENCES mix(mix_id)
        #                                 ON DELETE CASCADE
        #                                 ON UPDATE CASCADE
        #                                ; """
        #db.create_table(conn, sql_alter_something)
        sql_settings = "PRAGMA foreign_keys = ON;"
        print("DB schema update DONE - EXPERIMENTAL")
        raise SystemExit(0)

    sql_create_release_table = """ CREATE TABLE IF NOT EXISTS release (
                                       discogs_id INTEGER PRIMARY KEY ON CONFLICT REPLACE,
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
                                         d_track_no TEXT NOT NULL,
                                         track_pos INTEGER NOT NULL,
                                         trans_rating TEXT,
                                         trans_notes TEXT,
                                         FOREIGN KEY (mix_id)
                                            REFERENCES mix(mix_id)
                                         ON DELETE CASCADE
                                         ON UPDATE CASCADE

                                        ); """
    sql_create_track_table = """ CREATE TABLE IF NOT EXISTS track (
                                     d_release_id INTEGER NOT NULL,
                                     d_track_no TEXT NOT NULL,
                                     d_track_name TEXT,
                                     import_timestamp TEXT,
                                     PRIMARY KEY (d_release_id, d_track_no)
                                     ); """

                                           # We had this constraint before
                                           # FOREIGN KEY (d_release_id)
                                           #     REFERENCES release(d_discogs_id)
    # extend discogs track info with these fields
    sql_create_track_ext_table = """ CREATE TABLE IF NOT EXISTS track_ext (
                                         d_release_id INTEGER NOT NULL,
                                         d_track_no TEXT NOT NULL,
                                         key TEXT,
                                         key_notes TEXT,
                                         bpm INTEGER,
                                         notes TEXT,
                                         PRIMARY KEY (d_release_id, d_track_no)
                                        ); """
                                        #FOREIGN KEY (d_release_id)
                                        #    REFERENCES track(d_release_id)
                                        #FOREIGN KEY (d_track_no)
                                        #    REFERENCES track(d_track_no)
    db.create_table(conn, sql_settings)
    db.create_table(conn, sql_create_release_table)
    db.create_table(conn, sql_create_mix_table)
    db.create_table(conn, sql_create_mix_track_table)
    db.create_table(conn, sql_create_track_table)
    db.create_table(conn, sql_create_track_ext_table)
    # in INFO level show args object again after longish create_table msgs
    log.info(vars(args))

    # IMPORT MODE, if we said so
    if hasattr(args, "release_id"):
        # PREPARE DISCOGS API
        try:
            userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
            d = discogs_client.Client(
                    "J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                    user_token=userToken)
            me = d.identity()
        except HTTPError:
            print("Can't connect do Discogs! HTTPError. Quitting.")
            raise SystemExit(1)
        except Exception:
            print("Can't connect do Discogs! Quitting")
            raise SystemExit(1)

        # IMPORT OF WHOLE COLLECTION is the default
        if 0 in args.release_id or len(args.release_id) == 0:
            print(
            "Gathering collection and putting necessary fields into DISCOBASE")
            insert_count = 0
            for r in me.collection_folders[0].releases:
                rate_limit_slow_downer(d, remaining=5, sleep=2)
                print("Release :", r.release.id, "-", r.release.title)
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
                    log.info("discogs-rate-limit-remaining: %s\n",
                             d._fetcher.rate_limit_remaining)
                else:
                    print_help("Something wrong while importing \""+
                               r.release.title+"\"")
        else:
            # IMPORT SPECIFIC RELEASE ID
            #print(dir(me.collection_folders[0].releases))
            #print(dir(me))
            #print(me.collection_item)
            print_help("Asking Discogs for release ID {:d}".format(
                   args.release_id[0]))
            result = d.release(args.release_id[0])
            print_help("Release ID is valid: "+result.title+"\n"+
                       "Let's see if it's in your collection...)")

            for r in me.collection_folders[0].releases:
                #rate_limit_slow_downer(d, remaining=5, sleep=2)
                if r.release.id == args.release_id[0]:
                    print("Found it:", r.release.id, "-", r.release.title)
                    print("Importing to DISCOBASE.\n")
                    last_row_id = db.create_release(conn, r)
                    break
            if not last_row_id:
                print_help("This is not the release you are looking for!")

    conn.commit()
    conn.close()
    print("Done!")


# __main__ try/except wrap
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.error('Program interrupted!')


################# old stuff leave for reference ####################
def old_fold_away():
    print("crap")
    #itemsInCollection = [r.release for r in me.collection_folders[0].releases]
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

