#!/usr/bin/env python3

from discodos import db, log
import discogs_client
import csv
import time
import datetime
import argparse
import sys
import pprint

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")
    # basic subparser element:
    subparsers = parser.add_subparsers()
    # RELEASE subparser
    release_subparser = subparsers.add_parser(
        name='release',
        help='show different data of one or more discogs releases')
    release_subparser.add_argument(dest='release_cmd',
        help='release_cmd help',
        nargs='*',
        default="show")
    # TRACK subparser
    track_subparser = subparsers.add_parser(
        name='track',
        help='search for tracks, add to mix')
    track_subparser.add_argument(
        dest='track_cmd',
        help='track_cmd help')
    # only the main parser goes into a variable
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -v.
    #log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def main():
	# setup / init
    global log
    log=log.logger_init()
    args = argparser(sys.argv)
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")
    print(vars(args))
    #log.debug("pprint: ", vars(args))

    # discogs api connection
    userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
    try: 
        d = discogs_client.Client("J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                              user_token=userToken)
        me = d.identity()
    except Exception:
        log.error("Error connecting to Discogs API, let's stay offline!")
        offline_mode=True

    if hasattr(args, 'release_cmd'):
        if "all" in args.release_cmd:
            log.info("Showing all releases, this is gonna take some time")
            db.all_releases(conn)
        else:
            log.info("Pull release info from discogs and show info")
            for list_element in args.release_cmd:
                log.info("Pulling release from discogs: %s", list_element)
                release_id = d.release(list_element)
                log.info("Release title: %s", release_id)
    elif hasattr(args, 'track_cmd'):
        log.debug("we are in track_cmd branch")



    
    #for r in me.collection_folders[4].releases:
    
    if conn:
        conn.commit()
        conn.close()
        print("DB closed.")

if __name__ == "__main__":
    main()
