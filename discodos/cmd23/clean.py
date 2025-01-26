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


@clean_group.command(name='releases')
@click.option(
    "--resume", "-r", "offset", metavar='OFFSET',
    type=int, default=0,
    help='''Resumes at the given offset position (expects a number).''')
@click.pass_obj
def clean_releases_cmd(helper, offset):
    """
    Clean up the DiscoBASE release table.

    Deletes entries in the release table if not used by any `mix`, `sales listing` or
    `collection item` anymore.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered clean up DiscoBASE releases mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    coll_ctrl.cleanup_releases(offset=offset)
