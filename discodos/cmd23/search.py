import logging
import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup

from discodos.ctrl import CollectionControlCommandline, MixControlCommandline

log = logging.getLogger('discodos')


@click.command(name='search')
@click.argument('release_search', metavar='SEARCH_TERMS')
@click.option(
    "-t", "--track", 'track_to_add', metavar='TRACK_NUMBER',
    type=str, default=None,
    help='''In combination with -m this option adds the given track number (eg.
    A1, AA, B2, ...) to the mix passed via -m; in combination with -z, -zz or
    -u the given track is the one being updated with *Brainz or Discogs
    details; in combination with -e the given track is the one being edited.
    The special keyword "all" can be used to process all tracks on the found
    release.''')
@click.option(
    "-p", "--pos", 'add_at_pos', metavar='POS_IN_MIX',
    type=int, default=None,
    help='''In combination with -m this option states that we'd like to insert
    the track at the given position (eg. 1, 14, ...), rather than at the end of
    the mix; in combination with -z, -zz, -u or -e this option is ignored.''')
@click.option(
    "--resume", "search_offset", metavar='OFFSET',
    type=int, default=0,
    help='''Resumes long-running processes at the given offset position
    (expects a number). You can combine this option currently with *Brainz
    matching operations only (-z, -zz)''')
@optgroup.group("Actions", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    "-m", "--mix", 'add_to_mix', metavar='MIX_NAME',
    type=str, default=None,
    help='''Adds a track of the found release to the given mix ID (asks which
    track to add in case -t is missing).''')
@optgroup.option(
    "-u", "--discogs-update", 'search_discogs_update', is_flag=True,
    help='''Updates found release/track with Discogs track/artist details (asks
    which track to update in case -t is missing).''')
@optgroup.option(
    "-z", "--brainz-update", 'search_brainz_update',
    count=True, default=0,
    help='''Updates found release/track with additional info from MusicBrainz
    and AcousticBrainz. (asks which track to update in case -t is missing) -z
    quick match, -zz detailed match (takes longer, but more results).''')
@optgroup.option(
    "-e", "--edit", 'search_edit_track', is_flag=True,
    help='''Edits/adds details to a found release/track. Editable fields: key,
    BPM, key notes, general track notes, custom MusicBrainz recording ID. (asks
    which track to edit in case -t is missing).''')
@click.pass_obj
def search_cmd(helper, release_search, track_to_add, add_at_pos, search_offset,
               add_to_mix, search_discogs_update, search_brainz_update,
               search_edit_track):
    """Searches collection and launches actions on found items.

    Searches for releases and tracks in the Discogs collection. Several actions
    can be executed on the found items, eg. adding to a mix, updating track
    info from Discogs or fetching additional information from
    MusicBrainz/AcousticBrainz. View this subcommand's help: disco search -h.

    The collection is searched for SEARCH_TERMS. When offline, it
    searches through all releases' artists/titles only (eg tracknames not
    considered). When online, the Discogs API search engine is used and also
    tracknames, artists, labels and catalog numbers are looked through.  If
    your search term consists of multiple words, put them inside double quotes
    (eg. "foo bar term"). If you instead put a number as your search term, it
    is assumed you want to view exactly the Discogs release with the given ID.
    If search term is the special keyword "all", a list of all releases in the
    DiscoBASE is shown (including weblinks to Discogs/MusicBrainz release
    pages). In combination with -u, -z or -zz respectively, all tracks are
    updated. Note that this is exactely the same as "disco import" in
    combination with those options.
    """
    def update_user_interaction_helper(user):
        if release_search == "all":
            if search_discogs_update:
                # discogs update all
                user.WANTS_ONLINE = True
                user.WANTS_TO_LIST_ALL_RELEASES = True
                user.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = True
                if search_offset > 0:
                    user.RESUME_OFFSET = search_offset
                    m_r ='Resuming is not possible in combination with '
                    m_r+='"search all -u/--discogs-update". Try it with '
                    m_r+='"mix -u/--discogs-update". Also it works '
                    m_r+='together with "import -zz/brainz-update" '
                    m_r+='and "mix -zz/--brainz-update"'
                    log.error(m_r)
                    raise SystemExit(1)
            elif search_brainz_update:
                # brainz update all
                user.WANTS_ONLINE = True
                user.WANTS_TO_LIST_ALL_RELEASES = True
                user.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = True
                if search_brainz_update > 1:
                    user.BRAINZ_SEARCH_DETAIL = 2
                if search_offset > 0:
                    user.RESUME_OFFSET = search_offset
            else:
                # just list all
                user.WANTS_ONLINE = False
                user.WANTS_TO_LIST_ALL_RELEASES = True
        else:
            user.WANTS_TO_SEARCH_FOR_RELEASE = True
            if add_to_mix:
                if track_to_add and add_at_pos:
                    user.WANTS_TO_ADD_AT_POSITION = True
                else:
                    user.WANTS_TO_ADD_TO_MIX = True

            if search_discogs_update:
                if not user.WANTS_ONLINE:
                    log.error("You can't do that in offline mode!")
                    raise SystemExit(1)
                user.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = True
            elif search_brainz_update !=0:
                if not user.WANTS_ONLINE:
                    log.error("You can't do that in offline mode!")
                    raise SystemExit(1)
                user.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = True
                user.BRAINZ_SEARCH_DETAIL = search_brainz_update
                if search_brainz_update > 1:
                    user.BRAINZ_SEARCH_DETAIL = 2
            elif search_edit_track:
                user.WANTS_TO_SEARCH_AND_EDIT_TRACK = True
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_LIST_ALL_RELEASES:
        if user.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS:
            coll_ctrl.import_collection(tracks=True)
        elif user.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ:
            coll_ctrl.update_all_tracks_from_brainz(
                detail=user.BRAINZ_SEARCH_DETAIL,
                offset=user.RESUME_OFFSET
            )
        else:
            coll_ctrl.view_all_releases()
    elif user.WANTS_TO_SEARCH_FOR_RELEASE:
        searchterm = release_search
        msg_use = "Nothing more to do. Use -m <mix> to add to a "
        msg_use+= "mix, -e to edit, -u to update with Discogs information "
        msg_use+= "or -zz to update with *Brainz information. "
        msg_use+= "You can combine these options with -t too."
        if coll_ctrl.ONLINE:
            discogs_rel_found = coll_ctrl.search_release(searchterm)
            if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_AT_POSITION:
                mix_ctrl = MixControlCommandline(
                    False, add_to_mix, user, user.conf.discobase
                )
                mix_ctrl.add_discogs_track(
                    discogs_rel_found, track_to_add, add_at_pos,
                    track_no_suggest=coll_ctrl.first_track_on_release
                )
            elif user.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS:
                # online search gave us exactely one release in a list
                # print(discogs_rel_found)
                coll_ctrl.update_single_track_or_release_from_discogs(
                    discogs_rel_found['id'],
                    discogs_rel_found['title'],
                    track_to_add
                )
            elif user.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ:
                coll_ctrl.update_single_track_or_release_from_brainz(
                    discogs_rel_found['id'],
                    discogs_rel_found['title'],
                    track_to_add,
                    detail=user.BRAINZ_SEARCH_DETAIL
                )
            elif user.WANTS_TO_SEARCH_AND_EDIT_TRACK:
                coll_ctrl.edit_track(
                    discogs_rel_found['id'],
                    discogs_rel_found['title'],
                    track_to_add
                )
            else:
                # if discogs_rel_found: # prevents msg when nothing's found anyway
                coll_ctrl.cli.p(msg_use)
        else:  # when OFFLINE
            database_rel_found = coll_ctrl.search_release(searchterm)
            if not database_rel_found:
                return
            if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_AT_POSITION:
                mix_ctrl = MixControlCommandline(
                    False, add_to_mix, user, user.conf.discobase
                )
                mix_ctrl.add_offline_track(
                    database_rel_found, track_to_add,
                    add_at_pos
                )
            elif user.WANTS_TO_SEARCH_AND_EDIT_TRACK:
                coll_ctrl.edit_track(
                    database_rel_found[0]['discogs_id'],
                    database_rel_found[0]['discogs_title'],
                    track_to_add
                )
            else:
                if database_rel_found:  # prevents msg when nothing's found anyway
                    coll_ctrl.cli.p(msg_use)
