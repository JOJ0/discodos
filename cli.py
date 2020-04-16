#!/usr/bin/env python

from discodos.utils import ask_user, print_help, Config
from discodos.views import User_int
from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli
from discodos import log
import argparse
import sys
import pprint

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser()
                 #formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help='''increases output verbosity / shows what DiscoDOS is doing under
        the hood (-v is INFO level, -vv is DEBUG level).''')
    parser.add_argument(
		"-o", "--offline", dest="offline_mode",
        action="store_true",
        help="""DiscoDOS checks for connectivity to online services
        (Discogs, MusicBrainz, AcousticBrainz) itself. This option
        forces offline mode. A lot of options work in on- and
        offline mode. Some behave differently, depending on connection state.""")
    # basic subparser element:
    subparsers = parser.add_subparsers()
    ### SEARCH subparser #######################################################
    search_subparser = subparsers.add_parser(
        name='search',
        help='''searches for releases and tracks in the Discogs collection.
        Several actions can be executed on the found items, eg. adding
        to a mix, updating track info from Discogs or fetching additional
        information from MusicBrainz/AcousticBrainz.
        View this subcommand's help: "disco search -h".''')
    search_subparser.add_argument(
        dest='release_search', metavar='search_terms',
        help='''The collection is searched for these terms. When offline, it
        searches through all releases' artists/titles only (eg tracknames
        not considered). When online, the Discogs API search
        engine is used and also tracknames, artists, labels and
        catalog numbers are looked through.
        If your search term consists of multiple words, put them inside double
        quotes (eg. "foo bar term"). If you instead put a number as your
        search term, it is assumed you want to view exactly the Discogs
        release with the given ID.''')
    search_subp_excl_group = search_subparser.add_mutually_exclusive_group()
    search_subp_excl_group.add_argument(
        "-m", "--mix", type=str, dest='add_to_mix', metavar='MIX_NAME',
        help='''adds a track of the found release to the given mix ID
                (asks which track to add in case -t is missing).''',
        default=0)
    search_subp_excl_group.add_argument(
        "-u", "--discogs-update", action='store_true',
        dest='search_discogs_update', default=0,
        help='''updates found release/track with Discogs track/artist details
                (asks which track to update in case -t is missing).''')
    search_subp_excl_group.add_argument(
        "-z", "--brainz-update", action="count",
        dest='search_brainz_update', default=0,
        help='''updates found release/track with additional info from MusicBrainz
        and AcousticBrainz. (asks which track to update in case -t is missing)
        -z quick match,
        -zz detailed match (takes longer, but more results).''')
    search_subparser.add_argument(
        "-t", "--track", type=str, dest='track_to_add', metavar='TRACK_NUMBER',
        help='''in combination with -m this option adds the given track number
        (eg. A1, AA, B2, ...) to the mix selected using -m;
        in combination with -z or -u the given track is
        the one being updated with *Brainz or Discogs details.''')
    search_subparser.add_argument(
        "-p", "--pos", type=str, dest='add_at_pos', metavar='POS_IN_MIX',
        help='''in combination with -m this option states that we'd like to
        insert the track at the given position (eg. 1, 14, ...), rather than at the
        end of the mix; in combination with -z or -u this option is ignored.''',
        default=0)
    ### MIX subparser #############################################################
    mix_subparser = subparsers.add_parser(
        name='mix',
        help='manages your mixes. View this subcommand\'s help: "disco mix -h."')
    mix_subparser.add_argument(
        dest='mix_name',
        help='''mix name or mix ID being displayed, edited, created, copied,
        deleted, etc. If mix_name is left out, a list of available mixes is
        shown and all other arguments are ignored.''',
        nargs='?',
        default='all')
    mix_subparser.add_argument(
        "-v", "--verbose",
        action="count", default=0,
        dest='verbose_tracklist',
        help='''increases mix tracklist view detail. -v adds tracknames,
        artists, transition rating/notes and general track notes.
        -vv shows when and how MusicBrainz matching was done and also direct
        weblinks to Discogs releases, MusicBrainz releases/recordings and
        AccousticBrainz recordings.''')
    # only one of --create-mix OR --edit OR --add possible
    mix_subp_excl_group = mix_subparser.add_mutually_exclusive_group()
    mix_subp_excl_group.add_argument(
        "-c", "--create-mix", action='store_true',
        help='creates new mix (named as given in mix_name argument).')
    mix_subp_excl_group.add_argument(
        "-D", "--delete-mix", action='store_true',
        help='deletes the mix (given in mix_name) and all its contained tracks!')
    mix_subp_excl_group.add_argument(
        "-e", "--edit", type=str,
        dest='edit_mix_track',
        metavar='POSITION',
        help='''edits/adds details of a track in a mix. (editable fields:
        key, BPM, track number, position in mix, key notes, transition rating,
        transition notes, general track notes, custom MusicBrainz recording ID).''')
    mix_subp_excl_group.add_argument(
        "-E", "--edit-mix", action='store_true',
        help='edits/adds general info about a mix (name, played date, venue).')
    mix_subp_excl_group.add_argument(
        "-b", "--bulk-edit", type=str,
        dest='bulk_edit',
        metavar='FIELDS',
        help='''bulk-edits specific fields of each track in mix.
        Syntax of FIELDS argument: <field1>,<field2>,...
        available fields: key,bpm,track_no,track_pos,key_notes,trans_rating,
        trans_notes,notes.''')
    mix_subp_excl_group.add_argument(
        "-a", "--add-to-mix", type=str,
        dest='add_release_to_mix', metavar='SEARCH_TERMS',
        help='''searches for release/track in collection and adds it to the mix,
        This option is actually a shortcut to "disco search -m mix_name
        search_term" and behaves identically. If SEARCH_TERMS is a number, it
        is assumed being a Discogs release ID. A quick database check is done
        and if non-existent yet, the release is 1) added to the Discogs collection
        and 2) imported to DiscoBASE. This is a convenience function eg when trying
        to quickly add a release to the mix that's not in the DiscoBASE yet (possibly
        an only recently gained record?).''')
    mix_subp_excl_group.add_argument(
        "-r", "--reorder-tracks", type=int,
        dest='reorder_from_pos',
        metavar='POSITION',
        help='''reorders tracks in current mix, starting at POSITION.
        Note that this is a troubleshooting function and usually shouldn't
        be necessary to use.''')
    mix_subp_excl_group.add_argument(
        "-d", "--delete-track", type=int,
        dest='delete_track_pos',
        metavar='POSITION',
        help='removes the track at the given position from the mix.')
    mix_subp_excl_group.add_argument(
        "--copy", action='store_true',
        dest='copy_mix',
        help='copies the mix given in mix_name argument. Asks for new name!')
    mix_subp_excl_group.add_argument(
        "-u", "--discogs-update", action='store_true',
        dest='discogs_update',
        help='updates tracks in current mix with additional info from Discogs.')
    mix_subp_excl_group.add_argument(
        "-z", "--brainz-update", action="count", default=0,
        dest='brainz_update',
        help='''updates tracks in current mix with additional info from MusicBrainz and AcousticBrainz.
        Leave out mix ID to update every track contained in any mix.
        -z quick match, -zz detailed match (takes longer, but more results).''')
    # mutually exclusive group ends here
    mix_subparser.add_argument(
        "-p", "--pos", type=int,
        dest='mix_mode_add_at_pos', metavar='POSITION',
        help='''in combination with -a this option adds the found release/track
        at the given position in the mix (rather than at the end). In
        combination with -u or -z the update process is started at the given
        position in the mix.''')
    ### SUGGEST subparser ##########################################################
    suggest_subparser = subparsers.add_parser(
        name='suggest',
        help='''suggests tracks based on what you\'ve played before or views
        tracks based on BPM or musical key.
        View this subcommand's help: "disco suggest -h".''')
    suggest_subparser.add_argument(
        dest='suggest_search', metavar='search_terms',
        help='''track or release name you want to show a
        "track-combination report" for.''',
        nargs='?',
        default='0')
    suggest_subparser.add_argument(
        "-b", "--bpm", type=int,
        dest='suggest_bpm', metavar="BPM",
        help='''suggests tracks based on BPM value, within a
        pitch-range of +/-6 percent.''')
    suggest_subparser.add_argument(
        "-k", "--key", type=str,
        dest='suggest_key', metavar="KEY",
        help='suggests tracks based on musical key.')
    ### IMPORT subparser ##########################################################
    import_subparser = subparsers.add_parser(
        name='import',
        help='''imports your whole Discogs collection or just single releases.
        View this subcommand's help: "disco import -h".''')
    import_subparser.add_argument(
        dest='import_id', metavar='RELEASE_ID', type=int,
        help='''the Discogs release ID you want to import to DiscoBASE.
        If left empty, the whole collection will be imported. If the additional
        option -a is used, the release will be added to your Discogs collection
        _and_ imported to DiscoBASE. Note that a regular import of a given
        release ID is quite time consuming: We have to check wether or
        not this release ID is already in the Discogs collection (we don't
        want duplicates), thus we have to run through all of your releases
        via the Discogs API. Unfortunately Discogs does not allow us to search
        for release IDs in ones collection, we only can "iterate" through them.
        Therefore the recommended way of adding newly gained releases is by
        using the -a option.''',
        nargs='?',
        default='0')
    import_subp_excl_group = import_subparser.add_mutually_exclusive_group()
    import_subp_excl_group.add_argument(
        '--add-to-collection', '-a', dest='import_add_coll', action='store_true',
        help='''This is the recommended (and fastest) way of adding newly gained
        releases to your collection. The given release ID is added to your
        Discogs collection (same as when you click an "Add to collection"
        in the Discogs Webinterface.
        Additionally the release is added to the DiscoBASE.
        Note that for performance's sake, we don't do a time-consuming check if the
        release is already in your Discogs collection by asking the Discogs API,
        but only do a quick check if the ID is in the local DiscoBASE already.
        ''')
    import_subp_excl_group.add_argument(
        '--tracks', '-u', dest='import_tracks', action='store_true',
        help='''extends the Discogs import (releases and also tracks will
        be downloaded) - takes siginficantly longer than the regular import.
        Note: This is the same as "disco search all -u".''')
    import_subp_excl_group.add_argument(
        '--brainz', '-z', dest='import_brainz', action="count", default=0,
        help='''imports additional information from MusicBrainz/AcousticBrainz.
        This action takes a long time. -z quick match, -zz detailed match (takes
        even longer, but more results).
        Notes: This is the same as "disco search all -z". Prior to using this
        option, an extended Discogs import is recommended (disco import --tracks).
        Otherwise only tracks that were already downloaded to the DiscoBASE (eg
        used in mixes and updated using "disco mix -u")
        will be updated.
        ''')
    # only the main parser goes into a variable
    arguments = parser.parse_args(argv[1:])
    log.info("Console log_level currently set to {} via config.yaml or default".format(
        log.handlers[0].level))
    # Sets log level to WARN going more verbose for each new -v.
    cli_level = max(3 - arguments.verbose_count, 0) * 10
    if cli_level < log.handlers[0].level: # 10 = DEBUG, 20 = INFO, 30 = WARNING
        log.handlers[0].setLevel(cli_level)
        log.warning("Console log_level override via cli. Now set to {}.".format(
            log.handlers[0].level))
    return arguments 



# MAIN
def main():
    # CONFIGURATOR INIT / DISCOGS API conf
    conf = Config()
    log.handlers[0].setLevel(conf.log_level) # handler 0 is the console handler
    # SETUP / INIT
    #global args, ONLINE, user
    global args, user
    args = argparser(sys.argv)
    # DEBUG stuff
    #print(vars(args))
    log.info("args_dict: %s", vars(args))
    #log.info("dir(args): %s", dir(args))
    # check cli args and set attributes
    user = User_int(args)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    # INIT COLLECTION CONTROLLER (DISCOGS API CONNECTION)
    coll_ctrl = Coll_ctrl_cli(False, user, conf.discogs_token, conf.discogs_appid,
            conf.discobase, conf.musicbrainz_user, conf.musicbrainz_password)

    #### RELEASE MODE
    if user.WANTS_TO_LIST_ALL_RELEASES:
        if user.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS:
            coll_ctrl.import_collection(tracks = True)
        elif user.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ:
            pass
        else:
            coll_ctrl.view_all_releases()
    elif user.WANTS_TO_SEARCH_FOR_RELEASE:
        searchterm = args.release_search
        msg_use = "Nothing more to do. Use -m <mix> to add to a "
        msg_use+= "mix, -u to update with Discogs information "
        msg_use+= "or -zz to update with *Brainz information. "
        msg_use+= "You can combine these options with -t too."
        if coll_ctrl.ONLINE:
            discogs_rel_found = coll_ctrl.search_release(searchterm)
            if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_AT_POSITION:
                mix_ctrl = Mix_ctrl_cli(False, args.add_to_mix, user, conf.discobase)
                mix_ctrl.add_discogs_track(discogs_rel_found, args.track_to_add,
                        args.add_at_pos,
                        track_no_suggest = coll_ctrl.first_track_on_release)
            elif user.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS:
                # online search gave us exactely one release in a list
                #print(discogs_rel_found)
                coll_ctrl.update_single_track_from_discogs(
                      discogs_rel_found['id'],
                      discogs_rel_found['title'],
                      args.track_to_add)
            elif user.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ:
                coll_ctrl.update_single_track_from_brainz(
                      discogs_rel_found['id'],
                      discogs_rel_found['title'],
                      args.track_to_add,
                      detail=user.BRAINZ_SEARCH_DETAIL)
            else:
                #if discogs_rel_found: # prevents msg when nothing's found anyway
                print_help(msg_use)
        else: # when OFFLINE
            database_rel_found = coll_ctrl.search_release(searchterm)
            if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_AT_POSITION:
                mix_ctrl = Mix_ctrl_cli(False, args.add_to_mix, user, conf.discobase)
                mix_ctrl.add_offline_track(database_rel_found, args.track_to_add,
                        args.add_at_pos)
            else:
                if database_rel_found: # prevents msg when nothing's found anyway
                    print_help(msg_use)


    ##### MIX MODE ########################################################
    ### NO MIX ID GIVEN ###################################################
    if user.WANTS_TO_SHOW_MIX_OVERVIEW:
        # we instantiate a mix controller object
        mix_ctrl = Mix_ctrl_cli(False, args.mix_name, user, conf.discobase)
        if user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(coll_ctrl)
        elif user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE:
            mix_ctrl.update_track_info_from_brainz(coll_ctrl,
              detail = user.BRAINZ_SEARCH_DETAIL)
        else:
            mix_ctrl.view_mixes_list()

    ### MIX ID GIVEN #############################################
    ### SHOW MIX DETAILS ##################################################
    elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
        log.info("A mix_name or ID was given. Instantiating Mix_ctrl_cli class.\n")
        mix_ctrl = Mix_ctrl_cli(False, args.mix_name, user, conf.discobase)
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
            if mix_ctrl.mix.id_existing: # accessing a mix attr directly is bad practice
                if coll_ctrl.ONLINE:
                    # search_release returns an online or offline releases type object
                    # depending on the models online-state
                    discogs_rel_found = coll_ctrl.search_release(
                      args.add_release_to_mix)
                    mix_ctrl.add_discogs_track(discogs_rel_found, False,
                      args.mix_mode_add_at_pos,
                      track_no_suggest = coll_ctrl.first_track_on_release)
                else:
                    database_rel_found = coll_ctrl.search_release(
                            args.add_release_to_mix)
                    mix_ctrl.add_offline_track(database_rel_found, False,
                            args.mix_mode_add_at_pos)
            else:
                log.error("Mix not existing.")
        #### COPY A MIX
        elif user.WANTS_TO_COPY_MIX:
            mix_ctrl.copy_mix()
        #### EDIT MIX INFO
        elif user.WANTS_TO_EDIT_MIX:
            mix_ctrl.edit_mix()
                                       
        #### UPDATE TRACKS WITH DISCOGS INFO
        elif user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(coll_ctrl,
              start_pos=args.mix_mode_add_at_pos)
        #### UPDATE TRACKS WITH MUSICBRAINZ & ACOUSTICBRAINZ INFO
        elif user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE:
            mix_ctrl.update_track_info_from_brainz(coll_ctrl,
              start_pos=args.mix_mode_add_at_pos, detail=user.BRAINZ_SEARCH_DETAIL)


        #### BULK EDIT MIX COLUMNS
        elif user.WANTS_TO_BULK_EDIT:
            mix_ctrl.bulk_edit_tracks(args.bulk_edit, args.mix_mode_add_at_pos)

        #### JUST SHOW MIX-TRACKLIST:
        elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
            #pretty_print_mix_tracklist(mix_ctrl.id, mix_ctrl.info)
            mix_ctrl.view()


    ### SUGGEST MODE (was TRACK MODE)
    #if user.WANTS_TO_PULL_TRACK_INFO:
    #    mix_ctrl = Mix_ctrl_cli(False, False, user, conf.discobase)
    #    mix_ctrl.pull_track_info_from_discogs(coll_ctrl)
    #elif user.WANTS_SUGGEST_TRACK_REPORT:
    if user.WANTS_SUGGEST_TRACK_REPORT:
        coll_ctrl.track_report(args.suggest_search)
    if user.WANTS_SUGGEST_BPM_REPORT:
        coll_ctrl.bpm_report(args.suggest_bpm, 6)
    if user.WANTS_SUGGEST_KEY_REPORT:
        coll_ctrl.key_report(args.suggest_key)

    ### IMPORT MODE
    if user.WANTS_TO_IMPORT_COLLECTION:
        coll_ctrl.import_collection()
    if user.WANTS_TO_IMPORT_RELEASE:
        coll_ctrl.import_release(args.import_id)
    if user.WANTS_TO_ADD_AND_IMPORT_RELEASE:
        coll_ctrl.add_release(args.import_id)
    if user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS:
        coll_ctrl.import_collection(tracks=True)
    if user.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ:
        coll_ctrl.update_all_tracks_from_brainz(
            detail=user.BRAINZ_SEARCH_DETAIL)

    if user.DID_NOT_PROVIDE_COMMAND:
        if not coll_ctrl.ONLINE:
            merr ='Connection to your Discogs collection failed.'
            merr+='\nCheck your internet connection and DiscoDOS configuration (config.yaml)'
            merr+='\nBut anyway:'
            log.error(merr)
            coll_ctrl.cli.welcome_to_discodos()
            raise SystemExit(1)
        coll_ctrl.cli.welcome_to_discodos()
        coll_ctrl.cli.view_tutorial()
# __MAIN try/except wrap
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.error('Program interrupted!')
    #finally:
        #log.shutdown()
