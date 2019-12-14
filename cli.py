#!/usr/bin/env python3

#from discodos import log, db
from discodos.utils import *
#from discodos.models import *
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
#from tabulate import tabulate as tab
#from sqlite3 import Error as sqlerr
from pathlib import Path
import os

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
        help='add found release to given mix ID', default=0)
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
        help='add/edit rating, notes, key and other info of a track in a mix')
    mix_subp_excl_group.add_argument(
        "-b", "--bulk-edit", type=str,
        dest='bulk_edit',
        metavar='FIELD_LIST',
        help='''bulk-edit specific columns of whole mixes. Syntax of col list eg: <col1>,<col2>,...
        possible cols: key,bpm,track_no,track_pos,key_notes,trans_rating,trans_notes,release_id,notes''')
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
        help='search for Track name, show Track-combination report',
        aliases=('tr', 't'))
    track_subparser.add_argument(
        dest='track_search',
        help='The name of the track you want to show a report for.',
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



# MAIN
def main():
    # DISCOGS API config
    discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
    conf = read_yaml(discodos_root / "config.yaml")
    discobase = discodos_root / "discobase.db"
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
    log.info("discobase path is: {}".format(discobase))
    # also here refactoring is not through - conn should not be needed in future
    # Objects derived from models.py should handle it themselves
    # workaround for now:
    db_obj = Database(db_file = discobase)
    conn = db_obj.db_conn
    # INIT COLLECTION CONTROLLER (DISCOGS API CONNECTION)
    coll_ctrl = Coll_ctrl_cli(conn, user, conf['discogs_token'], conf['discogs_appid'])

    #### RELEASE MODE
    if user.WANTS_TO_LIST_ALL_RELEASES:
        coll_ctrl.view_all_releases()
    elif user.WANTS_TO_SEARCH_FOR_RELEASE:
        searchterm = args.release_search
        if coll_ctrl.ONLINE:
            #search_online_and_add_to_mix(searchterm, conn, args.add_to_mix,
            #                              args.track_to_add, args.add_at_pos)
            discogs_rel_found = coll_ctrl.search_release(searchterm)
            # initialize a mix_ctrl object from release mode
            mix_ctrl = Mix_ctrl_cli(conn, args.add_to_mix, user)
            mix_ctrl.add_discogs_track(discogs_rel_found, args.track_to_add, args.add_at_pos)
            mix_ctrl.view()
        else:
            database_rel_found = coll_ctrl.search_release(searchterm)
            mix_ctrl = Mix_ctrl_cli(conn, args.add_to_mix, user)
            mix_ctrl.add_offline_track(database_rel_found, args.track_to_add, args.add_at_pos)
            mix_ctrl.view()


    ##### MIX MODE ########################################################
    ### NO MIX ID GIVEN ###################################################
    if user.WANTS_TO_SHOW_MIX_OVERVIEW:
        # we instantiate a mix controller object
        mix_ctrl = Mix_ctrl_cli(False, args.mix_name, user) # conn = False, init from file
        if user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(coll_ctrl)
        else:
            mix_ctrl.view_mixes_list()

    ### MIX ID GIVEN #############################################
    ### SHOW MIX DETAILS ##################################################
    elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
        log.info("A mix_name or ID was given. Instantiating Mix_ctrl_cli class.\n")
        mix_ctrl = Mix_ctrl_cli(conn, args.mix_name, user)
        #coll_ctrl = Coll_ctrl_cli(conn, user)
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
            mix_ctrl.delete_track(args.delete_track_pos)
        ### SEARCH FOR A RELEASE AND ADD IT TO MIX (same as in release mode)
        elif user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
            if coll_ctrl.ONLINE:
                # this returns a online or offline releases type object depending on models state:
                discogs_rel_found = coll_ctrl.search_release(args.add_release_to_mix)
                mix_ctrl.add_discogs_track(discogs_rel_found, False,
                                            args.mix_mode_add_at_pos)
            else:
                database_rel_found = coll_ctrl.search_release(args.add_release_to_mix)
                mix_ctrl.add_offline_track(database_rel_found, False,
                                            args.mix_mode_add_at_pos)

        #### COPY A MIX
        elif user.WANTS_TO_COPY_MIX:
            mix_ctrl.copy_mix()
                                       
        #### UPDATE TRACKS WITH DISCOGS INFO
        elif user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(coll_ctrl, start_pos = args.mix_mode_add_at_pos)

        #### BULK EDIT MIX COLUMNS
        elif user.WANTS_TO_BULK_EDIT:
            mix_ctrl.bulk_edit_tracks(args.bulk_edit, args.mix_mode_add_at_pos)

        #### JUST SHOW MIX-TRACKLIST:
        elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
            #pretty_print_mix_tracklist(mix_ctrl.id, mix_ctrl.info)
            mix_ctrl.view()


    ### TRACK MODE
    #if user.WANTS_TO_TRACK_SEARCH:
    if user.WANTS_TO_PULL_TRACK_INFO:
        mix_ctrl = Mix_ctrl_cli(conn, False, user)
        mix_ctrl.pull_track_info_from_discogs(coll_ctrl)
    elif user.WANTS_TRACK_REPORT:
        coll_ctrl.track_report(args.track_search)

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
