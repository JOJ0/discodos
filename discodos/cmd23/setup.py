import logging
import click

from discodos.config import Db_setup
from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.command(name='setup')
@click.option(
    "--force", "force_upgrade_schema", is_flag=True,
    help='''Force-upgrade the database schema - use with caution!''')
@click.pass_obj
def setup_cmd(helper, force_upgrade_schema):
    """Sets up the DiscoBASE and handles database schema upgrades.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered setup mode.")
        user.WANTS_TO_LAUNCH_SETUP = True
        if force_upgrade_schema is True:
            user.WANTS_TO_FORCE_UPGRADE_SCHEMA = True
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    # INFORM USER what this subcommand does
    coll_ctrl.cli.p(
        "This is DiscoDOS setup. If you don't see any output below, "
        "there was nothing to do."
    )
    # SETUP DB
    setup = Db_setup(user.conf.discobase)
    setup.create_tables()
    if user.WANTS_TO_FORCE_UPGRADE_SCHEMA:
        setup.upgrade_schema(force_upgrade=True)
    else:
        setup.upgrade_schema()
    # INSTALL CLI if not there yet (only in self-contained package)
    if user.conf.frozen:
        user.conf.install_cli()
