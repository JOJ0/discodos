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
import pprint as pp

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
    print(''+str(message)+'\n') 

def search_release_online(discogs, id_or_title):
        try:
            if is_number(id_or_title):
                release = discogs.release(id_or_title)
                return '|'+str(release.id)+'|'+ str(release.title)+'|'
            else:
                releases = discogs.search(id_or_title, type='release')
                return releases
        except errors.HTTPError as HtErr:
            log.error("%s", HtErr)
        except urlerrors.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
        except urlerrors.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
        except Exception as Exc:
            log.error("Exception: %s", Exc)

def search_release_offline(dbconn, id_or_title):
    if is_number(id_or_title):
        try:
            release = db.search_release_id(dbconn, id_or_title)
            if release:
                return '| '+str(release[0][0])+' | '+ str(release[0][1])+' | '
            else:
                return 'Not found'
        except Exception as Exc:
            log.error("Not found or Database Exception: %s\n", Exc)
            raise Exc
    else:
        try:
            release = db.search_release_title(dbconn, id_or_title)
            if release:
                return '| '+str(release[0][0])+' | '+ str(release[0][1])+' | '
            else:
                return 'Not found'
        except Exception as Exc:
            log.error("Not found or Database Exception: %s\n", Exc)
            raise Exc

def main():
	# SETUP / INIT
    args = argparser(sys.argv)
    #if hasattr(args, ''):
    #if len(args)==1:
    #    print_help('No args')

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
        log.error("connecting to Discogs API, let's stay offline!\n")
        online=False

    if hasattr(args, 'release_cmd'):
        if "all" in args.release_cmd:
            print_help("Showing all releases, this is gonna take some time")
            db.all_releases(conn)
        else:
            db_releases = db.all_releases(conn)
            for list_element in args.release_cmd:
                if online:
                    print_help('Searching Discogs for Release ID or Title \"'+list_element+'\"')
                    search_results = search_release_online(d, list_element)
                    print_help("Found "+str(search_results.pages )+" page(s) of results!")
                    for result_item in search_results:
                        #if result_item.id in me.collection_folders[0].releases:
                        print_help("Checking " + str(result_item.id))
                        for dbr in db_releases:
                            #print_help(dbr[0])
                            if result_item.id == dbr[0]:
                                 print_help("Good, first matching record in your collection is:")
                                 result ='| '+result_item.artists[0].name+' | '+result_item.title
                                 result+=' | '+str(result_item.labels[0])+' |\n| '
                                 result+=result_item.country+' | '+str(result_item.year)+' | '
                                 result+=str(result_item.formats[0]['descriptions'][0])
                                 result+=', '+str(result_item.formats[0]['descriptions'][1])
                                 # string build done, now print
                                 print_help(result)
                                 tracklist = result_item.tracklist
                                 for track in tracklist:
                                    print(track)
                                 break
                        if result_item.id == dbr[0]:
                            break
                else:
                    print_help('Searching offline DB for \"' + list_element +'\"')
                    print_help(search_release_offline(conn, list_element))
    elif hasattr(args, 'track_cmd'):
        log.debug("We are in track_cmd branch")



    #for r in me.collection_folders[4].releases:
    
    if conn:
        conn.commit()
        conn.close()
        log.debug("DB closed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.error('Program interrupted!')
    #finally:
        #log.shutdown()
