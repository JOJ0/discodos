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
from tabulate import tabulate as tab

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser(
                 formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")
    parser.add_argument(
		"-o", "--offline", dest="offline_mode",
        action="store_true",
        help="stays in offline mode, doesn't even try to connect to Discogs")
    # basic subparser element:
    subparsers = parser.add_subparsers()
    # RELEASE subparser
    release_subparser = subparsers.add_parser(
        name='release',
        help='search for a discogs release and add it to a mix')
    release_subparser.add_argument(dest='release_search',
        help='search for this release name or ID')
    release_subparser.add_argument(
        "-m", "--mix", type=str, dest='add_to_mix',
        help='add found release to given mix ID', default=0)
    release_subparser.add_argument(
        "-t", "--track", type=str, dest='track_to_add',
        help='add track number to mix (eg. A1, AA, B2, ...)', default=0)
    release_subparser.add_argument(
        "-p", "--pos", type=str, dest='add_at_pos',
        help='insert track at specific position in mix (eg. 01, 14, ...), defaults to next', default=0)
    # TRACK subparser
    track_subparser = subparsers.add_parser(
        name='track',
        help='search for tracks, add to mix, FIXME not implemented')
    track_subparser.add_argument(
        dest='track_search',
        help='track_search help')
    # MIX subparser
    mix_subparser = subparsers.add_parser(
        name='mix',
        help='do stuff with mixes')
    mix_subparser.add_argument(dest='mix_name',
        help='which mix name or ID should be displayed?',
        default='0')
    mix_subparser.add_argument(
        "-c", "--create-mix", action='store_true',
        help='create a new mix with given name')
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
    except TypeError:
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
            releases = db.search_release_title(dbconn, id_or_title)
            if releases:
                # for now just return first found
                return releases[0]
            else:
                return 'Not found'
        except Exception as Exc:
            log.error("Not found or Database Exception: %s\n", Exc)
            raise Exc

def mix_table(mix_data):
    return tab(mix_data, tablefmt="simple",
        headers=["#", "Release", "Track", "Key", "Key Notes"])

def main():
	# SETUP / INIT
    args = argparser(sys.argv)
    #if hasattr(args, ''):
    #if len(args)==1:
    #    print_help('No args')
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")
    online = False

    # DEBUG stuff
    #print(vars(args))
    log.debug("args_dict: %s", vars(args))

    # DISCOGS API CONNECTION
    if not args.offline_mode == True:
        userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
        try: 
            d = discogs_client.Client("J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                                  user_token=userToken)
            me = d.identity()
            online = True
        except Exception:
            log.error("connecting to Discogs API, let's stay offline!\n")
            online = False

    if hasattr(args, 'release_search'):
        if "all" in args.release_search:
            print_help("Showing all releases, this is gonna take some time")
            print(db.all_releases(conn))
        else:
            db_releases = db.all_releases(conn)
            #for list_element in args.release_search:
            searchterm = args.release_search
            if online:
                print_help('Searching Discogs for Release ID or Title \"'+searchterm+'\"')
                search_results = search_release_online(d, searchterm)
                print_help("Found "+str(search_results.pages )+" page(s) of results!")
                for result_item in search_results:
                    #if result_item.id in me.collection_folders[0].releases:
                    print_help("Checking " + str(result_item.id))
                    for dbr in db_releases:
                        #print_help(dbr[0])
                        if result_item.id == dbr[0]:
                             #print_help("Good, first matching record in your collection is:")
                             #result ='| '+result_item.artists[0].name+' | '+result_item.title
                             #result+=' | '+str(result_item.labels[0])+' |\n| '
                             #result+=result_item.country+' | '+str(result_item.year)+' | '
                             #result+=str(result_item.formats[0]['descriptions'][0])
                             #result+=', '+str(result_item.formats[0]['descriptions'][1])
                             ## string build done, now print
                             #print_help(result)
                             #tracklist = result_item.tracklist
                             #for track in tracklist:
                             #   print(track)
                             #print("Now with tabulate:\n")
                             #pprint.pprint(result_item.artists[0].name)
                             result_list=[]
                             result_list.append([])
                             result_list[0].append(str(result_item.artists[0].name))
                             result_list[0].append(result_item.title)
                             result_list[0].append(str(result_item.labels[0]))
                             result_list[0].append(result_item.country)
                             result_list[0].append(str(result_item.year))
                             result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                                        ", "+str(result_item.formats[0]['descriptions'][1]))

                             #pprint.pprint(result_list)
                             print_help(tab(result_list, tablefmt="simple",
                                       headers=["Artist", "Release", "Label", "Ctry", "Year", "Format"]))
                             tracklist = result_item.tracklist
                             for track in tracklist:
                                print(track)
                             break

                    if result_item.id == dbr[0]:
                        break
            else:
                print_help('Searching offline DB for \"' + searchterm +'\"')
                found_offline = search_release_offline(conn, searchterm)
                #print_help('| '+str(found_offline[0])+' | '+found_offline[1]+' | ')
                #pprint.pprint(found_offline)
                print_help(tab([found_offline], tablefmt="simple",
                               headers=["Release ID", "Release", "Date imported"]))
                if args.add_to_mix and args.track_to_add:
                    mix = args.add_to_mix
                    if db.get_mix_id(conn, mix): 
                        track = args.track_to_add
                        last_track = db.get_last_track_in_mix(conn, mix)
                        log.debug("Currently last track in mix is: %s", last_track[0])
                        if is_number(last_track[0]):
                            current_id = db.add_track_to_mix(conn, mix, found_offline[0],
                                             track, track_pos = last_track[0] + 1)
                        else:
                            current_id = db.add_track_to_mix(conn, mix, found_offline[0],
                                             track, track_pos = 1)
                        #print_help('Added \"'+found_offline[1]+'\" - Track \"'+args.track_to_add+
                        #       '\" to Mix '+args.add_to_mix+' as ID #'+str(current_id))
                        print_help(mix_table(db.get_full_mix(conn, mix)))
                    else:
                        print_help("Mix with ID "+mix+" is not existing yet.")

    elif hasattr(args, 'track_cmd'):
        log.debug("We are in track_cmd branch")
    elif hasattr(args, 'mix_name'):
        mix_name = args.mix_name
        log.debug("A mix_name or ID was given")
        if args.create_mix == True:
            log.debug("Creating new mix")
            created = db.add_new_mix(conn, mix_name)
        else:
            full_mix = db.get_full_mix(conn, args.mix_name)
            if full_mix:
                for row in full_mix:
                   log.debug(str(row))
                log.debug("")
                #print("pprint full_mix")
                #pprint.pprint(full_mix)
                print_help(mix_table(full_mix))
            else:
                print_help("Mix not found or empty.")




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
