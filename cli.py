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
from sqlite3 import Error as sqlerr

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
    ### RELEASE subparser #######################################################
    release_subparser = subparsers.add_parser(
        name='release',
        help='search for a discogs release and add it to a mix',
        aliases=('rel', 'r'))
    release_subparser.add_argument(
        dest='release_search',
        help='search for this release name or ID')
    release_subparser.add_argument(
        "-m", "--mix", type=str, dest='add_to_mix',
        help='add found release to given mix ID', default="all")
    release_subparser.add_argument(
        "-t", "--track", type=str, dest='track_to_add',
        help='add track number to mix (eg. A1, AA, B2, ...)', default=0)
    release_subparser.add_argument(
        "-p", "--pos", type=str, dest='add_at_pos',
        help='insert track at specific position in mix (eg. 01, 14, ...), defaults to next',
        default=0)
    ### MIX subparser #############################################################
    mix_subparser = subparsers.add_parser(
        name='mix',
        help='do stuff with mixes',
        aliases=('m', ))
    mix_subparser.add_argument(
        dest='mix_name',
        help='which mix name or ID should be displayed?',
        nargs='?',
        default='all')
    mix_subparser.add_argument(
        "-c", "--create-mix", action='store_true',
        help='create a new mix with given name')
    mix_subparser.add_argument(
        "-v", "--verbose", action='store_true',
        help='mix tracklist shows more details')
    ### TRACK subparser ##########################################################
    track_subparser = subparsers.add_parser(
        name='track',
        help='search for tracks, add to mix, FIXME not implemented',
        aliases=('tr', 't'))
    track_subparser.add_argument(
        dest='track_search',
        help='track_search help',
        nargs='?',
        default='')
    track_subparser.add_argument(
        "-p", "--pull",
        action="store_true",
        default=False,
        help='all tracks used in mixes are updated with info pulled from Discogs')
    # only the main parser goes into a variable
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -v.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

# util: checks for numbers
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

# util: print a UI message
def print_help(message):
    print(''+str(message)+'\n') 

# util: ask user for some string
def ask_user(text=""):
    return input(text)

# search release online try/except wrapper
def search_release_online(discogs, id_or_title):
        try:
            if is_number(id_or_title):
                release = discogs.release(id_or_title)
                #return '|'+str(release.id)+'|'+ str(release.title)+'|'
                return [release]
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

# search release offline try/except wrapper
def search_release_offline(dbconn, id_or_title):
    if is_number(id_or_title):
        try:
            release = db.search_release_id(dbconn, id_or_title)
            if release:
                #return '| '+str(release[0][0])+' | '+ str(release[0][1])+' | '
                return [release]
            else:
                release_not_found = ['Not found']
                #return 'Not found'
                return release_not_found
        except Exception as Exc:
            log.error("Not found or Database Exception: %s\n", Exc)
            raise Exc
    else:
        try:
            releases = db.search_release_title(dbconn, id_or_title)
            if releases:
                # return all releases (so it's a list for tabulate),
                # but only first one is used later on... 
                return [releases]
            else:
                return ['Not found']
        except Exception as Exc:
            log.error("Not found or Database Exception: %s\n", Exc)
            raise Exc

# tabulate ALL releases 
def all_releases_table(release_data):
    return tab(release_data, tablefmt="plain",
        headers=["ID", "Release name", "Last import"])

# tabulate tracklist COARSLY
def mix_table_coarse(mix_data):
    return tab(mix_data, tablefmt="pipe",
        headers=["#", "Release", "Tr.Pos", "Rating", "Key", "BPM"])

# tabulate tracklist in DETAIL
def mix_table_fine(mix_data):
    return tab(mix_data, tablefmt="pipe",
        headers=["#", "Release", "Tr.Name", "Tr.Pos", "Rating", "Rating notes", 
                 "Key", "Key notes", "BPM"])

# tabulate ALl mixes
def all_mixes_table(mixes_data):
    return tab(mixes_data, tablefmt="simple",
        headers=["Mix #", "Name", "Created", "Updated", "Played", "Venue"])

# tabulate header of mix-tracklist
def mix_info_header(mix_info):
    return tab([mix_info], tablefmt="plain",
        headers=["Mix", "Name", "Created", "Updated", "Played", "Venue"])

# tabulate OFFLINE release search results
def offline_release_table(release_list):
    return tab(release_list, tablefmt="simple",
        headers=["Release ID", "Release", "Date imported"])

# tabulate ONLINE release search results
def online_release_table(_result_list): 
    return (tab(_result_list, tablefmt="simple",
        headers=["Artist", "Release", "Label", "C", "Year", "Format"]))

# args checker: want to add track to mix?
def wants_to_add_to_mix(cli_args):
    if cli_args.add_to_mix and cli_args.track_to_add:
        return True

# DB wrapper: add a track to a mix
def add_track_to_mix(conn, _args, rel_list):
    if _args.add_to_mix and _args.track_to_add:
        track = _args.track_to_add
        if is_number(_args.add_to_mix):
            mix_id = _args.add_to_mix
        else:
            mix_id = db.get_mix_id(conn, _args.add_to_mix) 
        if db.mix_id_existing(conn, mix_id):
            last_track = db.get_last_track_in_mix(conn, mix_id)
            log.debug("Currently last track in mix is: %s", last_track[0])
            if is_number(last_track[0]):
                current_id = db.add_track_to_mix(conn, mix_id, rel_list[0],
                                 track, track_pos = last_track[0] + 1)
            else:
                current_id = db.add_track_to_mix(conn, mix_id, rel_list[0],
                                 track, track_pos = 1)
            print_help(mix_table_coarse(db.get_full_mix(conn, mix_id)))
        else:
            print_help("Mix ID "+str(mix_id)+" is not existing yet.")

# Discogs: gets track name from discogs tracklist object via track_number, eg. A1
def tracklist_parse(d_tracklist, track_number):
    for tr in d_tracklist:
        if tr.position == track_number:
            return tr.title

# Discogs: stay in 60/min rate limit
def rate_limit_slow_downer(d_obj, remaining=10, sleep=2):
    if int(d_obj._fetcher.rate_limit_remaining) < remaining:
        log.info("Discogs request rate limit is about to exceed,\
                  let's wait a bit: %s\n",
                     d_obj._fetcher.rate_limit_remaining)
        time.sleep(sleep)

# Discogs: formatted output of release search results
def pretty_print_found_release(discogs_results, _searchterm, _db_releases):
    # only show pages count if it's a Release Title Search
    if not is_number(_searchterm):
        print_help("Found "+str(discogs_results.pages )+" page(s) of results!")
    else:
        print_help("ID: "+discogs_results[0].id+", Title: "+discogs_results[0].title+"")
    for result_item in discogs_results:
        print_help("Checking " + str(result_item.id))
        for dbr in _db_releases:
            if result_item.id == dbr[0]:
                 print_help("Good, first matching record in your collection is:")
                 result_list=[]
                 result_list.append([])
                 result_list[0].append(str(result_item.artists[0].name))
                 result_list[0].append(result_item.title)
                 result_list[0].append(str(result_item.labels[0].name))
                 result_list[0].append(result_item.country)
                 result_list[0].append(str(result_item.year))
                 result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                            ", "+str(result_item.formats[0]['descriptions'][1]))

                 print_help(tab(result_list, tablefmt="simple",
                           headers=["Artist", "Release", "Label", "C", "Year", "Format"]))
                 tracklist = result_item.tracklist
                 for track in tracklist:
                    print(track.position + "\t" + track.title + "\n")
                 break

        if result_item.id == dbr[0]:
            break


# MAIN
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
    log.info("args_dict: %s", vars(args))
    #log.info("dir(args): %s", dir(args))

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
            print_help(all_releases_table(db.all_releases(conn)))
        else:
            db_releases = db.all_releases(conn)
            searchterm = args.release_search
            if online:
                print_help('Searching Discogs for Release ID or Title \"'+searchterm+'\"')
                search_results = search_release_online(d, searchterm)
                # SEARCH RESULTS OUTPUT HAPPENS HERE
                pretty_print_found_release(search_results, searchterm, db_releases)
                #####  User wants to add a Track to a Mix #####
                # FIXME untested, works in offline mode
                if wants_to_add_to_mix(args):
                    add_track_to_mix(conn, args, result_list)
            else:
                print_help('Searching offline DB for \"' + searchterm +'\"')
                found_offline = search_release_offline(conn, searchterm)
                # for now only work with first result
                print_help(offline_release_table(found_offline))
                #####  User wants to add a Track to a Mix #####
                if wants_to_add_to_mix(args):
                    add_track_to_mix(conn, args, found_offline[0])

    elif hasattr(args, 'track_search'):
        if args.pull:
            if online:
                print_help("Let's update tracks used in mixes with info from Discogs...")
                all_mixed_tracks = db.get_tracks_in_mixes(conn)
                for mix_track in all_mixed_tracks:

                    rate_limit_slow_downer(d, remaining=5, sleep=2)
                    name = tracklist_parse(d.release(mix_track[2]).tracklist, mix_track[3])
                    if name:
                        print("Adding track info: "+ str(mix_track[2])+" "+
                                mix_track[3] + " " + name)
                        try:
                            db.create_track(conn, mix_track[2], mix_track[3], name)
                        except sqlerr as err:
                            log.warning("Not added, probably already there.\n")
                            log.info("DB returned: %s", err)
                    else:
                        print("Adding track info: "+ str(mix_track[2])+" "+
                                mix_track[3])
                        log.error("No trackname found for Tr.Pos %s",
                                mix_track[3])
                        log.error("Probably you misspelled? (eg A vs. A1)\n")
            else:
                print_help("Not online can't pull from Discogs...")

        else:
            log.error("We are in track mode but what should I do?")

    elif hasattr(args, 'mix_name'):
        # show mix overview
        if args.mix_name == "all":
            print_help(all_mixes_table(db.get_all_mixes(conn)))
        # show mix details
        else:
            log.info("A mix_name or ID was given")
            if is_number(args.mix_name):
                mix_id = args.mix_name
                mix_name = None
            else:
                mix_name = args.mix_name
                try:
                    mix_id_tuple = db.get_mix_id(conn, mix_name)
                    log.info('%s', mix_id_tuple)
                    mix_id = mix_id_tuple[0]
                except:
                    print_help("No mix-name matching.")
                    raise SystemExit(1)

            if args.create_mix == True:
                played = ask_user(text="When did you (last) play it? ")
                venue = ask_user(text="And where? ")
                created_id = db.add_new_mix(conn, mix_id, played, venue)
                print_help("New mix created with ID " + str(created_id))
                print_help(all_mixes_table(db.get_all_mixes(conn)))
            else:
                mix_info = db.get_mix_info(conn, mix_id)
                print_help(mix_info_header(mix_info))
                if args.verbose:
                    full_mix = db.get_full_mix(conn, mix_id, detail="fine")
                else:
                    full_mix = db.get_full_mix(conn, mix_id, detail="coarse")

                if full_mix:
                    # debug only
                    for row in full_mix:
                       log.debug(str(row))
                    log.debug("")
                    # now really
                    if args.verbose:
                        print_help(mix_table_fine(full_mix))
                    else:
                        print_help(mix_table_coarse(full_mix))
                else:
                    print_help("No tracks in mix yet.")


        conn.close()
        log.debug("DB closed.")

# __MAIN try/except wrap
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.error('Program interrupted!')
    #finally:
        #log.shutdown()
