import logging
import click

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')

@click.command(name='sell')
@click.pass_obj
@click.argument("release_id", type=int)
@click.option(
    "-c", "--condition",
    type=click.Choice(["M", "NM", "VG+", "VG", "G+", "G", "F", "P"],
                       case_sensitive=True),
    default="VG+",
    prompt="Record condition (M, NM, VG+, VG, G+, G, F, P)",
    help="Condition of the record."
)
@click.option(
    "-s", "--sleeve-condition",
    type=click.Choice(["M", "NM", "VG+", "VG", "G+", "G", "F", "P"],
                       case_sensitive=True),
    default="VG+",
    prompt="Sleeve condition",
    help="Condition of the sleeve."
)
@click.option(
    "-p", "--price",
    type=float,
    prompt="Price (enter 0 to fetch Discogs suggested price)",
    default=None,
    help="Listing price for the record. Leave blank for suggested price."
)
@click.option(
    "-a", "--status",
    type=click.Choice(["For Sale", "Draft"], case_sensitive=True),
    prompt="Status",
    default="For Sale",
    help="Initial status of the listing."
)
@click.option(
    "-l", "--location",
    type=str,
    prompt="Storage location",
    help="Location of the record in storage (e.g., shelf or bin label)."
)
@click.option(
    "-o", "--allow-offers",
    is_flag=True,
    default=True,
    prompt="Accept offers? (yes/no)",
    help="Allow buyers to make offers on this listing."
)
@click.option(
    "-m", "--comments",
    type=str,
    prompt="Public comments",
    help="Public comments about the listing."
)
@click.option(
    "-n", "--private-comments",
    type=str,
    prompt="Private comments",
    help="Private comments about the listing."
)
def sell_cmd(helper, release_id, condition, sleeve_condition, price, status,
             location, allow_offers, comments, private_comments):
    """
    List a record for sale on Discogs.

    Lists the specified record for sale with details such as condition, price, quantity,
    and so on. Leave price empty to fetch a suggestion for the given record condition.
    """
    def update_user_interaction_helper(user):
        log.debug("Entered sell mode.")
        user.WANTS_ONLINE = True
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if not coll_ctrl.ONLINE:
        log.warning("Online mode is required to list a record for sale.")
        return

    if not price:
        suggested_price = coll_ctrl.collection.fetch_price_suggestion(
            release_id, condition
        )
        if suggested_price:
            click.echo(
                f"Suggested price for condition '{condition}': "
                f"{suggested_price.currency} {suggested_price.value}"
            )
            price = click.prompt(
                "Accept?",
                type=float,
                default=round(suggested_price.value, 2),
            )
        else:
            click.echo("No suggested price available; please enter a price manually.")
            price = click.prompt("Price", type=float)

    log.info(f"Attempting to list record {release_id} for sale.")
    coll_ctrl.collection.list_for_sale(
        release_id=release_id,
        condition=condition,
        sleeve_condition=sleeve_condition,
        price=price,
        status=status,
        location=location,
        allow_offers=allow_offers,
        comments=comments,
        private_comments=private_comments
    )
    coll_ctrl.cli.p("Listed for sale.")
