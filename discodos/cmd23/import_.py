import logging
import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup

from discodos.cmd23.helper import AbbreviationGroup
from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.group(cls=AbbreviationGroup, name='import')
def import_group():
    """Imports a Discogs collection or adds further data to it.

    A typical workflow involves running import commands in this order:

    \b
    * basic
    * sales
    * tracks
    * brainz

    For single item imports use:

    \b
    * release
    * listing

    For single item removals use:

    \b
    * release -d
    * listing -d

    To remove data in bulk refer to the "clean" command group.
    """


@import_group.command(name='basic')
@click.pass_obj
def import_basic_cmd(helper ):
    """Initially imports Discogs release and user collection data.

    A basic subset of the details of all releases in the user's Discogs collection is
    imported into the DiscoBASE. Currently this includes artist, release title, catalog
    number, and the time of import.

    Information about collection items is also stored. This includes folders, notes,
    added date and rating (not all is made use of in DiscoDOS yet).

    Collection folder names are imported as a first step during an import run.

    The basic import can be re-run any time. Existing releases data is updated. Note
    that releases are not deleted on re-runs because they might still be used by the
    `sales` or `mixes` features of DiscoDOS. If "orphaned" collection item's are found,
    they are marked as such and won't show up in views anymore (e.g `dsc ls`). Orphaned
    in that context means: Not in the user's (online) collection anymore (e.g removed
    via the Discogs webinterface).

    To manually remove releases from the DiscoBASE anyway, use
    `dsc import release -d <release_id>`. This is able to remove them from the offline
    collection, the (online) Discogs collection and purge any release data from the
    DiscoBASE.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered collection and details import mode.")
        user.WANTS_TO_IMPORT_COLLECTION = True
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_COLLECTION:
        coll_ctrl.import_collection()


@import_group.command(name='tracks')
@click.option(
    "--resume", "--offset", "-r", "import_offset", metavar='OFFSET',
    type=int, default=0,
    help='''resumes the import at the given offset position (expects a number).''')
@click.pass_obj
def import_tracks_cmd(helper, import_offset):
    """Imports tracks and if not yet available releases from Discogs collection

    Is synonym to "dsc search all -u"

    Takes a significant amount of time but is the basis for DiscoDOS' features around
    "mixes management" and "brainz matching".
    """
    def update_user_interaction_helper(user):
        log.debug("Entered brainz import mode.")
        user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = True
        if import_offset > 0:
            user.RESUME_OFFSET = import_offset
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS:
        coll_ctrl.import_collection(
            tracks=True,
            offset=user.RESUME_OFFSET,
        )


@import_group.command(name='brainz')
@click.option(
    '--quick', '-q', is_flag=True,
    help='''''')
@click.option(
    "--resume", "--offset", "-r", "import_offset", metavar='OFFSET',
    type=int, default=0,
    help='''resumes the brainz matching process at the given offset position (expects a
    number). By default, tracks containing key and BPM already will be skipped. On a
    re-run using this option, the total number might be different already since the
    count of tracks without key and BPM might have changed.''')
@click.option(
    "--force-brainz", "-f", "import_brainz_force", is_flag=True,
    help=''' on MusicBrainz updates (-z, -zz), also tracks
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
def import_brainz_cmd(helper, quick, import_offset, import_brainz_force,
                      import_brainz_skip_unmatched):
    """Tries to match collection with MusicBrainz and add additional details.

    Details are MusicBrainz album and recording ID's and if available key and BPM from
    AcousticBrainz. Note that AcousticBrainz fetching might still work but is considered
    deprecated since the project has shutdown in 2022, and might be unavailable any time
    soon.

    Usually this action takes a long time unless -q is passed, which tries to find a
    match quickly but with a smaller chance of success.

    Only tracks already present in the DiscoBASE (using any of the import possibilites,
    eg. dsc mix -u, dsc import tracks, dsc search -u) will be updated.

    To really update _all_ tracks in the collection a full run of "dsc import tracks" is
    required prior to using this command.

    "dsc search all -z" is synonym to this option.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered brainz import mode.")
        user.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = True
        user.BRAINZ_SEARCH_DETAIL = 1
        if not quick:
            user.BRAINZ_SEARCH_DETAIL = 2
        if import_brainz_force:
            user.BRAINZ_FORCE_UPDATE = True
        if import_brainz_skip_unmatched:
            user.BRAINZ_SKIP_UNMATCHED = True
        if import_offset > 0:
            user.RESUME_OFFSET = import_offset
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ:
        coll_ctrl.update_all_tracks_from_brainz(
            detail=user.BRAINZ_SEARCH_DETAIL,
            offset=user.RESUME_OFFSET,
            force=user.BRAINZ_FORCE_UPDATE,
            skip_unmatched=user.BRAINZ_SKIP_UNMATCHED)


@import_group.command(name='release')
@click.argument('import_id', metavar='RELEASE_ID', type=str)
@optgroup.group("", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
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
@optgroup.option(
    '--delete', '-d', is_flag=True,
    help='''Removes all instances of a release from the Discogs collection and deletes
    them from the DiscoBASE.''')
@click.option(
    '--tracks', '-u', 'import_tracks', is_flag=True,
    help='''extends the Discogs import (also tracks will be imported). This is the
    same as "dsc search RELEASE_ID -u".''')
@click.pass_obj
def import_release_cmd(helper, import_id, import_add_coll, import_tracks, delete):
    """Imports a single release.

    Optionally imports tracks on the release or deletes a release entry entirely

    Usually the release must be in the Discogs collection already but an alternative way
    for adding newly gained releases is using the `-a` option. The flag enables releases
    being added to the Discogs collection and additionally added to the local DiscoBASE.
    """

    def update_user_interaction_helper(user):
        log.debug("Entered single release import mode.")
        if delete:
            user.WANTS_TO_REMOVE_AND_DELETE_RELEASE = True
        elif import_id != 0 and import_add_coll:
            if import_tracks:
                user.WANTS_TO_ADD_AND_IMPORT_RELEASE_WITH_TRACKS = True
            else:
                user.WANTS_TO_ADD_AND_IMPORT_RELEASE = True
        else:
            if import_tracks:
                user.WANTS_TO_IMPORT_RELEASE_WITH_TRACKS = True
            else:
                user.WANTS_TO_IMPORT_RELEASE = True
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_RELEASE:
        coll_ctrl.import_release(import_id)
    if user.WANTS_TO_IMPORT_RELEASE_WITH_TRACKS:
        coll_ctrl.import_release(import_id)
        coll_ctrl.update_single_track_or_release_from_discogs(
            import_id, rel_title="", track_no="*"
        )
    if user.WANTS_TO_ADD_AND_IMPORT_RELEASE:
        coll_ctrl.add_release(import_id)
    if user.WANTS_TO_ADD_AND_IMPORT_RELEASE_WITH_TRACKS:
        coll_ctrl.update_single_track_or_release_from_discogs(
            import_id, rel_title="", track_no="*"
        )
    if user.WANTS_TO_REMOVE_AND_DELETE_RELEASE:
        coll_ctrl.remove_and_delete_release(import_id)


@import_group.command(name='sales')
@click.option(
    "--light", "-l", is_flag=True,
    help='''Light import is for subsequent quick updates: Only fetches sales status (For
    Sale, Expired, Sold, Pending)'''
)
@click.pass_obj
def import_sales_cmd(helper, light):
    """Imports the marketplace inventory.
    """

    def update_user_interaction_helper(user):
        log.debug("Entered import sales inventory mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    coll_ctrl.import_sales_inventory(light_import=light)


@import_group.command(name='listing')
@click.argument('listing_id', type=int)
@click.option(
    '--delete', '-d', is_flag=True,
    help='''Removes listing from Discogs Marketplace and deletes from DiscoBASE.''')
@click.pass_obj
def import_listing_cmd(helper, listing_id, delete):
    """Imports a single marketplace listing or removes and deletes it.
    """

    def update_user_interaction_helper(user):
        log.debug("Entered import listing mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if delete:
        coll_ctrl.remove_and_delete_sales_listing(listing_id)
        return
    coll_ctrl.import_sales_listing(listing_id, display_help=True)
