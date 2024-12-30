import logging
import click

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    },
    name="links",
)
@click.argument("search_terms", metavar="SEARCH_TERMS", nargs=-1)
@click.option("--order-by", "-o", type=str, default="d_artist, discogs_title",
              help="order by DiscoBASE field")
@click.pass_obj
def links_cmd(helper, search_terms, order_by):
    """Prints a list of releases and their corresponding links to online services.

    Hyperlinks include Discogs release URL, MusicBrainz release URL and Discogs
    Marketplace listing ID (when listed for sale).

    Supports key=value search terms.
    """
    def update_user_interaction_helper(user):
        user.WANTS_ONLINE = True
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    try:  # Catch when `=` character is missing and assume title column
        search_key_value = coll_ctrl.prepare_key_value_search(query=search_terms)
    except ValueError as error:
        coll_ctrl.cli.p(error)

    coll_ctrl.view_links_list(query=search_key_value, orderby=order_by)
