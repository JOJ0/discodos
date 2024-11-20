import logging
import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.group(name='import')
def import_group():
    """Imports a Discogs collection or adds further data to it.

    A typical workflow involves running import commands in this order:

    \b
    * basic
    * details --tracks

    Optionally:

    \b
    * details --brainz
    * release`
    """
    pass


@import_group.command(name='basic')
@click.pass_obj
def import_basic_cmd(helper ):
    """Initially imports a Discogs collection.

    A very basic subset of the Discogs collection data is imported to the
    DiscoBASE. Currently this includes artist, release title, catalog number, a
    timestamp of the import time, and a flag named is_in_d_collection.

    The basic import can be re-run any time. It
    overwrites any existing data in the release table of the DiscoBASE, though
    additional information like the sales date is not overwritten when present
    already.

    The purpose of the is_in_d_collection flag marks releases that are not in
    the online Discogs collection anymore with a 0 (false). This helps to get
    the releases table in sync when releases have been removed using the Discogs
    web interface.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered collection and details import mode.")
        user.WANTS_TO_IMPORT_COLLECTION = True
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_COLLECTION:
        coll_ctrl.import_collection()


@import_group.command(name='details')
@optgroup.group("Actions", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    '--tracks', '-u', 'import_tracks', is_flag=True,
    help='''extends the Discogs import (releases and also tracks will be
    downloaded) - takes siginficantly longer than the regular import. Note:
    This is the same as "dsc search all -u".''')
@optgroup.option(
    '--brainz', '-z', 'import_brainz', count=True, default=0,
    help='''imports additional information from MusicBrainz
    (Release MBID, Recording MBID). Usually this
    action takes a long time; -z tries to find a match quickly, -zz tries
    harder but requires even more time. Only tracks already present in the
    DiscoBASE (using any of the import possibilites, eg. dsc mix -u, dsc
    import details -u, dsc search -u) will be updated. To really update _all_
    tracks in the collection an extended Discogs import (dsc import details -u) is
    required prior to using -z, -zz. Also note that "dsc search all -z" is
    synonym to this option.''')
@click.option(
    "--resume", "--offset", "-r", "import_offset", metavar='OFFSET',
    type=int, default=0,
    help='''resumes long-running processes at the given offset position
    (expects a number). You can combine this option currently with the *Brainz
    matching import operation only (-z, -zz). Note [deprecated]: By default, tracks
    containing key and BPM already will be skipped. On a re-run using this
    option, the total number might be different already since the count of
    tracks without key and BPM might have changed.''')
@click.option(
    "--force-brainz", "-f", "import_brainz_force", is_flag=True,
    help='''[deprecated] on MusicBrainz updates (-z, -zz), also tracks
    containing key and BPM information in the DiscoBASE already, will tried to
    be matched and updated.''')
@click.option(
    "--skip-unmatched", "-s", "import_brainz_skip_unmatched", is_flag=True,
    help='''this option is useful on re-runs of MusicBrainz
    updates (-z, -zz) to speed up things a little. Only tracks that previosuly
    where matched with MusicBrainz successfully (have a MusicBrainz Recording
    ID already saved in the DiscoBASE), are tried to be matched and updated.
    ''')
@click.pass_obj
def import_details_cmd(helper, import_tracks, import_brainz, import_offset,
               import_brainz_force, import_brainz_skip_unmatched):
    """Enriches the collection with more details.

    Details currently are information about tracks on a Discogs release and
    running a "matching process" with MusicBrainz. The latter adds MB album and
    recording ID's.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered collection and details import mode.")
        if import_tracks:
            user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = True
            if import_offset > 0:
                user.RESUME_OFFSET = import_offset
        elif import_brainz:
            user.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = True
            user.BRAINZ_SEARCH_DETAIL = import_brainz
            if import_brainz > 1:
                user.BRAINZ_SEARCH_DETAIL = 2
            if import_brainz_force:
                user.BRAINZ_FORCE_UPDATE = True
            if import_brainz_skip_unmatched:
                user.BRAINZ_SKIP_UNMATCHED = True
            if import_offset > 0:
                user.RESUME_OFFSET = import_offset
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS:
        coll_ctrl.import_collection(
            tracks=True,
            offset=user.RESUME_OFFSET,
        )
    if user.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ:
        coll_ctrl.update_all_tracks_from_brainz(
            detail=user.BRAINZ_SEARCH_DETAIL,
            offset=user.RESUME_OFFSET,
            force=user.BRAINZ_FORCE_UPDATE,
            skip_unmatched=user.BRAINZ_SKIP_UNMATCHED)


@import_group.command(name='release')
@click.argument('import_id', metavar='RELEASE_ID', type=int)
@click.option(
    '--add-to-collection', '-a', 'import_add_coll', is_flag=True,
    help='''The fastest way of adding newly gained releases to your collection.
    The given release ID is added to your Discogs collection (equal to clicking
    "Add to collection" on the Discogs webinterface) as well as added to the
    local DiscoBASE.

    For performance's sake though, we don't do a time-consuming check whether or
    not the release is in the (online) collection via the Discogs API, we just
    do a quick check for the presence of the ID in the (local) DiscoBASE. This
    safes us a lot of time and is a good enough solution to prevent
    duplicates.''')
@click.pass_obj
def import_release_cmd(helper, import_id, import_add_coll):
    """Imports a single release.

    Note that currently this is a rather time consuming process: Technical
    limitations that are out of our hands require running through all of the
    releases in the collection via the Discogs API. Unfortunately Discogs does
    not allow us to search for release IDs in the user collection directly.

    The recommended way of adding newly gained releases is using the -a option
    (import release -a RELEASE_ID) which is much faster. Using this flag, the
    release is added to Discogs collection and additionally added to the local
    DiscoBASE.
    """

    def update_user_interaction_helper(user):
        log.debug("Entered single release import mode.")
        if import_id != 0 and import_add_coll:
            user.WANTS_TO_ADD_AND_IMPORT_RELEASE = True
        else:
            user.WANTS_TO_IMPORT_RELEASE = True
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_RELEASE:
        coll_ctrl.import_release(import_id)
    if user.WANTS_TO_ADD_AND_IMPORT_RELEASE:
        coll_ctrl.add_release(import_id)


@import_group.command(name='sales')
@click.pass_obj
def import_sales_cmd(helper):
    """Imports the marketplace inventory.
    """

    def update_user_interaction_helper(user):
        log.debug("Entered import sales inventory mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    coll_ctrl.import_sales_inventory()
