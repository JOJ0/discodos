import logging
from sqlite3 import Row
from datetime import datetime
from textual.app import App
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Digits, Footer, Label, Static, RichLog
from textual.coordinate import Coordinate
from rich.markdown import Markdown

from discodos.model import DiscogsMixin
from discodos.ctrl.tui_edit import EditScreen

log = logging.getLogger('discodos')


class DiscodosListApp(App, DiscogsMixin):  # pylint: disable=too-many-instance-attributes
    """Inline Textual app to view and edit dsc ls results."""
    CSS_PATH = "tui_ls.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("e", "edit_sales_listing", "Edit sales listing"),
        ("v", "fetch_videos", "Fetch videos"),
        ("l", "fetch_listing_details", "Fetch listing details"),
    ]

    def __init__(
        self,
        rows,
        headers,
        sales_listing_headers,
        discogs,
        collection,
        cli,
    ):
        super().__init__()
        super().discogs_connect(
            user_token=None,
            app_identifier=None,
            discogs=discogs,
        )
        self.collection = collection
        self.cli = cli
        self.table = None
        self.rows = rows
        self.headers = headers
        self.rlog = RichLog()
        # Columns content
        self.left_column_headline = None
        self.middle_column_headline = None
        self.right_column_headline = None
        self.left_column_content = None
        self.middle_column_upper_content = None
        self.middle_column_content = None
        self.middle_column_lower_content = None
        self.right_column_upper_content = None
        self.right_column_content = None
        # Content that can be fetched from DB as well as from Discogs
        self.sales_price = None
        self.sales_listing_details = None
        # Content only available from Discogs
        self.marketplace_stats = None
        # Hardcoded column translations
        self.key_translation = sales_listing_headers

    def action_toggle_dark(self):
        self.dark = not self.dark

    def action_request_quit(self):
        self.exit()

    def action_toggle_sold(self):
        """When shortcut is pressed, toggle field "sold" in DB."""
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        release_id = self.table.get_cell(row_key, "discogs_id")
        instance_id = self.table.get_cell(row_key, "d_coll_instance_id")
        # Current and wanted states toggle
        current_state = self.table.get_cell(row_key, "sold")
        wanted_state = "No" if current_state == "Yes" else "Yes"
        # DB write
        toggled, _ = self.collection.toggle_sold_state(
            release_id, self.cli.yes_no_to_bool(wanted_state), instance_id
        )
        # Update the cell on success and log
        if toggled:
            self.rlog.write(
                f"Set collection item instance {instance_id} sold state {wanted_state} "
            )
            self.table.update_cell(row_key, "sold", wanted_state)
            return
        self.rlog.write(f"Error setting {release_id} sold state {wanted_state} ")

    def action_edit_sales_listing(self):
        """Open the edit screen for a sales listing."""
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        listing_id = self.table.get_cell(row_key, "d_sales_listing_id")
        listing, l_err, _ = self.fetch_sales_listing_details(listing_id, tui_view=True)
        if l_err:
            self.rlog.write(f"Error fetching sales listing details: {l_err}")
            return

        def save_changes(**kwargs):
            if not self.collection.update_sales_listing(
                listing_id=listing_id, **kwargs
            ):
                self.rlog.write("Updating Discogs Marketplace listing failed.")
                return
            self.rlog.write("Updated Discogs Marketplace listing.")

            listing, l_err, _ = self.fetch_sales_listing_details(listing_id, tui_view=True)
            if l_err:
                self.rlog.write("Error fetching sales listing details:", l_err)
                return

            listing["d_sales_listing_id"] = listing_id
            created = self.collection.create_sales_entry(listing)
            if not created:
                self.rlog.write("Updating sales entry in DiscoBASE failed")
                return

            self.rlog.write("Updated sales entry in DiscoBASE")

            # Update the table's cells and panels
            r_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
            self.table.update_cell(r_key, "d_sales_status", kwargs["status"])
            self.table.update_cell(r_key, "d_sales_location", kwargs["location"])
            self.table.update_cell(r_key, "d_sales_price", kwargs["price"])
            self.rlog.write(f"Updated columns in table row {r_key}.")
            self._sales_digits_update(listing)
            self.rlog.write("Updated sales price panel.")
            listing = self.collection.get_sales_listing_details(listing_id)
            self.left_column_content.update(
                self.cli.two_column_view(listing, translate_keys=self.key_translation)
            )
            self.rlog.write("Updated sales listing details panel.")

            self.pop_screen()  # Return to the main screen

        # Show the EditScreen
        self.push_screen(
            EditScreen(
                save_changes,
                listing_id=listing_id,
                price=listing["d_sales_price"],
                condition=listing["d_sales_condition"],
                sleeve_condition=listing["d_sales_sleeve_condition"],
                location=listing["d_sales_location"],
                status=listing["d_sales_status"],
                allow_offers=listing["d_sales_allow_offers"],
                comments=listing["d_sales_comments"],
                comments_private=listing["d_sales_comments_private"],
            )
        )

    def action_fetch_videos(self):
        """Fetches videos from Discogs release and displays in Rich column view."""
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        release_id = self.table.get_cell(row_key, "discogs_id")
        # Get videos ...
        videos, err_videos, _ = self.collection.fetch_release_videos(release_id)
        render_videos = (
            err_videos if err_videos else self.cli.two_column_view(videos, as_is=True)
        )
        # ... log and display
        self.rlog.write(f"Fetched release {release_id} YouTube video links.")
        self.right_column_content.update(render_videos)

    def action_fetch_listing_details(self):
        """Updates the listing details shown in left column.
        
        FIXME implement updating in DiscoBASE in here.
        """
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        listing_id = self.table.get_cell(row_key, "d_sales_listing_id")
        listing, l_err, _ = self.fetch_sales_listing_details(listing_id, tui_view=True)
        if l_err:
            self.rlog.write(f"Can't fetch listing details: {l_err}")
            return
        if listing:
            self.left_column_content.update(
                self.cli.two_column_view(listing, translate_keys=self.key_translation)
            )
            self._sales_digits_update(listing)
        self.rlog.write(
            f"Updated price and details of listing {listing_id} "
            "with Discogs data."
        )

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
        self.right_column_headline = Label("[b]Release Details & YouTube Listen[/b]")
        # Content widgets
        self.left_column_content = Static("")
        self.middle_column_upper_content = Static("Currently for sale:")
        self.middle_column_content = Static("")
        self.middle_column_lower_content = Static("")
        self.right_column_upper_content = Static("")
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
                    yield self.middle_column_upper_content
                    yield self.middle_column_content
                    yield self.middle_column_lower_content
                with VerticalScroll(id="lower-right-column"):
                    yield self.right_column_headline
                    yield self.right_column_upper_content
                    yield self.right_column_content
            with Horizontal(id="log-area"):
                with VerticalScroll():
                    yield self.rlog
            yield Footer()

    def on_mount(self):
        self.title = "DiscoDOS ls results"
        self.sub_title = "Use keystrokes to edit/sell/view details, ..."
        self._load_rows_into_table()

    def on_data_table_row_highlighted(self, event):
        """Get DB listing details and Marketplace stats for highlighted row."""
        row_key = event.row_key
        # Get ID's from table
        listing_id = self.table.get_cell(row_key, "d_sales_listing_id")
        release_id = self.table.get_cell(row_key, "discogs_id")
        listing = self.collection.get_sales_listing_details(listing_id, tui_view=True)
        # Update column left
        self.left_column_content.update(
            self.cli.two_column_view(listing, translate_keys=self.key_translation)
        )
        self._sales_digits_update(listing)

        # Update column middle - Currently for sale link
        for_sale_link = self.cli.link_to("discogs for sale", release_id, md=True)
        md_link = Markdown(f"Currently for sale: {for_sale_link}")
        self.middle_column_upper_content.update(md_link)
        # Update column middle - Reset stats
        self.middle_column_content.update(
           "\nPress enter to fetch Marketplace stats and suggested price!"
        )
        self.middle_column_lower_content.update("")
        # Update column right
        self.right_column_upper_content.update(
            self.cli.two_column_view(
                {
                    "Release": release_id,
                    "Release URL": self.cli.link_to("discogs release", release_id),
                },
                as_is=True,
            )
        )

    def on_data_table_row_selected(self, event):
        """Fetch Discogs listing details and Marketplace stats for selected row."""
        row_key = event.row_key
        release_id = self.table.get_cell(row_key, "discogs_id")
        # Stats
        stats, s_err, _ = self.fetch_marketplace_stats(release_id)
        if s_err:
            self.rlog.write(f"Fetching Marketplace stats: {s_err}")
        self.middle_column_content.update(self.cli.two_column_view(stats))
        # Price suggestion
        p = self.fetch_price_suggestion(release_id, "VG+")
        if not p:
            self.rlog.write("Fetching price suggestion failed.")
        self.middle_column_lower_content.update(
            f"Suggested VG+ price: {round(p.value, 1)}"
        )
        if s_err or not p:
            return
        self.rlog.write(
            f"Updated price, Marketplace stats and details of release {release_id} "
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

    def _sales_digits_update(self, listing):
        """A Rich-formatted big digits view of the sales price.
        """
        # Display a 0 when not listed for sale.
        sales_price = 0
        if listing is not None:
            sales_price = listing.get("d_sales_price", 0)
        self.sales_price.update(str(sales_price))
