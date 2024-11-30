import logging
import click

from discodos.ctrl import CollectionControlCommandline
from discodos.utils import RECORD_CHOICES, SLEEVE_CHOICES, STATUS_CHOICES


log = logging.getLogger('discodos')


@click.command(name="sell")
@click.pass_obj
@click.argument("query", nargs=-1)
@click.option(
    "--edit", "-e", "listing_id", type=int, help="Edit an existing sales listing."
)
@click.option(
    "--id",
    "-i",
    "release_id",
    type=int,
    help="Omit search by passing a release ID with this option.",
)
@click.option(
    "-c",
    "--condition",
    type=click.Choice(RECORD_CHOICES, case_sensitive=True),
    default="VG+",
    help="Condition of the record.",
)
@click.option(
    "-s",
    "--sleeve-condition",
    type=click.Choice(SLEEVE_CHOICES, case_sensitive=True),
    default="generic",
    help="Condition of the sleeve.",
)
@click.option(
    "-p",
    "--price",
    type=float,
    default=None,
    help="Listing price for the record. Leave blank for suggested price.",
)
@click.option(
    "-a",
    "--status",
    type=click.Choice(STATUS_CHOICES, case_sensitive=True),
    default="draft",
    help="Initial status of the listing.",
)
@click.option(
    "-l",
    "--location",
    type=str,
    help="Location of the record in storage (e.g., shelf or bin label).",
)
@click.option(
    "-o",
    "--allow-offers",
    is_flag=True,
    default=False,
    help="Allow buyers to make offers on this listing.",
)
@click.option("-m", "--comments", type=str, help="Public comments about the listing.")
@click.option(
    "-n", "--private-comments", type=str, help="Private comments about the listing."
)
def sell_cmd(helper, query, listing_id, release_id, condition, sleeve_condition, price,
             status, location, allow_offers, comments, private_comments):
    """
    List a record for sale on Discogs.

    Lists the specified record for sale with details such as condition, price, quantity,
    and so on. Leave price empty to fetch a suggestion for the given record condition.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered sell mode.")
        user.WANTS_ONLINE = True
        if listing_id:
            user.WANTS_TO_EDIT_SALES_LISTING = True
        else:
            user.WANTS_TO_ADD_SALES_LISTING = True
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_TO_ADD_SALES_LISTING:
        coll_ctrl.sell_record_wizard(
            query,
            release_id,
            condition,
            sleeve_condition,
            price,
            status,
            location,
            allow_offers,
            comments,
            private_comments,
        )
    if user.WANTS_TO_EDIT_SALES_LISTING:
        coll_ctrl.edit_sales_listing(
            listing_id,
            condition,
            sleeve_condition,
            price,
            status,
            location,
            allow_offers,
            comments,
            private_comments,
        )
