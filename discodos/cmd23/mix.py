import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
from click_option_group import RequiredAnyOptionGroup
import logging

from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli


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
    "all tracks in mixes *Brainz matching" (disco mix -z, disco mix -zz).
    ''')
@click.pass_obj
def mix_cmd(helper, mix_name, verbose_tracklist, table_format, create_mix,
            delete_mix, edit_mix_track, edit_mix, bulk_edit, add_release_to_mix,
            reorder_from_pos, delete_track_pos, copy_mix, discogs_update,
            brainz_update, mix_mode_add_at_pos, mix_offset):
    """Manages mixes.

    Mixes essentially are ordered collections of tracks from a user's
    collection. This subcommand creates, deletes, fills and alters them.

    MIX_NAME is the name or the ID of the mix that should be handled. If left
    out, the list of existing mixes is displayed and all other arguments are
    ignored.
    """
    click.echo(f'The mix command draft {mix_name}')
