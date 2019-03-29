#!/usr/bin/env python3

from discodos import log, db
from discodos.utils import *
from discodos.models import *
from discodos.ctrls import *
from discodos.views import *
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
        help='''current mix (mix name or mix ID that should be displayed, edited, created, ...), 
                omit this argument to show an overview of available mixes.''',
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
        help='create a new mix')
    mix_subp_excl_group.add_argument(
        "-D", "--delete-mix", action='store_true',
        help='deletes a mix and all its contained tracks!')
    mix_subp_excl_group.add_argument(
        "-e", "--edit", type=str,
        dest='edit_mix_track',
        metavar='POSITION',
        help='add/edit rating, notes, key and other info in mix-track')
    mix_subp_excl_group.add_argument(
        "-a", "--add-to-mix", type=str,
        dest='add_release_to_mix',
        metavar='SEARCH_TERM',
        help='''search for release in collection and add it to current mix,
                SEARCH_TERM can also be a Discogs release ID''')
    mix_subp_excl_group.add_argument(
        "-r", "--reorder-tracks", type=int,
        dest='reorder_from_pos',
        metavar='POSITION',
        help='reorder tracks in current mix, starting at POSITION')
    mix_subp_excl_group.add_argument(
        "-d", "--delete-track", type=int,
        dest='delete_track_pos',
        metavar='POSITION',
        help='delete a track in current mix')
    mix_subp_excl_group.add_argument(
        "--copy", action='store_true',
        dest='copy_mix',
        help='creates new mix based on current mix_name (or ID)')
    mix_subp_excl_group.add_argument(
        "-u", "--discogs-update", action='store_true',
        dest='discogs_update',
        help='updates tracks in current mix with additional info from Discogs')
    # mutually exclusive group ends here
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
        default='0')
    track_subparser.add_argument(
        "-u", "--discogs-update",
        dest='track_pull',
        action="store_true",
        help='all tracks used in mixes are updated with info pulled from Discogs')
    # only the main parser goes into a variable
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -v.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

# search release online try/except wrapper
def search_release_online(discogs, id_or_title):
        try:
            if is_number(id_or_title):
                release = discogs.release(id_or_title)
                #return '|'+str(release.id)+'|'+ str(release.title)+'|'
                return [release]
            else:
                releases = discogs.search(id_or_title, type='release')
                print(releases[0])
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
            return True
        else:
            return False
    else:
        print_help("Mix ID "+str(mix_id)+" is not existing yet.")
        return False

# DB wrapper: add track to specfic pos in mix
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
        print_help("verbose add successful")
        for t in tracks_to_shift:
            new_pos = t['track_pos']+1
            log.info("Shifting track %i from pos %i to %i", t[0], t[1], new_pos)
            db.update_pos_in_mix(conn, t['mix_track_id'], new_pos)
        return True

# DB wrapper: reorder tracks starting at given position
def reorder_tracks_in_mix(conn, _reorder_pos, _mix_id):
    reorder_pos = int(_reorder_pos)
    tracks_to_shift = db.get_tracks_from_position(
                          conn, _mix_id, reorder_pos)
    for t in tracks_to_shift:
        log.info("Shifting mix_track_id %i from pos %i to %i", t['mix_track_id'],
                 t['track_pos'], reorder_pos)
        db.update_pos_in_mix(conn, t['mix_track_id'], reorder_pos)
        reorder_pos = reorder_pos + 1

# Discogs: gets Track name from discogs tracklist object via track_number, eg. A1
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
            #return result_list[0]
            return result_list
            #break

# Discogs: update mix_tracks with details from discogs
def pull_track_info_from_discogs(_conn, _mix_id = False):
    if ONLINE:
        if _mix_id:
            print_help("Let's update current mixes tracks with info from Discogs...")
            mixed_tracks = db.get_tracks_of_one_mix(_conn, _mix_id)
        else:
            print_help("Let's update ALL tracks used in mixes with info from Discogs...")
            mixed_tracks = db.get_all_tracks_in_mixes(_conn)
        for mix_track in mixed_tracks:
            rate_limit_slow_downer(d, remaining=5, sleep=2)
            name = tracklist_parse(d.release(mix_track[2]).tracklist, mix_track[3])
            #artist = tracklist_parse_artist(d.release(mix_track[2]).tracklist, mix_track[3])
            #print_help(d.release(mix_track[2]).tracklist)
            if name:
                print("Adding track info: "+ str(mix_track[2])+" "+
                        mix_track[3] + " " + name)
                        #mix_track[3] + " " + artist + " - " + name)
                try:
                    db.create_track(_conn, mix_track[2], mix_track[3], name)
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
        print_help("Not online, can't pull from Discogs...")

def search_offline_and_add_to_mix(_searchterm, _conn, _mix_id, _track = False,
                                  _pos = False):
    print_help('Searching offline DB for \"' + _searchterm +'\"')
    try:
        found_offline = search_release_offline(_conn, _searchterm)
        # for now only work with first result
        if found_offline:
            print_help(offline_release_table(found_offline[0]))
            track_to_add = _track
            #####  User wants to add Track at given POSITION #####
            if user.WANTS_TO_ADD_AT_POSITION or user.WANTS_TO_ADD_AT_POS_IN_MIX_MODE:
                if not _track:
                    track_to_add = ask_user("Which Track? ")
                cur_id_add_pos = add_track_at_pos(_conn, _mix_id, track_to_add,
                                                  _pos, found_offline[0])
                if cur_id_add_pos == None or cur_id_add_pos == False:
                    log.error("Error in add_track_at_pos()")
                else:
                    if user.WANTS_VERBOSE_MIX_TRACKLIST:
                        print_help("\n"+mix_table_fine(db.get_full_mix(conn,
                                                      _mix_id, detail="fine")))
                    else:
                        print_help("\n"+mix_table_coarse(db.get_full_mix(conn,
                                                        _mix_id, detail="coarse")))

            #####  User wants to add a Track to END OF Mix #####
            elif user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
                if not _track:
                    track_to_add = ask_user("Which Track? ")
                cur_id_add = add_track_to_mix(_conn, _mix_id, track_to_add,
                                               found_offline[0])
                if cur_id_add == None or cur_id_add == False:
                    log.error("Error in add_track_to_mix()")
                else:
                    if user.WANTS_VERBOSE_MIX_TRACKLIST:
                        print_help("\n"+mix_table_fine(db.get_full_mix(conn,
                                           _mix_id, detail="fine")))
                    else:
                        print_help("\n"+mix_table_coarse(db.get_full_mix(conn,
                                           _mix_id, detail="coarse")))
        else:
            print_help('No results')
    except TypeError as TErr:
        print_help('No results')
        raise TErr

def search_online_and_add_to_mix(_searchterm, _conn, _mix_id, _track = False, _pos = False):
    print_help('Searching Discogs for Release ID or Title: {}'.format(_searchterm))
    try:
        db_releases = db.all_releases(_conn)
        search_results = search_release_online(d, _searchterm)
        # SEARCH RESULTS OUTPUT HAPPENS HERE
        compiled_results_list = pretty_print_found_release(
            search_results, _searchterm, db_releases)
        #####  User wants to add Track at given position #####
        if user.WANTS_TO_ADD_AT_POSITION or user.WANTS_TO_ADD_AT_POS_IN_MIX_MODE:
            if not _track:
                track_to_add = ask_user("Which Track? ")
            else:
                track_to_add = _track
            cur_id_add_pos = add_track_at_pos(_conn, _mix_id, track_to_add,
                                          _pos, compiled_results_list)
            if cur_id_add_pos == None or cur_id_add_pos == False:
                log.error("Error in add_track_to_mix()")
            else:
                if user.WANTS_VERBOSE_MIX_TRACKLIST:
                    print_help("\n"+mix_table_fine(db.get_full_mix(conn,
                                       _mix_id, detail="fine")))
                else:
                    print_help("\n"+mix_table_coarse(db.get_full_mix(conn,
                                       _mix_id, detail="coarse")))
        # FIXME no elif her (like above), should have been handled
        # in check_args() already
        #####  User wants to add a Track to a Mix #####
        if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
            if not _track:
                track_to_add = ask_user("Which Track? ")
            else:
                track_to_add = _track
            cur_id_add = add_track_to_mix(_conn, _mix_id, track_to_add,
                             compiled_results_list)
            if cur_id_add == None or cur_id_add == False:
                log.error("Error in add_track_to_mix()")
            else:
                if user.WANTS_VERBOSE_MIX_TRACKLIST:
                    print_help("\n"+mix_table_fine(db.get_full_mix(conn,
                                       _mix_id, detail="fine")))
                else:
                    print_help("\n"+mix_table_coarse(db.get_full_mix(conn,
                                       _mix_id, detail="coarse")))
    except TypeError as TErr:
        print_help('No results')
        raise TErr

# user interaction class - holds info about what user wants to do
# currently this only analyzes argparser args and puts it to nicely human readable properties
class User_int(object):

    def __init__(self, _args):
        self.args = _args
        self.WANTS_ONLINE = True
        self.WANTS_TO_LIST_ALL_RELEASES = False
        self.WANTS_TO_SEARCH_FOR_RELEASE = False
        self.WANTS_TO_ADD_TO_MIX = False
        self.WANTS_TO_SHOW_MIX_OVERVIEW = False
        self.WANTS_TO_SHOW_MIX_TRACKLIST = False
        self.WANTS_TO_CREATE_MIX = False
        self.WANTS_TO_EDIT_MIX_TRACK = False
        self.WANTS_TO_PULL_TRACK_INFO = False
        self.WANTS_VERBOSE_MIX_TRACKLIST = False
        self.WANTS_TO_REORDER_MIX_TRACKLIST = False
        self.WANTS_TO_ADD_AT_POSITION = False
        self.WANTS_TO_DELETE_MIX_TRACK = False
        self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = False
        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = False
        self.WANTS_TO_COPY_MIX = False
        self.WANTS_TO_TRACK_SEARCH = False
        self.WANTS_TO_DELETE_MIX = False

        # RELEASE MODE:
        if hasattr(self.args, 'release_search'):
            if "all" in self.args.release_search:
                self.WANTS_TO_LIST_ALL_RELEASES = True
                self.WANTS_ONLINE = False
            else:
                self.WANTS_TO_SEARCH_FOR_RELEASE = True
                if self.args.add_to_mix and self.args.track_to_add and self.args.add_at_pos:
                    self.WANTS_TO_ADD_AT_POSITION = True
                    #self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                elif self.args.add_to_mix and self.args.track_to_add:
                    self.WANTS_TO_ADD_TO_MIX = True

        # MIX MODE
        if hasattr(self.args, 'mix_name'):
            if self.args.mix_name == "all":
                self.WANTS_TO_SHOW_MIX_OVERVIEW = True
                self.WANTS_ONLINE = False
                if self.args.create_mix == True:
                    log.error("Please provide a mix name to be created!")
                    log.error("(Mix name \"all\" is not valid.)")
                    raise SystemExit(1)
                elif self.args.delete_mix == True:
                    log.error("Please provide a mix name or ID to be deleted!")
                    raise SystemExit(1)
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO = True
                    self.WANTS_ONLINE = True
            else:
                self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                self.WANTS_ONLINE = False
                #if hasattr(self.args, 'create_mix')
                if self.args.create_mix:
                    self.WANTS_TO_CREATE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.edit_mix_track:
                    self.WANTS_TO_EDIT_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.verbose_tracklist:
                    self.WANTS_VERBOSE_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.reorder_from_pos:
                    self.WANTS_TO_REORDER_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.delete_track_pos:
                    self.WANTS_TO_DELETE_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.add_release_to_mix:
                    self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_mode_add_at_pos:
                        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = True
                if self.args.copy_mix:
                    self.WANTS_TO_COPY_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO = True
                    self.WANTS_ONLINE = True
                if self.args.delete_mix:
                    self.WANTS_TO_DELETE_MIX = True
                    self.WANTS_ONLINE = False

        # TRACK MODE
        if hasattr(self.args, 'track_search'):
            self.WANTS_TO_TRACK_SEARCH = True
            if args.track_pull:
                self.WANTS_TO_PULL_TRACK_INFO = True
            else:
                log.error("Online track search not implemented yet.")
                raise SystemExit(1)

        if self.args.offline_mode == True:
            self.WANTS_ONLINE = False

# discogs connect try,except wrapper, sets globals d and me
def discogs_connect(_userToken, _appIdentifier):
    try:
        global d
        d = discogs_client.Client(
                _appIdentifier,
                user_token = _userToken)
        global me
        me = d.identity()
        _ONLINE = True
    except Exception as Exc:
        log.error("connecting to Discogs API, let's stay offline!\n")
        _ONLINE = False
        #raise Exc
    return _ONLINE



# MAIN
def main():
    # DISCOGS API CONFIG
    userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
    appIdentifier = "J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0"
	# SETUP / INIT
    global args, ONLINE, user
    args = argparser(sys.argv)
    # DEBUG stuff
    #print(vars(args))
    log.info("args_dict: %s", vars(args))
    #log.info("dir(args): %s", dir(args))
    # check cli args and set attributes
    user = User_int(args)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    # db connection global (classes get it passed)
    global conn
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")

    # DISCOGS API CONNECTION
    if user.WANTS_ONLINE:
        ONLINE = discogs_connect(userToken, appIdentifier)
    else:
        ONLINE = False

    log.info("ONLINE: %s", ONLINE)

    #### RELEASE MODE
    if user.WANTS_TO_LIST_ALL_RELEASES:
        print_help("Showing all releases, this is gonna take some time")
        print_help(all_releases_table(db.all_releases(conn)))
    elif user.WANTS_TO_SEARCH_FOR_RELEASE:
        searchterm = args.release_search
        if ONLINE:
            search_online_and_add_to_mix(searchterm, conn, args.add_to_mix,
                                          args.track_to_add, args.add_at_pos)
        else:
            search_offline_and_add_to_mix(searchterm, conn, args.add_to_mix,
                                          args.track_to_add, args.add_at_pos)


    ##### MIX MODE ########################################################
    ### NO MIX ID GIVEN ###################################################
    if user.WANTS_TO_SHOW_MIX_OVERVIEW:
        if user.WANTS_TO_PULL_TRACK_INFO:
            pull_track_info_from_discogs(conn)
        else:
            #print_help(all_mixes_table(db.get_all_mixes(conn)))
            mix_ctrl = Mix_ctrl_cli(conn, args.mix_name, user)
            mix_ctrl.view_mixes_list()

    ### SPECIFIC MIX ID GIVEN #############################################
    ### SHOW MIX DETAILS ##################################################
    elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
        log.info("A mix_name or ID was given. Instantiating Mix_ctrl_cli class.\n")
        mix_ctrl = Mix_ctrl_cli(conn, args.mix_name, user)
        ### CREATE A NEW MIX ##############################################
        if user.WANTS_TO_CREATE_MIX:
            mix_ctrl.create()
            # mix is created (or not), nothing else to do
            raise SystemExit(0)
        ### DELETE A MIX ##############################################
        if user.WANTS_TO_DELETE_MIX:
            mix_ctrl.delete()
            # mix is deleted (or not), nothing else to do
            raise SystemExit(0)
        ### DO STUFF WITH EXISTING MIXES ###################################
        ### EDIT A MIX-TRACK ###############################################
        if user.WANTS_TO_EDIT_MIX_TRACK:
            mix_ctrl.edit_track(args.edit_mix_track)
        ### REORDER TRACKLIST
        elif user.WANTS_TO_REORDER_MIX_TRACKLIST:
            print_help("Tracklist reordering starting at position {}".format(
                       args.reorder_from_pos))
            mix_ctrl.reorder_tracks(args.reorder_from_pos)
        ### DELETE A TRACK FROM MIX
        elif user.WANTS_TO_DELETE_MIX_TRACK:
            really_del = ask_user(text="Delete Track {} from mix {}? ".format(
                                         args.delete_track_pos, mix_id))
            if really_del.lower() == "y":
                successful = db.delete_track_from_mix(conn, mix_id,
                                             args.delete_track_pos)
                # reorder existing and print tracklist
                if successful:
                    reorder_tracks_in_mix(conn, args.delete_track_pos - 1, mix_id)
                    pretty_print_mix_tracklist(mix_id, mix_info)
                else:
                    print_help("Delete failed, maybe nonexistent track position?")
        ### SEARCH FOR A RELEASE AND ADD IT TO MIX (same as in release mode)
        elif user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
            if ONLINE:
                search_online_and_add_to_mix(args.add_release_to_mix, conn, mix_id,
                                              False, args.mix_mode_add_at_pos)
            else:
                search_offline_and_add_to_mix(args.add_release_to_mix, conn, mix_id,
                                              False, args.mix_mode_add_at_pos)
        #### COPY A MIX
        elif user.WANTS_TO_COPY_MIX:
            print_help("Copying mix {} - {}.".format(mix_id, mix_name))
            copy_tr = db.get_mix_tracks_to_copy(conn, mix_id)
            new_mix_name = ask_user("How should the copy be named? ")
            new_mix_id = create_mix(conn, new_mix_name)
            for tr in copy_tr:
                db.add_track_to_mix(conn, new_mix_id, tr[0], tr[1], tr[2], tr[3], tr[4])
            conn.commit()
            pretty_print_mix_tracklist(new_mix_id, db.get_mix_info(conn, new_mix_id))
                                       
        #### UPDATE TRACKS WITH DISCOGS INFO
        elif user.WANTS_TO_PULL_TRACK_INFO:
            pull_track_info_from_discogs(conn, mix_id)

        #### JUST SHOW MIX-TRACKLIST:
        elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
            #pretty_print_mix_tracklist(mix_ctrl.id, mix_ctrl.info)
            mix_ctrl.view()


    ### TRACK MODE
    if user.WANTS_TO_TRACK_SEARCH:
        if user.WANTS_TO_PULL_TRACK_INFO:
            pull_track_info_from_discogs(conn)

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
