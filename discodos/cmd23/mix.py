import logging
import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup

from discodos.ctrl import CollectionControlCommandline, MixControlCommandline

log = logging.getLogger('discodos')


@click.command(name='mix')
@click.argument('mix_name', metavar='MIX_NAME', default='all', required=False)
@click.option(
    "-v", "--verbose",
    'verbose_tracklist',
    count=True, default=0,
    help='''increases mix tracklist view detail. -v adds tracknames,
    artists, transition rating/notes and general track notes.
    -vv shows when and how MusicBrainz matching was done and also direct
    weblinks to Discogs releases, MusicBrainz releases/recordings and
    AccousticBrainz recordings.''')
@click.option(
    "-f", "--format", "table_format", metavar='FORMAT',
    type=str, default='',
    help='''overrides the default output format for rendered tables. FORMAT
    is passed through to the underlying library (tabulate). Choose
    from: plain, simple, github, grid, fancy_grid, pipe, orgtbl, jira,
    presto, pretty psql, rst, mediawiki, moinmoin, youtrack, html,
    unsafehtml, latex, latex_raw latex_booktabs, latex_longtable, textile,
    tsv.''')
@optgroup.group("Actions", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    "-c", "--create-mix", is_flag=True,
    help='creates new mix (named as given in mix_name argument).')
@optgroup.option(
    "-D", "--delete-mix", is_flag=True,
    help='deletes the mix MIX_NAME and all its contained tracks!')
@optgroup.option(
    "-e", "--edit", 'edit_mix_track', type=str,
    metavar='POSITION',
    help='''edits/adds details of a track in a mix (editable fields:
    key, BPM, track number, position in mix, key notes, transition rating,
    transition notes, general track notes, custom MusicBrainz recording ID).''')
@optgroup.option(
    "-E", "--edit-mix", is_flag=True,
    help='edits/adds general info about a mix (name, played date, venue).')
@optgroup.option(
    "-b", "--bulk-edit", type=str,
    metavar='FIELDS',
    help='''bulk-edits specific fields of each track in mix.
    Syntax of FIELDS argument: <field1>,<field2>,...
    available fields: key,bpm,track_no,track_pos,key_notes,trans_rating,
    trans_notes,notes,m_rec_id_override.''')
@optgroup.option(
    "-a", "--add-to-mix",
    'add_release_to_mix', type=str, metavar='SEARCH_TERMS',
    help='''searches for release/track in collection and adds it to the mix,
    This option is actually a shortcut to "disco search -m mix_name
    search_term" and behaves identically. If SEARCH_TERMS is a number, it
    is assumed being a Discogs release ID. A quick database check is done
    and if non-existent yet, the release is 1) added to the Discogs collection
    and 2) imported to DiscoBASE. This is a convenience function eg when trying
    to quickly add a release to the mix that's not in the DiscoBASE yet (possibly
    an only recently gained record?).''')
@optgroup.option(
    "-r", "--reorder-tracks",
    'reorder_from_pos', type=int,
    metavar='POSITION',
    help='''reorders tracks in current mix, starting at POSITION.
    Note that this is a troubleshooting function and usually shouldn't
    be necessary to use.''')
@optgroup.option(
    "-d", "--delete-track",
    'delete_track_pos', type=int,
    metavar='POSITION',
    help='removes the track at the given position from the mix.')
@optgroup.option(
    "--copy",
    'copy_mix', is_flag=True,
    help='copies the mix given in mix_name argument. Asks for new name!')
@optgroup.option(
    "-u", "--discogs-update",
    is_flag=True,
    help='''updates tracks in current mix with additional info from Discogs.
    Can be combined with -p when mix ID provided or with --resume when mix ID
    not provided (all tracks in mixes update).''')
@optgroup.option(
    "-z", "--brainz-update", count=True, default=0,
    help='''updates tracks in current mix with additional info from MusicBrainz and AcousticBrainz.
    Leave out mix ID to update every track contained in any mix.
    -z quick match, -zz detailed match (takes longer, but more results).
    Can be combined with -p when mix ID provided or with --resume when mix ID
    not provided (all tracks in mixes *Brainz matching).''')
@click.option(
    "-p", "--pos",
    'mix_mode_add_at_pos', type=int, metavar='POSITION',
    help='''in combination with -a this option adds the found release/track
    at the given position in the mix (rather than at the end). In
    combination with -u, -z or -zz the update process is started at the given
    position in the mix.''')
@click.option(
    "--resume", "mix_offset", metavar='OFFSET',
    type=int, default=0,
    help='''resumes long-running processes at the given offset position
    (expects a number). You can combine this option currently
    with "all tracks in mixes Discogs update" (disco mix -u) or with
    "all tracks in mixes *Brainz matching" (disco mix -z, disco mix -zz).''')
@click.option(
    "-s", "--sort", "mix_sort", metavar='COLUMN',
    type=str, default='track_pos asc',
    help='''sort tracklist by specified column. add "asc" or "desc" to
    specify ascending or descending sort order. "track_pos asc" is the
    default. Experimental feature: currently expects sql column names.''')
@click.pass_obj
def mix_cmd(helper, mix_name, verbose_tracklist, table_format, create_mix,
            delete_mix, edit_mix_track, edit_mix, bulk_edit,
            add_release_to_mix, reorder_from_pos, delete_track_pos, copy_mix,
            discogs_update, brainz_update, mix_mode_add_at_pos, mix_offset,
            mix_sort):
    """Manages mixes.

    Mixes essentially are ordered collections of tracks from a user's
    collection. This subcommand creates, deletes, fills and alters them.

    MIX_NAME is the name or the ID of the mix that should be handled. If left
    out, the list of existing mixes is displayed and all other arguments are
    ignored.
    """
    def update_user_interaction_helper(user):
        if 'mix_name':
            user.TABLE_FORMAT_OVERRIDE = table_format
            if mix_name == "all":
                user.WANTS_TO_SHOW_MIX_OVERVIEW = True
                user.WANTS_ONLINE = False
                if create_mix is True:
                    log.error("Please provide a mix name to be created!")
                    log.error('(Mix name "all" is not valid.)')
                    raise SystemExit(1)
                elif delete_mix is True:
                    log.error("Please provide a mix name or ID to be deleted!")
                    raise SystemExit(1)
                if discogs_update:
                    user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    user.WANTS_ONLINE = True
                    if mix_offset > 0:
                        user.RESUME_OFFSET = mix_offset
                if brainz_update:
                    user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    user.WANTS_ONLINE = True
                    user.BRAINZ_SEARCH_DETAIL = brainz_update
                    if brainz_update > 1:
                        user.BRAINZ_SEARCH_DETAIL = 2
                    if mix_offset > 0:
                        user.RESUME_OFFSET = mix_offset
            else:
                user.WANTS_TO_SHOW_MIX_TRACKLIST = True
                user.WANTS_ONLINE = False
                if mix_sort:
                    user.MIX_SORT = mix_sort
                if create_mix:
                    user.WANTS_TO_CREATE_MIX = True
                    user.WANTS_ONLINE = False
                if edit_mix_track:
                    user.WANTS_TO_EDIT_MIX_TRACK = True
                    user.WANTS_ONLINE = False
                if verbose_tracklist == 1:
                    user.WANTS_VERBOSE_MIX_TRACKLIST = True
                    user.WANTS_ONLINE = False
                if verbose_tracklist == 2:
                    user.WANTS_MUSICBRAINZ_MIX_TRACKLIST = True
                    user.WANTS_ONLINE = False
                if reorder_from_pos:
                    user.WANTS_TO_REORDER_MIX_TRACKLIST = True
                    user.WANTS_ONLINE = False
                if delete_track_pos:
                    user.WANTS_TO_DELETE_MIX_TRACK = True
                    user.WANTS_ONLINE = False
                if add_release_to_mix:
                    user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = True
                    user.WANTS_ONLINE = True
                    if mix_mode_add_at_pos:
                        user.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = True
                if copy_mix:
                    user.WANTS_TO_COPY_MIX = True
                    user.WANTS_ONLINE = False
                if discogs_update:
                    user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    user.WANTS_ONLINE = True
                    if mix_offset > 0:
                        m_r ="Resuming is not possible in single-mix "
                        m_r+="-u/--discogs-update. "
                        m_r+="Use -p/--pos instead."
                        log.error(m_r)
                        raise SystemExit(1)
                if delete_mix:
                    user.WANTS_TO_DELETE_MIX = True
                    user.WANTS_ONLINE = False
                if bulk_edit:
                    user.WANTS_TO_BULK_EDIT = True
                if brainz_update:
                    user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    user.WANTS_ONLINE = True
                    user.BRAINZ_SEARCH_DETAIL = brainz_update
                    if brainz_update > 1:
                        user.BRAINZ_SEARCH_DETAIL = 2
                    if mix_offset > 0:
                        m_r ="Resuming is not possible in single-mix "
                        m_r+="-z/--brainz-update. "
                        m_r+="Use -p/--pos instead."
                        log.error(m_r)
                        raise SystemExit(1)
                if edit_mix:
                    user.WANTS_TO_EDIT_MIX = True
                    user.WANTS_ONLINE = False
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    # NO MIX ID GIVEN #########################################################
    # SHOW LIST OF MIXES ######################################################
    if user.WANTS_TO_SHOW_MIX_OVERVIEW:
        mix_ctrl = MixControlCommandline(False, mix_name, user, user.conf.discobase)
        if user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(
                coll_ctrl,
                offset=user.RESUME_OFFSET
            )
        elif user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE:
            mix_ctrl.update_track_info_from_brainz(
                coll_ctrl,
                detail=user.BRAINZ_SEARCH_DETAIL,
                offset=user.RESUME_OFFSET
            )
        else:
            mix_ctrl.view_mixes_list()

    # MIX ID GIVEN ############################################################
    # SHOW MIX DETAILS ########################################################
    elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
        log.info("A mix_name or ID was given. Instantiating MixControlCommandline class.\n")
        mix_ctrl = MixControlCommandline(
            False, mix_name, user, user.conf.discobase
        )
        # coll_ctrl = CollectionControlCommandline(conn, user)
        # CREATE A NEW MIX ####################################################
        if user.WANTS_TO_CREATE_MIX:
            mix_ctrl.create()
            # mix is created (or not), nothing else to do
            raise SystemExit(0)
        # DELETE A MIX ########################################################
        if user.WANTS_TO_DELETE_MIX:
            mix_ctrl.delete()
            # mix is deleted (or not), nothing else to do
            raise SystemExit(0)
        # DO STUFF WITH EXISTING MIXES ########################################
        # EDIT A MIX-TRACK ####################################################
        if user.WANTS_TO_EDIT_MIX_TRACK:
            mix_ctrl.edit_track(edit_mix_track)
        # REORDER TRACKLIST ###################################################
        elif user.WANTS_TO_REORDER_MIX_TRACKLIST:
            coll_ctrl.cli.p(f"Tracklist reordering starting at position "
                            f"{reorder_from_pos}")
            mix_ctrl.reorder_tracks(reorder_from_pos)
        # DELETE A TRACK FROM MIX #############################################
        elif user.WANTS_TO_DELETE_MIX_TRACK:
            mix_ctrl.delete_track(delete_track_pos)
        # SEARCH FOR A RELEASE AND ADD IT TO MIX (same as in release mode) ####
        elif user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
            if mix_ctrl.mix.id_existing:  # FIXME direct accessing of mix attr
                if coll_ctrl.ONLINE:
                    # search_release returns an online or offline releases type
                    # object depending on the models online-state
                    discogs_rel_found = coll_ctrl.search_release(
                        add_release_to_mix
                    )
                    mix_ctrl.add_discogs_track(
                        discogs_rel_found, False,
                        mix_mode_add_at_pos,
                        track_no_suggest=coll_ctrl.first_track_on_release
                    )
                else:
                    database_rel_found = coll_ctrl.search_release(
                        add_release_to_mix
                    )
                    mix_ctrl.add_offline_track(
                        database_rel_found,
                        False,
                        mix_mode_add_at_pos
                    )
            else:
                log.error("Mix not existing.")
        # COPY A MIX ##########################################################
        elif user.WANTS_TO_COPY_MIX:
            mix_ctrl.copy_mix()
        # EDIT MIX INFO #######################################################
        elif user.WANTS_TO_EDIT_MIX:
            mix_ctrl.edit_mix()
        # UPDATE TRACKS WITH DISCOGS INFO #####################################
        elif user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(
                coll_ctrl,
                start_pos=mix_mode_add_at_pos
            )
        # UPDATE TRACKS WITH MUSICBRAINZ & ACOUSTICBRAINZ INFO ################
        elif user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE:
            mix_ctrl.update_track_info_from_brainz(
                coll_ctrl,
                start_pos=mix_mode_add_at_pos,
                detail=user.BRAINZ_SEARCH_DETAIL
            )
        # BULK EDIT MIX COLUMNS ###############################################
        elif user.WANTS_TO_BULK_EDIT:
            mix_ctrl.bulk_edit_tracks(
                bulk_edit, mix_mode_add_at_pos
            )
        # JUST SHOW MIX-TRACKLIST #############################################
        elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
            mix_ctrl.view()
