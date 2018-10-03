#!/usr/bin/env python3

from discodos import log, db
import discogs_client
import csv
import time
import datetime
import argparse
import sys
import pprint
import discogs_client.exceptions as errors
import requests.exceptions as reqerrors
import urllib3.exceptions as urlerrors

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
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def print_help(message):
    print('\n'+str(message)+'\n') 

def search_release_online(id_or_title):
    if is_number(id_or_title):
        try:
            release = d.release(id_or_title)
            return '|'+str(release.id)+'|'+ str(release.title)+'|'
        except errors.HTTPError as HtErr:
            log.error("%s", HtErr)
        except urlerrors.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
        except urlerrors.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
        except Exception as Exc:
            log.error("Exception: %s", Exc)

def main():
	# SETUP / INIT
    args = argparser(sys.argv)
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")

    # DEBUG stuff
    #print(vars(args))
    log.debug("args_dict: %s", vars(args))

    # DISCOGS API CONNECTION
    userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
    try: 
        d = discogs_client.Client("J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                              user_token=userToken)
        me = d.identity()
        online=True
    except Exception:
        log.error("Error connecting to Discogs API, let's stay offline!\n")
        online=False

    if hasattr(args, 'release_cmd'):
        if "all" in args.release_cmd:
            print_help("Showing all releases, this is gonna take some time")
            db.all_releases(conn)
        else:
            for list_element in args.release_cmd:
                if online:
                    print_help('Searching Discogs for Release ID or Title \"'+list_element+'\"')
                    print_help(search_release_online(list_element))
                else:
                    print_help('Searching offline DB for ' + list_element)
    elif hasattr(args, 'track_cmd'):
        log.debug("we are in track_cmd branch")



    #for r in me.collection_folders[4].releases:
    
    if conn:
        conn.commit()
        conn.close()
        log.debug("DB closed.")

if __name__ == "__main__":
    main()
