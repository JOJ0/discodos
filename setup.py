#!/usr/bin/env python

import argparse
from sys import argv
import pprint
# setup.py is kind of a controller - it inits the db and uses some Coll_ctrl methods
from discodos import log
from discodos.utils import print_help, ask_user, Config, read_yaml
from discodos.models import Database, sqlerr, Collection
from discodos.views import User_int
from discodos.ctrls import Coll_ctrl_cli

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
		"--upgrade-db-schema", dest="upgrade_db_schema",
        action='store_true',
        help="force upgrade database schema - only use if you know what you are doing.")
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

class Db_setup(Database):
    def __init__(self, _db_file):
        super().__init__(db_file = _db_file, setup = True)
        self.sql_initial = {
            'release':
            """ CREATE TABLE release (
                  discogs_id INTEGER PRIMARY KEY ON CONFLICT REPLACE,
                  discogs_title TEXT NOT NULL,
                  import_timestamp TEXT,
                  d_artist TEXT,
                  in_d_collection INTEGER
                  ); """,
            'mix':
            """ CREATE TABLE mix (
                  mix_id INTEGER PRIMARY KEY,
                  name TEXT,
                  created TEXT,
                  updated TEXT,
                  played TEXT,
                  venue TEXT
                  ); """,
            'mix_track':
            """ CREATE TABLE mix_track (
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
                  ); """,
            'track':
            """ CREATE TABLE track (
                  d_release_id INTEGER NOT NULL,
                  d_track_no TEXT NOT NULL,
                  d_artist TEXT,
                  d_track_name TEXT,
                  import_timestamp TEXT,
                  PRIMARY KEY (d_release_id, d_track_no)
                  ); """,
                  # We had this constraints once...
                  # FOREIGN KEY (d_release_id)
                  #     REFERENCES release(d_discogs_id)
            # the initial idea of track_ext was to "extend" discogs data with some fields
            'track_ext':
            """ CREATE TABLE track_ext (
                  d_release_id INTEGER NOT NULL,
                  d_track_no TEXT NOT NULL,
                  key TEXT,
                  key_notes TEXT,
                  bpm INTEGER,
                  notes TEXT,
                  PRIMARY KEY (d_release_id, d_track_no)
                  ); """}

        self.sql_upgrades = [    # list element 0 contains a dict
           {'schema_version': 2, # this dict contains 2 entries: schema and tasks
            'tasks': {           # tasks entry contains another dict with a lot of entries
                'Add field track.m_rec_id': 'ALTER TABLE track ADD m_rec_id TEXT;',
                'Add field track.m_match_method': 'ALTER TABLE track ADD m_match_method TEXT;',
                'Add field track.m_match_time': 'ALTER TABLE track ADD m_match_time TEXT;',
                'Add field track.a_key': 'ALTER TABLE track ADD a_key TEXT;',
                'Add field track.a_chords_key': 'ALTER TABLE track ADD a_chords_key TEXT;',
                'Add field track.a_bpm': 'ALTER TABLE track ADD a_bpm TEXT;',
                'Add field track_ext.m_rec_id_override': 'ALTER TABLE track_ext ADD m_rec_id_override TEXT;',
                'Add field release.m_rel_id': 'ALTER TABLE release ADD m_rel_id TEXT;',
                'Add field release.m_rel_id_override': 'ALTER TABLE release ADD m_rel_id_override TEXT;',
                'Add field release.m_match_method': 'ALTER TABLE release ADD m_match_method TEXT;',
                'Add field release.m_match_time': 'ALTER TABLE release ADD m_match_time TEXT;',
                'Add field release.d_catno': 'ALTER TABLE release ADD d_catno TEXT;'
             }
           }                       # list element 0 ends here
           #{'schema_version': 3,  # list element 1 starts here
           # 'tasks': {
           #     'Add field track.test_upgrade': 'ALTER TABLE track ADD test_upgrade TEXT;',
           # }
           #}                      # list element 1 ends here
        ]                          # list closes here

    def create_tables(self): # initial db setup
        for table, sql in self.sql_initial.items():
            try: # release
                self.execute_sql(sql, raise_err = True)
                msg_release="CREATE TABLE '{}' was successful.".format(table)
                log.info(msg_release)
                print(msg_release)
            except sqlerr as e:
                log.info("CREATE TABLE '%s': %s", table, e.args[0])

    def get_latest_schema_version(self):
        vers_list = [schema['schema_version'] for schema in self.sql_upgrades]
        latest = max(vers_list)
        log.debug('Db_setup: Latest DiscoBASE schema version: {}'.format(latest))
        return latest

    def get_current_schema_version(self):
        curr_vers_row = self._select('PRAGMA user_version', fetchone = True)
        return int(curr_vers_row['user_version'])

    def upgrade_schema(self, force_upgrade = False):
        current_schema = self.get_current_schema_version()
        latest_schema = self.get_latest_schema_version()
        # check if upgrade necessary
        if not current_schema < latest_schema and force_upgrade == False:
            log.info('Db_setup: No schema upgrade necessary.')
        else: # also happens if force_upgrade True
            print("Upgrading DiscoBASE schema to latest version.")
            failure = False
            self.execute_sql('PRAGMA foreign_keys = OFF;')
            for upgrade in self.sql_upgrades: # list is sorted -> execute all up to highest
                current_schema = self.get_current_schema_version()
                if (current_schema < upgrade['schema_version'] or force_upgrade == True):
                    for task, sql in upgrade['tasks'].items():
                        try:
                            self.execute_sql(sql, raise_err = True)
                            msg_task="Task '{}' was successful.".format(task)
                            log.info(msg_task)
                            print(msg_task)
                        except sqlerr as e:
                            log.warning("Task failed '%s': %s", task, e.args[0])
                            failure = True

            if failure:
                msg_fail='DiscoBASE schema upgrade failed, open an issue on Github!'
                log.info(msg_fail)
                print(msg_fail)
                self.configure_db() # this sets foreign_keys = ON again
                return False
            else:
                self.execute_sql('PRAGMA user_version = {}'.format(latest_schema))
                msg_done='DiscoBASE schema upgrade done!')
                log.info(msg_fail)
                print(msg_fail)
                self.configure_db() # this sets foreign_keys = ON again
                return True



# main program
def main():
    # CONFIGURATOR INIT / DISCOGS API conf
    conf = Config()
    log.handlers[0].setLevel(conf.log_level) # handler 0 is the console handler
    # ARGPARSER INIT
    args=argparser(argv)
    # INSTALL CLI if not there yet
    conf.install_cli()

    # INFORM USER what this script does
    if len(argv) <= 1:
        print_help(
          "This script sets up the DiscoBASE and/or imports data from Discogs.")
        print("Run setup.py -i to import your whole Discogs collection.")
        print("Run setup.py -i <ID> to import only one release.")
        print("Run setup.py -a <ID> to add a release to your collection.\n")
    log.info(vars(args))

    setup = Db_setup(conf.discobase)
    setup.create_tables()
    setup.upgrade_schema()

    if args.upgrade_db_schema:
        setup.create_tables()
        setup.upgrade_schema(force_upgrade = True)
    # in INFO level show args object again after longish create_table msgs
    log.info(vars(args))

    # PREPARE DISCOGS API and USER INTERACTION classes
    user = User_int(args)
    coll_ctrl = Coll_ctrl_cli(False, user, conf.discogs_token,
            conf.discogs_appid, _db_file = conf.discobase)

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

