#!/usr/bin/env python

import discogs_client
import csv
import time
import datetime
import argparse
import sys

from discodos.models import *
from discodos.ctrls import *
from discodos.utils import *

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increase log verbosity (-v -> INFO level, -vv DEBUG level)")
    parser.add_argument(
		"-o", "--offline", dest="offline_mode",
        action="store_true",
        help="stay in offline mode, don't connect to Discogs")
    parser_group1 = parser.add_mutually_exclusive_group()
    parser_group1.add_argument(
		"-i", "--import", dest="release_id",
        type=int, default=False, nargs="*",
        help="import release ID from Discogs, default is _all_ releases")
    parser_group1.add_argument(
		"--update-db-schema", dest="update_db_schema",
        action='store_true',
        help="update database schema - be careful! Checkout README.md")
    parser_group1.add_argument(
		"-a", "--add_to_collection", dest="add_release_id",
        type=int,
        help="add release ID to collection (on Discogs and in the DiscoBase)")
    arguments = parser.parse_args(argv[1:])
    log.info("Console log_level currently set to {} via config.yaml or default.".format(
        log.handlers[0].level))
    # Sets log level to WARN going more verbose for each new -v.
    cli_level = max(3 - arguments.verbose_count, 0) * 10
    if cli_level < log.handlers[0].level: # 10 = DEBUG, 20 = INFO, 30 = WARNING
        log.handlers[0].setLevel(cli_level)
        log.warning("Console log_level override via cli. Now set to {}.".format(
            log.handlers[0].level))
    return arguments 

# initial db setup
def create_db_tables(_db_obj):
    sql_settings = "PRAGMA foreign_keys = ON;"
    sql_create_release_table = """ CREATE TABLE release (
                                     discogs_id INTEGER PRIMARY KEY ON CONFLICT REPLACE,
                                     discogs_title TEXT NOT NULL,
                                     import_timestamp TEXT,
                                     d_artist TEXT,
                                     in_d_collection INTEGER
                                     ); """
    sql_create_mix_table = """ CREATE TABLE mix (
                                    mix_id INTEGER PRIMARY KEY,
                                    name TEXT,
                                    created TEXT,
                                    updated TEXT,
                                    played TEXT,
                                    venue TEXT
                                        ); """
    sql_create_mix_track_table = """ CREATE TABLE mix_track (
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
    sql_create_track_table = """ CREATE TABLE track (
                                     d_release_id INTEGER NOT NULL,
                                     d_track_no TEXT NOT NULL,
                                     d_track_name TEXT,
                                     import_timestamp TEXT,
                                     d_artist TEXT,
                                     PRIMARY KEY (d_release_id, d_track_no)
                                     ); """

                                           # We had this constraint before
                                           # FOREIGN KEY (d_release_id)
                                           #     REFERENCES release(d_discogs_id)
    # extend discogs track info with these fields
    sql_create_track_ext_table = """ CREATE TABLE track_ext (
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
    #try: # settings
    #    _db_obj.execute_sql(sql_settings)
    #    log.info("Adjusting sqlite settings")
    #except sqlerr as e:
    #    log.info(e.args[0])
    try: # release
        _db_obj.execute_sql(sql_create_release_table, raise_err = True)
        msg_release="CREATE TABLE 'release' was successful."
        log.info(msg_release)
        print_help(msg_release)
    except sqlerr as e:
        log.info("CREATE TABLE 'release': %s", e.args[0])
    try: # mix
        _db_obj.execute_sql(sql_create_mix_table, raise_err = True)
        msg_mix="CREATE TABLE 'mix' was successful."
        log.info(msg_mix)
        print_help(msg_mix)
    except sqlerr as e:
        log.info("CREATE TABLE 'mix': %s", e.args[0])
    try: # mix_track
        _db_obj.execute_sql(sql_create_mix_track_table, raise_err = True)
        msg_mix_track="CREATE TABLE 'mix_track' was successful."
        log.info(msg_mix_track)
        print_help(msg_mix_track)
    except sqlerr as e:
        log.info("CREATE TABLE 'mix_track': %s", e.args[0])
    try: # track
        _db_obj.execute_sql(sql_create_track_table, raise_err = True)
        msg_track="CREATE TABLE 'track' was successful."
        log.info(msg_track)
        print_help(msg_track)
    except sqlerr as e:
        log.info("CREATE TABLE 'track': %s", e.args[0])
    try: # track_ext
        _db_obj.execute_sql(sql_create_track_ext_table, raise_err = True)
        msg_track_ext="CREATE TABLE 'track_ext' was successful."
        log.info(msg_track_ext)
        print_help(msg_track_ext)
    except sqlerr as e:
        log.info("CREATE TABLE 'track_ext': %s", e.args[0])

# main program
def main():
    # CONFIGURATOR INIT / DISCOGS API conf
    conf = Config()
    log.handlers[0].setLevel(conf.log_level) # handler 0 is the console handler
    # ARGPARSER INIT
    args=argparser(sys.argv)
    # INSTALL CLI if not there yet
    conf.install_cli()

    # INFORM USER what this script does
    if len(sys.argv) <= 1:
        print_help(
          "This script sets up the DiscoBASE and/or imports data from Discogs.")
        print("Run setup.py -i to import your whole Discogs collection.")
        print("Run setup.py -i <ID> to import only one release.")
        print("Run setup.py -a <ID> to add a release to your collection.\n")
    log.info(vars(args))

    # DB setup
    db_obj = Database(db_file = conf.discobase)

    if args.update_db_schema:
        update_vers = 0
        curr_vers_row = db_obj._select('PRAGMA user_version', fetchone = True)
        curr_vers = int(curr_vers_row['user_version'])
        print('Current schema version: {}'.format(curr_vers))
        log.info('Current schema version: {}'.format(curr_vers))
        if curr_vers == 0 or curr_vers == 1: # update to v2
            upd_vers = 2
            alter_table = ['ALTER TABLE track ADD m_rec_id TEXT;',
                           'ALTER TABLE track ADD m_rec_id_override TEXT;',
                           'ALTER TABLE track ADD m_match_method TEXT;',
                           'ALTER TABLE track ADD m_match_time TEXT;',
                           'ALTER TABLE track_ext ADD a_key TEXT;',
                           'ALTER TABLE track_ext ADD a_chords_key TEXT;',
                           'ALTER TABLE track_ext ADD a_bpm TEXT;',
                           'ALTER TABLE release ADD m_rel_id TEXT;',
                           'ALTER TABLE release ADD m_rel_id_override TEXT;',
                           'ALTER TABLE release ADD m_match_method TEXT;',
                           'ALTER TABLE release ADD m_match_time TEXT;',
                           'ALTER TABLE release ADD d_catno TEXT;']
        elif curr_vers == 2: # we are up2date
            print('DiscoBASE schema already up to date!')
            log.info('DiscoBASE schema already up to date!')
            raise SystemExit(0)
        else:
            log.error('Unknown DiscoBASE schema version!')
            raise SystemExit(0)

        a = ask_user('Update DiscoBASE schema to version {}? (n) '.format(upd_vers))
        if a.lower() == 'y':
            fkeys_off = 'PRAGMA foreign_keys = OFF;'
            fkeys_on = 'PRAGMA foreign_keys = ON;'
            all_done = False
            db_obj.execute_sql(fkeys_off)
            for cmd in alter_table:
                success = db_obj.execute_sql(cmd)
                if not success:
                    log.error('Schema update command unsuccessful.')
                    break
                all_done = True

            if all_done:
                db_obj.execute_sql('PRAGMA user_version = {}'.format(upd_vers))
                print('DiscoBASE schema update done!')
                log.info('DiscoBASE schema update done!')
            db_obj.execute_sql(fkeys_on)
            #print('DiscoBASE schema update done.')
        raise SystemExit(0)

    # create DB tables if not existing already
    create_db_tables(db_obj)
    # in INFO level show args object again after longish create_table msgs
    log.info(vars(args))

    # PREPARE DISCOGS API and USER INTERACTION classes
    user = User_int(args)
    coll_ctrl = Coll_ctrl_cli(db_obj.db_conn, user, conf.discogs_token,
            conf.discogs_appid)

    # ADD RELEASE TO DISCOGS COLLECTION
    if args.add_release_id:
        coll_ctrl.add_release(args.add_release_id)

    # IMPORT MODE, if we said so
    if args.release_id != False:
        log.debug("args.release_id length: ".format(len(args.release_id)))
        if len(args.release_id) == 0:
            # IMPORT OF WHOLE COLLECTION is the default
            coll_ctrl.import_collection()
        else:
            # IMPORT SPECIFIC RELEASE ID
            coll_ctrl.import_release(args.release_id[0])

# __main__ try/except wrap
if __name__ == "__main__":
    try:
        main()
        #db_obj.close_conn()
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

