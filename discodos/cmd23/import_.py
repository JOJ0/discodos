import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
import logging

from discodos.ctrls import Coll_ctrl_cli

log = logging.getLogger('discodos')


@click.command(name='import')
@click.argument('import_id', metavar='RELEASE_ID', required=False,
                type=int, default='0')
@optgroup.group("Actions", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    '--add-to-collection', '-a', 'import_add_coll', is_flag=True,
    help='''The recommended and fastest way of adding newly gained releases to
    your collection. The given release ID is added to your Discogs collection
    (equal to clicking "Add to collection" on the Discogs webinterface  as well
    as added to the local DiscoBASE. For performance's sake though, we don't do
    a time-consuming check whether or not the release is in the (online)
    collection via the Discogs API, we just do a quick check for the presence
    of the ID in the (local) DiscoBASE. This safes us a lot of time and is a
    good enough solution to prevent duplicates.''')
@optgroup.option(
    '--tracks', '-u', 'import_tracks', is_flag=True,
    help='''extends the Discogs import (releases and also tracks will be
    downloaded) - takes siginficantly longer than the regular import. Note:
    This is the same as "disco search all -u".''')
@optgroup.option(
    '--brainz', '-z', 'import_brainz', count=True, default=0,
    help='''imports additional information from MusicBrainz/AcousticBrainz
    (Release MBID, Recording MBID, musical key, chords key, BPM). Usually this
    action takes a long time; -z tries to find a match quickly, -zz tries
    harder but requires even more time. Only tracks already present in the
    DiscoBASE (using any of the import possibilites, eg. disco mix -u, disco
    import -u, disco search -u) will be updated. Tracks containing
    *Brainz-fetched key/BPM already will be skipped. To really update _all_
    tracks in the collection an extended Discogs import (disco import -u) is
    required prior to using -z, -zz. Also note that "disco search all -z" is
    synonym to this option.''')
@click.option(
    "--resume", "--offset", "import_offset", metavar='OFFSET',
    type=int, default=0,
    help='''resumes long-running processes at the given offset position
    (expects a number). You can combine this option currently with the *Brainz
    matching import operation only (-z, -zz). Note: By default, tracks
    containing key and BPM already will be skipped. On a re-run using this
    option, the total number might be different already since the count of
    tracks without key and BPM might have changed.''')
@click.option(
    "--force-brainz", "-f", "import_brainz_force", is_flag=True,
    help='''on MusicBrainz/AcousticBrainz updates (-z, -zz), also tracks
    containing key and BPM information in the DiscoBASE already, will tried to
    be matched and updated.''')
@click.option(
    "--skip-unmatched", "-s", "import_brainz_skip_unmatched", is_flag=True,
    help='''this option is useful on re-runs of MusicBrainz/AcousticBrainz
    updates (-z, -zz) to speed up things a little. Only tracks that previosuly
    where matched with MusicBrainz successfully (have a MusicBrainz Recording
    ID already saved in the DiscoBASE), are tried to be matched and updated.
    ''')
@click.pass_obj
def import_cmd(helper, import_id, import_add_coll, import_tracks,
               import_brainz, import_offset, import_brainz_force,
               import_brainz_skip_unmatched):
    """Imports a Discogs collection or adds single releases to the collection.

    The local database is referred to as DiscoBASE. RELEASE_ID is the Discogs
    release ID you want to import to the DiscoBASE. If left out, the whole
    collection will be imported. Option -a adds the release to the Discogs
    collection _and_ additionally imports it to the DiscoBASE.

    Note that a regular import of a given release ID (import RELEASE_ID) is
    rather slow: Technical limitations that are out of our hands require us to
    run through all of the releases in the collection via the Discogs API.
    Unfortunately Discogs does not allow us to search for release IDs in the
    user collection directly.

    That is the reason why the recommended way of adding newly gained releases
    is using the -a option (import -a RELEASE_ID).
    """
    def update_user_interaction_helper(user):
        log.debug("Entered import mode.")
        if import_id != 0 and import_add_coll:
            user.WANTS_TO_ADD_AND_IMPORT_RELEASE = True
        elif import_id == 0 and import_add_coll:
            log.error("Release ID missing. Which release should be added and "
                      "imported?")
            raise SystemExit(1)
        elif import_id == 0:
            if import_tracks:
                user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = True
                if import_offset > 0:
                    user.RESUME_OFFSET = import_offset
                    m_r ='Resuming is not possible in combination with '
                    m_r+='"import -u/--discogs-update". Try it with '
                    m_r+='"mix -u/--discogs-update". Also it works '
                    m_r+='together with "import -zz/brainz-update" '
                    m_r+='and "mix -zz/--brainz-update"'
                    log.error(m_r)
                    raise SystemExit(1)
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
            else:
                user.WANTS_TO_IMPORT_COLLECTION = True
        else:
            if import_brainz or import_tracks:
                log.error("You can't combine a single release import with "
                          "-z or -u.")
                raise SystemExit(1)
            else:
                user.WANTS_TO_IMPORT_RELEASE = True
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = Coll_ctrl_cli(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_IMPORT_COLLECTION:
        coll_ctrl.import_collection()
    if user.WANTS_TO_IMPORT_RELEASE:
        coll_ctrl.import_release(import_id)
    if user.WANTS_TO_ADD_AND_IMPORT_RELEASE:
        coll_ctrl.add_release(import_id)
    if user.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS:
        coll_ctrl.import_collection(tracks=True)
    if user.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ:
        coll_ctrl.update_all_tracks_from_brainz(
            detail=user.BRAINZ_SEARCH_DETAIL,
            offset=user.RESUME_OFFSET,
            force=user.BRAINZ_FORCE_UPDATE,
            skip_unmatched=user.BRAINZ_SKIP_UNMATCHED)
