import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
from click_option_group import RequiredAnyOptionGroup

from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli


@click.command(name='search')
@click.argument('release_search', metavar='SEARCH_TERMS')
@click.option(
    "-t", "--track", 'track_to_add', type=str, metavar='TRACK_NUMBER',
    help='''In combination with -m this option adds the given track number (eg.
    A1, AA, B2, ...) to the mix passed via -m; in combination with -z, -zz or
    -u the given track is the one being updated with *Brainz or Discogs
    details; in combination with -e the given track is the one being edited.
    The special keyword "all" can be used to process all tracks on the found
    release.''')
@click.option(
    "-p", "--pos", 'add_at_pos', type=str, metavar='POS_IN_MIX',
    help='''In combination with -m this option states that we'd like to insert
    the track at the given position (eg. 1, 14, ...), rather than at the end of
    the mix; in combination with -z, -zz, -u or -e this option is ignored.''',
    default=0)
@click.option(
    "--resume", "search_offset", metavar='OFFSET',
    type=int, default=0,
    help='''Resumes long-running processes at the given offset position
    (expects a number). You can combine this option currently with *Brainz
    matching operations only (-z, -zz) ''')
@optgroup.group("Actions", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    "-m", "--mix", 'add_to_mix', type=str, default=0,
    metavar='MIX_NAME',
    help='''Adds a track of the found release to the given mix ID (asks which
    track to add in case -t is missing).''')
@optgroup.option(
    "-u", "--discogs-update", 'search_discogs_update', is_flag=True,
    default=0,
    help='''Updates found release/track with Discogs track/artist details (asks
    which track to update in case -t is missing).''')
@optgroup.option(
    "-z", "--brainz-update", 'search_brainz_update', count=True,
    default=0,
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
    # coll_ctrl = Coll_ctrl_cli(
    #     False, helper, conf.discogs_token, conf.discogs_appid, conf.discobase,
    #     conf.musicbrainz_user, conf.musicbrainz_password )
