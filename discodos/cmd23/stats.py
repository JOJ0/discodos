import logging
import click

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.command(name='stats')
@click.pass_obj
def stats_cmd(helper):
    """
    Displays statistics about the collection.

    Besides showing stats like the size of the collection (on Discogs vs. in
    the DiscoBASE) also counts on existing mixes, how many tracks they contain
    and which additional metadata is present, are availalbe.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered stats mode.")
        user.WANTS_TO_SHOW_STATS = True
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)
    coll_ctrl.view_stats()
