#!/usr/bin/env python3

from discodos import log, db
from discodos.utils import *
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
        "-v", "--verbose", action='store_true',
        dest='verbose_tracklist',
        help='mix tracklist shows more details')
    # only one of --create-mix OR --edit OR --add possible
    mix_subp_excl_group = mix_subparser.add_mutually_exclusive_group()
    mix_subp_excl_group.add_argument(
        "-c", "--create-mix", action='store_true',
        help='create a new mix with given name')
    mix_subp_excl_group.add_argument(
        "-e", "--edit", type=str,
        dest='edit_mix_track',
        help='add/edit rating, notes, key and other info in mix-tracks')
    mix_subp_excl_group.add_argument(
        "-a", "--add-to-mix", type=str,
        dest='add_release_to_mix',
        help='search for release and add it to current mix')
    mix_subp_excl_group.add_argument(
        "-r", "--reorder-tracks", type=int,
        dest='reorder_from_pos',
        help='reorder tracks in current mix')
    mix_subp_excl_group.add_argument(
        "-d", "--delete-track", type=int,
        dest='delete_track_pos',
        help='delete a track in current mix')
    mix_subparser.add_argument(
        "-p", "--pos", type=int,
        dest='mix_mode_add_at_pos',
        help='add found release track at specific position in mix')
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

# util: args checker, sets global constants
def check_args(_args):
    # defaults for all constants
    global ONLINE
    ONLINE = True
    global WANTS_TO_LIST_ALL_RELEASES
    WANTS_TO_LIST_ALL_RELEASES = False
    global WANTS_TO_SEARCH_FOR_RELEASE
    WANTS_TO_SEARCH_FOR_RELEASE = False
    global WANTS_TO_ADD_TO_MIX
    WANTS_TO_ADD_TO_MIX = False
    global WANTS_TO_SHOW_MIX_OVERVIEW
    WANTS_TO_SHOW_MIX_OVERVIEW = False
    global WANTS_TO_SHOW_MIX_TRACKLIST
    WANTS_TO_SHOW_MIX_TRACKLIST = False
    global WANTS_TO_CREATE_MIX
    WANTS_TO_CREATE_MIX = False
    global WANTS_TO_EDIT_MIX_TRACK
    WANTS_TO_EDIT_MIX_TRACK = False
    global WANTS_TO_PULL_TRACK_INFO
    WANTS_TO_PULL_TRACK_INFO = False
    global WANTS_VERBOSE_MIX_TRACKLIST
    WANTS_VERBOSE_MIX_TRACKLIST = False
    global WANTS_TO_REORDER_MIX_TRACKLIST
    WANTS_TO_REORDER_MIX_TRACKLIST = False
    global WANTS_TO_ADD_AT_POSITION
    WANTS_TO_ADD_AT_POSITION = False
    global WANTS_TO_DELETE_MIX_TRACK
    WANTS_TO_DELETE_MIX_TRACK = False
    global WANTS_TO_ADD_RELEASE_IN_MIX_MODE
    WANTS_TO_ADD_RELEASE_IN_MIX_MODE = False
    global WANTS_TO_ADD_AT_POS_IN_MIX_MODE
    WANTS_TO_ADD_AT_POS_IN_MIX_MODE = False

    # RELEASE MODE:
    if hasattr(_args, 'release_search'):
        if "all" in _args.release_search:
            WANTS_TO_LIST_ALL_RELEASES = True
            ONLINE = False
        else:
            WANTS_TO_SEARCH_FOR_RELEASE = True
            if _args.add_to_mix and _args.track_to_add and _args.add_at_pos:
                WANTS_TO_ADD_AT_POSITION = True
                #WANTS_TO_SHOW_MIX_TRACKLIST = True
            elif _args.add_to_mix and _args.track_to_add:
                WANTS_TO_ADD_TO_MIX = True

    # MIX MODE
    if hasattr(_args, 'mix_name'):
        if _args.mix_name == "all":
            WANTS_TO_SHOW_MIX_OVERVIEW = True
            ONLINE = False
            if _args.create_mix == True:
                log.error("Please provide a mix name to be created!")
                log.error("(Mix name \"all\" is not valid.)")
                raise SystemExit(1)
        else:
            WANTS_TO_SHOW_MIX_TRACKLIST = True
            ONLINE = False
            #if hasattr(_args, 'create_mix')
            if _args.create_mix:
                WANTS_TO_CREATE_MIX = True
            if _args.edit_mix_track:
                WANTS_TO_EDIT_MIX_TRACK = True
            if _args.verbose_tracklist:
                WANTS_VERBOSE_MIX_TRACKLIST = True
            if _args.reorder_from_pos:
                WANTS_TO_REORDER_MIX_TRACKLIST = True
            if _args.delete_track_pos:
                WANTS_TO_DELETE_MIX_TRACK = True
            if _args.add_release_to_mix:
                WANTS_TO_ADD_RELEASE_IN_MIX_MODE = True
                if _args.mix_mode_add_at_pos:
                    WANTS_TO_ADD_AT_POS_IN_MIX_MODE = True

    # TRACK MODE
    if hasattr(args, 'track_search'):
        if args.pull:
            WANTS_TO_PULL_TRACK_INFO = True
        else:
            log.error("Online track search not implemented yet.")
            raise SystemExit(1)

    if _args.offline_mode == True:
        ONLINE = False

# UI: what info should be edited in mix-track
def ask_details_to_edit(_track_det):
    # dbfield, question
    questions_table = [
        ["d_track_no", "Fix track number on record? eg B2 ? ({}) "],
        ["d_release_id", "Change Release ID? eg 123456 ? ({}) "],
        ["track_pos", "Move track to new position in mix? eg 3 ({}) "],
        ["trans_rating", "Rate transition? eg ++ ({}) "],
        ["trans_notes", "Other notes on this transition? ({}) "],
        ["key", "The tracks musical key? eg Am ({}) "],
        ["key_notes", "More music notes (eg Bassline tones)? ({}) "],
        ["bpm", "The tracks BPM? ({}) "],
        ["notes", "General notes on track? ({}) "]
    ]
    #print(_track_det['d_track_no'])
    # collect answers from user input
    answers = {}
    answers['track_pos'] = "x"
    for db_field, question in questions_table:
        if db_field == 'track_pos':
            while not is_number(answers['track_pos']):
                answers[db_field] = ask_user(
                                         question.format(_track_det[db_field]))
                if answers[db_field] == "":
                    answers[db_field] = _track_det[db_field]
                    break
        else:
            answers[db_field] = ask_user(
                                     question.format(_track_det[db_field]))
            if answers[db_field] == "":
                log.info("Answer was empty, keeping previous value: %s",
                         _track_det[db_field])
                answers[db_field] = _track_det[db_field]
    #pprint.pprint(answers)
    return answers

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
                release_not_found = None
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
                return None
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
        headers=["#", "Release", "Tr\nPos", "Trns\nRat", "Key", "BPM"])

# tabulate tracklist in DETAIL
def mix_table_fine(mix_data):
    return tab(mix_data, tablefmt="pipe",
        headers=["#", "Release", "Track\nName", "Track\nPos", "Trans.\nRating",
        "Trans.\nR. Notes", "Key", "Key\nNotes", "BPM", "Track\nNotes"])

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

# DB wrapper: add a track to a mix
def add_track_to_mix(conn, _mix_id, _track, _rel_list, _pos=None):
    print_help("_pos given to add_track_to_mix(): "+str(_pos))
    def _user_is_sure(_pos):
        if ONLINE:
            quest=(
            'Add "{:s}" on "{:s}" - "{:s}" to mix #{:d}, at position {:d}? (y) '
                .format(track, _rel_list[0][1], _rel_list[0][2], int(mix_id), _pos))
        else:
            quest=(
            'Add "{:s}" on "{:s}" to mix #{:d}, at position {:d}? (y) '
                .format(track, _rel_list[0][1], int(mix_id), _pos))
        _answ = ask_user(quest)
        if _answ.lower() == "y" or _answ.lower() == "":
            return True
    log.info("Adding first item of release_list to mix: %s", _rel_list)
    track = _track
    if is_number(_mix_id):
        mix_id = _mix_id
    else:
        mix_id = db.get_mix_id(conn, _mix_id)
    if db.mix_id_existing(conn, mix_id):
        last_track = db.get_last_track_in_mix(conn, mix_id)
        log.debug("Currently last track in mix is: %s", last_track[0])
        current_id = False
        if _pos:
            if _user_is_sure(int(_pos)):
                current_id = db.add_track_to_mix(conn, mix_id, _rel_list[0][0],
                             track, track_pos = _pos)
        elif is_number(last_track[0]):
            if _user_is_sure(last_track[0]+1):
                current_id = db.add_track_to_mix(conn, mix_id, _rel_list[0][0],
                             track, track_pos = last_track[0] + 1)
        else:
            if _user_is_sure(1):
                current_id = db.add_track_to_mix(conn, mix_id, _rel_list[0][0],
                             track, track_pos = 1)
        # FIXME untested if this is actually a proper sanity check
        if current_id:
            if WANTS_VERBOSE_MIX_TRACKLIST and WANTS_TO_ADD_AT_POSITION == False:
                print_help("\n"+mix_table_fine(db.get_full_mix(conn, mix_id)))
            elif WANTS_TO_ADD_AT_POSITION == False:
                print_help("\n"+mix_table_coarse(db.get_full_mix(conn, mix_id)))
            return True
        else:
            return False
    else:
        print_help("Mix ID "+str(mix_id)+" is not existing yet.")
        return False

# DB wrapper: add track to spec pos in mix
def add_track_at_pos(conn, _mix_id, _track, _pos, _results_list_item):
    mix_id = _mix_id
    pos = _pos
    tracks_to_shift = db.get_tracks_from_position(
                          conn, mix_id, pos)
    # first add new track (user can cancel at this point)
    #mix_info = db.get_mix_info(conn, mix_id)
    add_successful = add_track_to_mix(conn, _mix_id, _track, _results_list_item,
                                      _pos=pos)
    # then reorder existing
    if add_successful:
        for t in tracks_to_shift:
            new_pos = t['track_pos']+1
            log.info("Shifting track %i from pos %i to %i", t[0], t[1], new_pos)
            db.update_pos_in_mix(conn, t['mix_track_id'], new_pos)
        if WANTS_VERBOSE_MIX_TRACKLIST:
            print_help("\n"+mix_table_fine(db.get_full_mix(conn, mix_id)))
        else:
            print_help("\n"+mix_table_coarse(db.get_full_mix(conn, mix_id)))

# DB wrapper: reorder tracks starting at given position
def reorder_tracks_in_mix(conn, _args, _mix_id):
    reorder_pos = int(_args.reorder_from_pos)
    tracks_to_shift = db.get_tracks_from_position(
                          conn, _mix_id, reorder_pos)
    for t in tracks_to_shift:
        log.info("Shifting track %i from pos %i to %i", t[0], t[1], reorder_pos)
        db.update_pos_in_mix(conn, t['mix_track_id'], reorder_pos)
        reorder_pos = reorder_pos + 1

# Discogs: gets track name from discogs tracklist object via track_number, eg. A1
def tracklist_parse(d_tracklist, track_number):
    for tr in d_tracklist:
        if tr.position == track_number:
            return tr.title

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
                result_list[0].append(result_item.id)
                result_list[0].append(str(result_item.artists[0].name))
                result_list[0].append(result_item.title)
                result_list[0].append(str(result_item.labels[0].name))
                result_list[0].append(result_item.country)
                result_list[0].append(str(result_item.year))
                #result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                #           ", "+str(result_item.formats[0]['descriptions'][1]))
                result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                           ", "+str(result_item.formats[0]['descriptions'][0]))

                print_help(tab(result_list, tablefmt="simple",
                          headers=["ID", "Artist", "Release", "Label", "C", "Year", "Format"]))
                tracklist = result_item.tracklist
                for track in tracklist:
                   print(track.position + "\t" + track.title)
                print()
                break

        if result_item.id == dbr[0]:
            return result_list[0]
            #break

# show pretty mix-tracklist
def pretty_print_mix_tracklist(_mix_id, _mix_info):
    print_help(mix_info_header(_mix_info))
    if WANTS_VERBOSE_MIX_TRACKLIST:
        full_mix = db.get_full_mix(conn, _mix_id, detail="fine")
    else:
        full_mix = db.get_full_mix(conn, _mix_id, detail="coarse")

    if full_mix:
        # debug only
        for row in full_mix:
           log.debug(str(row))
        log.debug("")
        # now really
        if WANTS_VERBOSE_MIX_TRACKLIST:
            print_help(mix_table_fine(full_mix))
        else:
            print_help(mix_table_coarse(full_mix))
    else:
        print_help("No tracks in mix yet.")

def search_offline_and_add_to_mix(_searchterm, _conn, _mix_id, _track = False,
                                  _pos = False):
    print_help('Searching offline DB for \"' + _searchterm +'\"')
    try:
        found_offline = search_release_offline(_conn, _searchterm)
        # for now only work with first result
        if found_offline:
            print_help(offline_release_table(found_offline[0]))
            track_to_add = _track
            #####  User wants to add Track at given position #####
            if WANTS_TO_ADD_AT_POSITION or WANTS_TO_ADD_AT_POS_IN_MIX_MODE:
                print_help("We are in ADD_AT_POS")
                if not _track:
                    track_to_add = ask_user("Which Track? ")
                add_track_at_pos(_conn, _mix_id, track_to_add, _pos, found_offline[0])
            #####  User wants to add a Track to a Mix #####
            elif WANTS_TO_ADD_TO_MIX or WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
                if not _track:
                    track_to_add = ask_user("Which Track? ")
                add_track_to_mix(_conn, _mix_id, track_to_add, found_offline[0])
        else:
            print_help('No results')
    except TypeError as TErr:
        print_help('No results')
        raise TErr

# MAIN
def main():
	# SETUP / INIT
    global args, ONLINE
    args = argparser(sys.argv)
    # DEBUG stuff
    #print(vars(args))
    log.info("args_dict: %s", vars(args))
    #log.info("dir(args): %s", dir(args))
    check_args(args)
    log.info("ONLINE: %s", ONLINE)
    global conn
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")

    # DISCOGS API CONNECTION
    if ONLINE:
        userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
        try: 
            d = discogs_client.Client(
                    "J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                    user_token=userToken)
            me = d.identity()
            ONLINE = True
        except Exception:
            log.error("connecting to Discogs API, let's stay offline!\n")
            ONLINE = False

    if WANTS_TO_LIST_ALL_RELEASES:
        print_help("Showing all releases, this is gonna take some time")
        print_help(all_releases_table(db.all_releases(conn)))
    elif WANTS_TO_SEARCH_FOR_RELEASE:
        db_releases = db.all_releases(conn)
        searchterm = args.release_search
        if ONLINE:
            print_help('Searching Discogs for Release ID or Title \"'+searchterm+'\"')
            try:
                search_results = search_release_online(d, searchterm)
                # SEARCH RESULTS OUTPUT HAPPENS HERE
                compiled_results_list = pretty_print_found_release(
                    search_results, searchterm, db_releases)
                #####  User wants to add a Track to a Mix #####
                if WANTS_TO_ADD_TO_MIX:
                    add_track_to_mix(conn, args.add_to_mix, args.track_to_add,
                                     compiled_results_list)
                #####  User wants to add Track at given position #####
                if WANTS_TO_ADD_AT_POSITION:
                    add_track_at_pos(conn, args.add_to_mix, args.track_to_add,
                                     args.add_at_pos, compiled_results_list)
            except TypeError as TErr:
                print_help('No results')
                raise TErr
        else:
            search_offline_and_add_to_mix(searchterm, conn, args.add_to_mix,
                                          args.track_to_add, args.add_at_pos)


    if WANTS_TO_SHOW_MIX_OVERVIEW:
        print_help(all_mixes_table(db.get_all_mixes(conn)))
        # show mix details
    elif WANTS_TO_SHOW_MIX_TRACKLIST:
        log.info("A mix_name or ID was given\n")
        ### CREATE A NEW MIX ###############################################
        if WANTS_TO_CREATE_MIX:
            if is_number(args.mix_name):
                log.error("Mix name can't be a number!")
            else:
                played = ask_user(
                           text="When did you (last) play it? eg 2018-01-01 ")
                venue = ask_user(text="And where? ")
                created_id = db.add_new_mix(conn, args.mix_name, played, venue)
                conn.commit()
                print_help("New mix created with ID " + str(created_id))
                print_help(all_mixes_table(db.get_all_mixes(conn)))
            # mix is created (or not), nothing else to do
            raise SystemExit(0)
        ### DO STUFF WITH EXISTING MIXES ###################################
        # if it's a mix ID, load basic mix-info from DB
        if is_number(args.mix_name):
            mix_id = args.mix_name
            try:
                mix_info = db.get_mix_info(conn, mix_id)
                mix_name = mix_info[1]
            except:
                print_help("This Mix ID is not existing yet!")
                #raise Exception
                raise SystemExit(1)
        else:
            mix_name = args.mix_name
            # if it's a mix-name, get the id
            try:
                mix_id_tuple = db.get_mix_id(conn, mix_name)
                log.info('%s', mix_id_tuple)
                mix_id = mix_id_tuple[0]
            except:
                print_help("No mix-name matching.")
                raise SystemExit(1)
            # load basic mix-info from DB, FIXME error handling necessary??
            mix_info = db.get_mix_info(conn, mix_id)
        ### EDIT A MIX-TRACK ###############################################
        if WANTS_TO_EDIT_MIX_TRACK:
            edit_track = args.edit_mix_track
            print_help("Editing track "+edit_track+" in \""+
                        mix_name+"\":")
            track_details = db.get_one_mix_track(conn, mix_id, edit_track)
            if track_details:
                log.info("current d_release_id: %s", track_details['d_release_id'])
                edit_answers = ask_details_to_edit(track_details)
                for a in edit_answers.items():
                    log.info("answers: %s", str(a))
                try:
                    db.update_track_in_mix(conn,
                        track_details['mix_track_id'],
                        edit_answers['d_release_id'],
                        edit_answers['d_track_no'],
                        edit_answers['track_pos'],
                        edit_answers['trans_rating'],
                        edit_answers['trans_notes'])
                    db.update_or_insert_track_ext(conn,
                        track_details['d_release_id'],
                        edit_answers['d_release_id'],
                        edit_answers['d_track_no'],
                        edit_answers['key'],
                        edit_answers['key_notes'],
                        edit_answers['bpm'],
                        edit_answers['notes'],
                        )
                except Exception as edit_err:
                    log.error("Something went wrong on mix_track edit!")
                    raise edit_err
                    raise SystemExit(1)
                pretty_print_mix_tracklist(mix_id, mix_info)
            else:
                print_help("No track "+edit_track+" in \""+
                            mix_name+"\".")
        ### REORDER TRACKLIST
        elif WANTS_TO_REORDER_MIX_TRACKLIST:
            print_help("Tracklist reordering starting at position {}".format(
                       args.reorder_from_pos))
            reorder_tracks_in_mix(conn, args, mix_id)
            if WANTS_VERBOSE_MIX_TRACKLIST:
                print_help("\n"+mix_table_fine(
                                    db.get_full_mix(conn, mix_id)))
            else:
                print_help("\n"+mix_table_coarse(
                                   db.get_full_mix(conn, mix_id)))
        ### DELETE A TRACK FROM MIX
        elif WANTS_TO_DELETE_MIX_TRACK:
            really_del = ask_user(text="Delete Track {} from mix {}? ".format(
                                         args.delete_track_pos, mix_id))
            if really_del.lower() == "y":
                successful = db.delete_track_from_mix(conn, mix_id,
                                             args.delete_track_pos)
                if successful:
                    if WANTS_VERBOSE_MIX_TRACKLIST:
                        print_help("\n"+mix_table_fine(
                                            db.get_full_mix(conn, mix_id)))
                    else:
                        print_help("\n"+mix_table_coarse(
                                       db.get_full_mix(conn, mix_id)))
                else:
                    print_help("Delete failed, maybe nonexistent track position?")
        ### SEARCH FOR A RELEASE AND ADD IT TO MIX (same as in release mode)
        elif WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
            search_offline_and_add_to_mix(args.add_release_to_mix, conn, mix_id,
                                          False, args.mix_mode_add_at_pos)

        #### JUST SHOW MIX-TRACKLIST:
        elif WANTS_TO_SHOW_MIX_TRACKLIST:
            pretty_print_mix_tracklist(mix_id, mix_info)

    ### TRACK MODE
    if WANTS_TO_PULL_TRACK_INFO:
        if ONLINE:
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
                        log.info("Not added, probably already there.\n")
                        log.info("DB returned: %s", err)
                else:
                    print("Adding track info: "+ str(mix_track[2])+" "+
                            mix_track[3])
                    log.error("No trackname found for Tr.Pos %s",
                            mix_track[3])
                    log.error("Probably you misspelled? (eg A vs. A1)\n")
        else:
            print_help("Not online can't pull from Discogs...")

    # most importantly commit stuff to DB
    #time.sleep(10)
    log.debug("DB commiting...")
    conn.commit()
    log.debug("DB closing...")
    conn.close()
    log.debug("DB closed.")

# __MAIN try/except wrap
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # most importantly commit stuff to DB
        #conn.commit()
        #conn.close()
        log.error('Program interrupted!')
    #finally:
        #log.shutdown()
