import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
import logging

from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli


@click.command(name='import')
@click.argument('import_id', metavar='RELEASE_ID', type=int, required=False,
                 default='0')
@optgroup.group("Actions", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    '--add-to-collection', '-a', 'import_add_coll', is_flag=True,
    help='''The recommended and fastest way of adding newly gained releases to
    your collection. The given release ID is added to your Discogs collection
    (equal to clicking "Add to collection" on the Discogs webinterface  as well
    as added to the local DiscoBASE. For performance's sake though, we don't do
    a time-consuming check whether or not the release is in the (online)
    collection via the Discogs API, we just do a quick check for the presence
    of the ID in the local DiscoBASE. This safes us a lot of time and is a good
    enough solution to prevent duplicates.
    ''')
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
    "--resume", "--offset", "import_offset", metavar='OFFSET', type=int,
    default=0,
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
    "--skip-unmatched", "-s", "import_brainz_skip_unmatched",
    is_flag=True,
    help='''this option is useful on re-runs of MusicBrainz/AcousticBrainz
    updates (-z, -zz) to speed up things a little. Only tracks that previosuly
    where matched with MusicBrainz successfully (have a MusicBrainz Recording
    ID already saved in the DiscoBASE), are tried to be matched and updated.
    ''')
@click.pass_obj
def import_cmd(helper, import_id, import_add_coll, import_tracks,
               import_brainz, import_offset, import_brainz_force,import_brainz_skip_unmatched):
    """
    Imports a Discogs collection or adds single releases to the collection.

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
    click.echo(f'Hello {import_id}')
