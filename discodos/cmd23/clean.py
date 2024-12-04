import logging
import click
# from click_option_group import optgroup, MutuallyExclusiveOptionGroup

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.group(name='clean')
def clean_group():
    """Clean up orphaned DiscoBASE entries."""

@clean_group.command(name='sales')
@click.option(
    "--resume", "-r", "offset", metavar='OFFSET',
    type=int, default=0,
    help='''Resumes at the given offset position (expects a number).''')
@click.option(
    "--force", "-f", is_flag=True,
    help='''Don't ask, just do!''')
@click.pass_obj
def clean_sales_cmd(helper, force, offset):
    """
    Clean up sales inventory. Remove entries deleted from Discogs Marketplace inventory.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered clean up DiscoBASE sales inventory mode.")
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    coll_ctrl.cleanup_sales_inventory(force=force, offset=offset)
