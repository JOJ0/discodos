import logging
import click

from discodos.cmd23.helper import AbbreviationGroup
from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.group(cls=AbbreviationGroup, name='clean')
def clean_group():
    """Clean up orphaned DiscoBASE entries."""

@clean_group.command(name='sales')
@click.option(
    "--resume", "-r", "offset", metavar='OFFSET',
    type=int, default=0,
    help='''Resumes at the given offset position (expects a number).''')
@click.pass_obj
def clean_sales_cmd(helper, offset):
    """Clean up the DiscoBASE sales inventory.

    Remove entries from the DiscoBASE sales inventory when they have been removed from
    the online Discogs Marketplace inventory.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered clean up DiscoBASE sales inventory mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    coll_ctrl.cleanup_sales_inventory(offset=offset)


@clean_group.command(name='collection')
@click.option(
    "--resume", "-r", "offset", metavar='OFFSET',
    type=int, default=0,
    help='''Resumes at the given offset position (expects a number).''')
@click.pass_obj
def clean_collection_cmd(helper, offset):
    """
    Clean up the DiscoBASE collection.

    Marks items orphaned in the release table if non-existent in the online Discogs
    collection anymore.

    TLDR, it uses the the in_d_collection flag in the release table to keep track of the
    online collection state. It does not delete rows in the releases table ever (use the
    "import release -d" flag to fix such issues). The reason for that is that release
    data might still be required for DiscoDOS' sales inventory or mixes related
    features.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered clean up DiscoBASE collection inventory mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    coll_ctrl.cleanup_collection(offset=offset)
