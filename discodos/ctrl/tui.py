import logging
from sqlite3 import Row
from datetime import datetime
from rich.table import Table as rich_table
from rich.markdown import Markdown
from textual.app import App
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Digits, Footer, Label, Static, RichLog
from textual.coordinate import Coordinate

from discodos.model import DiscogsMixin

log = logging.getLogger('discodos')


class DiscodosListApp(App, DiscogsMixin):  # pylint: disable=too-many-instance-attributes
    """Inline Textual app to view and edit dsc ls results."""
    CSS_PATH = "tui_ls.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("l", "list_sale", "List for sale"),
        ("d", "draft_sale", "Set to draft"),
        ("s", "toggle_sold", "Toggle sold (in DB)"),
        ("c", "fix_coll", "Sync Coll. Flag (in DB)"),
        ("r", "remove_coll", "Remove from Coll."),
        ("e", "edit_release", "Edit release"),
        ("E", "edit_sale", "Edit sales listing"),
    ]

    def __init__(self, rows, headers, discogs=None, collection=None):
        super().__init__()
        super().discogs_connect(
            user_token=None,
            app_identifier=None,
            discogs=discogs,
        )
        self.collection = collection
        self.table = None
        self.rows = rows
        self.headers = headers
        self.left_column_headline = None
        self.middle_column_headline = None
        self.right_column_headline = None
        self.left_column_content = None
        self.middle_column_content = None
        self.right_column_content = None
        # Content that can be fetched from DB as well as from Discogs
        self.sales_price = None
        self.sales_listing_details = None
        # Content only available from Discogs
        self.marketplace_stats = None
        # Hardcoded column translations
        self.key_translation = {
            "d_sales_listing_id": "Listing ID",
            "d_sales_release_id": "Release ID",
            "d_sales_release_url": "Release URL",
            "d_sales_url": "Listing URL",
            "d_sales_condition": "Condition",
            "d_sales_sleeve_condition": "Sleeve Condition",
            "d_sales_price": "Price",
            "d_sales_comments": "Comments",
            "d_sales_allow_offers": "Allow Offers",
            "d_sales_status": "Status",
            "d_sales_comments_private": "Comments",
            "d_sales_counts_as": "Counts as",
            "d_sales_location": "Location Comments",
            "d_sales_weight": "Weight",
            "d_sales_posted": "Listed on",
        }

    def action_toggle_dark(self):
        self.dark = not self.dark

    def action_request_quit(self):
        self.exit()

    def action_list_sale(self):
        pass

    def action_draft_sale(self):
        pass

    def action_toggle_sold(self):
        """When shortcut is pressed, toggle field "sold" in DB."""
        rlog = self.query_one(RichLog)
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        current_state = self.table.get_cell(row_key, "sold")
        release_id = self.table.get_cell(row_key, "release_id")
        wanted_state = True if current_state is False else True
        self.collection.toggle_sold_state(release_id, wanted_state)
        rlog.write("Set {release_id} sold state {wanted_state} ")

    def action_edit_release(self):
        pass

    def action_edit_sale(self):
        pass

    def compose(self):
        # The main data widget
        self.table = DataTable()
        self.table.focus()
        for key, label in self.headers.items():
            self.table.add_column(label=label, key=key)
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        # Headline widgets
        self.left_column_headline = Label("[b]Listing Details[/b]")
        self.middle_column_headline = Label("[b]My Price & Marketplace Stats[/b]")
        self.right_column_headline = Label("[b]Log[/b]")
        # Content widgets
        self.left_column_content = Static("")
        self.middle_column_content = Static("")
        self.right_column_content = Static("")
        self.sales_price = Digits("0", id="sales-price")
        # Layout
        with Vertical():
            with Horizontal(id="upper-area"):
                with VerticalScroll():
                    yield self.table
            with Horizontal(id="lower-area"):
                with VerticalScroll(id="lower-left-column"):
                    yield self.left_column_headline
                    yield self.left_column_content
                with VerticalScroll(id="lower-middle-column"):
                    yield self.middle_column_headline
                    yield self.sales_price
                    yield self.middle_column_content
                with VerticalScroll(id="lower-right-column"):
                    yield self.right_column_headline
                    yield self.right_column_content
            with Horizontal(id="log-area"):
                with VerticalScroll():
                    yield RichLog()
            yield Footer()

    def on_mount(self):
        self.title = "DiscoDOS ls results"
        self.sub_title = "Use keystrokes to edit/sell/view details, ..."
        self._load_rows_into_table()

    def on_data_table_row_highlighted(self, event):
        """Get DB listing details and Marketplace stats for highlighted row."""
        row_key = event.row_key
        # Listing
        listing_id = self.table.get_cell(row_key, "forsale")
        listing = self.collection.get_sales_listing_details(listing_id)
        self.left_column_content.update(
            self._two_column_view(listing, translate_keys=self.key_translation)
        )
        self._sales_digits_update(listing)
        # Stats
        self.middle_column_content.update("Press enter to fetch Discogs stats!")

    def on_data_table_row_selected(self, event):
        """Fetch Discogs listing details and Marketplace stats for selected row."""
        rlog = self.query_one(RichLog)
        row_key = event.row_key
        # Listing - we fetch only when listing_id in DB
        listing_id = self.table.get_cell(row_key, "forsale")
        if listing_id:
            listing = self.fetch_sales_listing_details(listing_id)
            self.left_column_content.update(
                self._two_column_view(listing, translate_keys=self.key_translation)
            )
            self._sales_digits_update(listing)
        # Stats - we fetch always
        release_id = self.table.get_cell(row_key, "release_id")
        stats = self.fetch_marketplace_stats(release_id)
        self.middle_column_content.update(self._two_column_view(stats))
        rlog.write(
            f"Updated price, marketplace stats and details of listing {listing_id} "
            "with Discogs data."
        )

    # Helpers

    def _load_rows_into_table(self):
        table_widget = self.query_one(DataTable)
        if isinstance(self.rows[0], Row):
            for row in self.rows:
                table_widget.add_row(*row)
        else:
            for row_id, row in enumerate(self.rows):
                table_widget.add_row(*row.values(), key=row_id)

    def _two_column_view(self, details_dict, translate_keys=None):
        """A Rich-formatted view of keys and values.

        - by default simply capitalizes key names
        - optionally alters key names via a passed translaton table

        We use it for Marketplace stats and Marketplace listing details.
        """
        # Create a rich Table with two columns.
        table = rich_table(box=None)
        table.add_column("Field", style="cyan", justify="right")
        table.add_column("Value", style="white")
        # Display an empty table instead of nothing.
        if not details_dict:
            return table

        # Highlight/fix/replace some values first
        values_replaced = {}
        for key, value in details_dict.items():
            if key in ["d_sales_release_url", "d_sales_url"]:
                value = Markdown(f"[View in browser]({value})")
            if key == "d_sales_allow_offers":
                value =  "Yes" if value in [1, True] else "No"
            elif key == "status" and value == "Sold":
                value = f"[magenta]{value}[/magenta]"
            elif key == "d_sales_posted" and isinstance(value, datetime):
                value = datetime.strftime(value, "%Y-%m-%d")
            values_replaced[key] = value

        # Prettify column captions
        if translate_keys:
            final_details = {
               translate_keys.get(k, k): v for k, v in values_replaced.items()
            }
        else:  # Without a tranlation table, fall back to simply capitalizing
            final_details = {
               k.capitalize(): v for k, v in values_replaced.items()
            }

        # The final creation of the Rich table
        for key, value in final_details.items():
            if isinstance(value, Markdown):
                table.add_row(f"[bold]{key}[/bold]", value)
                continue
            # Format key bold and value normal font (or as we manipulated it above)
            table.add_row(f"[bold]{key}[/bold]", str(value))
        return table

    def _sales_digits_update(self, listing):
        """A Rich-formatted big digits view of the sales price.
        """
        # Display a 0 when not listed for sale.
        sales_price = 0
        if listing is not None:
            sales_price = listing.get("d_sales_price", 0)
        self.sales_price.update(str(sales_price))
