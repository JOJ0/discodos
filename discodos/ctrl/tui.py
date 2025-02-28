import logging
from sqlite3 import Row
from datetime import datetime
from textual.app import App
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Digits, Footer, Label, Static, RichLog, Button
from textual.coordinate import Coordinate
from textual.binding import Binding
from rich.markdown import Markdown

from discodos.model import DiscogsMixin
from discodos.ctrl.tui_edit import EditScreen
from discodos.ctrl.tui_folder import EditFolderScreen
from discodos.utils import timestamp_now, is_number

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
        ("p", "fetch_marketplace", "Fetch Marketplace stats"),
        ("r", "reimport_collection_item", "Reimport collection item"),
        ("f", "edit_folder", "Edit collection item folder"),
        Binding("escape", "back", "Back", tooltip="Cancel edits", show=True),
        Binding("s", "save_edit_folder", "Save", tooltip="Save edits", show=True),
    ]

    def __init__(
        self,
        rows,
        headers,
        sales_listing_headers,
        discogs,
        collection,
        cli,
        user,
    ):
        # DiscoDOS base functionalies received as args
        self.collection = collection
        self.cli = cli
        self.user = user
        super().discogs_connect(None, None, discogs=discogs)
        log.debug("TUI: ONLINE=%s in %s", self.ONLINE, __class__.__name__)

        # Textual initializations
        super().__init__()
        self.table = None
        self.rows = rows
        self.rlog = RichLog()
        # Global table headers and those for sales listing details (left column)
        # are passed on initialization
        self.headers = headers
        self.key_translation = sales_listing_headers

        # Keeping track of content
        self.right_column_current = None
        self.left_column_current = None
        self.middle_column_current = None
        # Content that can be fetched from DB as well as from Discogs
        self.sales_price = None
        self.sales_listing_details = None
        # Content only available from Discogs
        self.marketplace_stats = None

        # Headlines
        self.left_column_headline = None
        self.middle_column_headline = None
        self.right_column_headline = None

        # Content left
        self.left_column_content = None
        # Content middle
        self.middle_column_upper_content = None
        self.middle_column_content = None
        self.middle_column_lower_content = None
        # Content right
        self.right_column_upper_content = None
        self.right_column_content = None

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
        if not listing_id:
            self.rlog.write("Not listed for sale.")
            return
        release_id = self.table.get_cell(row_key, "discogs_id")
        listing = self.collection.get_sales_listing_details(listing_id)
        if not listing:
            self.rlog.write("Error getting sales listing from DiscoBASE.")
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
            listing["d_sales_release_id"] = release_id
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
                release_id=listing["d_sales_release_id"],
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

    def action_edit_folder(self):
        """Open the edit item folder screen."""
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        instance_id = self.table.get_cell(row_key, "d_coll_instance_id")
        release_id = self.table.get_cell(row_key, "discogs_id")
        folder_name = self.table.get_cell(row_key, "d_collfolder_name")
        folder_id = self.collection.get_folder_id_by_name(folder_name)
        folders = self.collection.get_collection_folders()
        if not instance_id:
            self.rlog.write("Not a collection item.")
            return

        def save_changes(instance_id, release_id, folder_id):
            timestamp = timestamp_now()
            is_sold = "No"
            if not self.collection.update_collection_item_folder(
                instance_id, release_id, folder_id
            ):
                self.rlog.write("Updating Discogs collection item folder failed.")
                self.pop_screen()
                return
            if not self.collection.set_collection_item_folder(
                instance_id, folder_id, self.user.conf.sold_folder_id, timestamp
            ):
                self.rlog.write("Updating DiscoBASE collection item folder failed.")
                self.pop_screen()
                return
            r_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
            folder_name = self.collection.get_folder_name_by_id(folder_id)
            if is_number(self.user.conf.sold_folder_id):
                is_sold = self.cli.bool_to_yes_no(
                    int(self.user.conf.sold_folder_id) == folder_id
                )
            self.table.update_cell(r_key, "d_collfolder_name", folder_name)
            self.table.update_cell(r_key, "coll_mtime", timestamp)
            self.table.update_cell(r_key, "sold", is_sold)
            self.rlog.write("Updated collection item folder.")
            self.pop_screen()
            return

        self.push_screen(
            EditFolderScreen(
                save_changes,
                instance_id=instance_id,
                release_id=release_id,
                folder_id=folder_id,
                folders=folders
            )
        )

    def action_save_edit_folder(self):
        try:
            self.query_one("#save_edit_folder").action_press()
        except Exception:
            pass

    def action_fetch_videos(self):
        """Fetches videos from Discogs release and displays in Rich column view."""
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        release_id = self.table.get_cell(row_key, "discogs_id")
        # Get videos ...
        videos, err_videos, _ = self.collection.fetch_release_videos(release_id)
        if err_videos:
            render_videos = err_videos
        else:
            self.right_column_current = videos
            title = "YouTube"
            render_videos = self.cli.two_column_view(videos, as_is=True, title=title)

        if err_videos:
            self.rlog.write(
                f"Fetching video links for {release_id} failed: {err_videos}."
            )
            return
        # ... log and display
        self.rlog.write(f"Fetched release {release_id} video links.")
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

    def action_reimport_collection_item(self):
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        release_id = self.table.get_cell(row_key, "discogs_id")
        instance_id = self.table.get_cell(row_key, "d_coll_instance_id")
        instances = self.collection.fetch_collection_item_instances(release_id)
        timestamp = timestamp_now()
        for instance in instances:
            if instance_id == instance["instance_id"]:
                folder = self.collection.get_folder_name_by_id(instance["folder_id"])
                notes = self.cli.extract_collection_item_notes(instance)
                if not self.collection.create_collection_item(
                    {
                        "d_coll_instance_id": instance["instance_id"],
                        "d_coll_release_id": instance["id"],
                        "d_coll_folder_id": instance["folder_id"],
                        "d_coll_added": instance["date_added"],
                        "d_coll_rating": instance["rating"],
                        "d_coll_notes": notes,
                        "coll_sold": instance["folder_id"] == int(self.user.conf.sold_folder_id),
                        "coll_orphaned": 0,
                        "coll_mtime": timestamp,
                    }
                ):
                    self.rlog.write(f"Nothing to reimport for {instance_id}.")
                    return
                self.table.update_cell(row_key, "d_collfolder_name", folder)
                self.table.update_cell(row_key, "d_coll_notes", notes)
                self.table.update_cell(row_key, "coll_mtime", timestamp)
                self.rlog.write(f"Reimport collection item {instance_id} done.")
                return
        self.rlog.write(f"Error fetching {instance_id} for reimport.")
        return

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
        self.right_column_content = Static("", classes="top-spacer")
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
        instance_id = self.table.get_cell(row_key, "d_coll_instance_id")
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
           "\nPress p to fetch Marketplace stats and suggested price!"
        )
        self.middle_column_lower_content.update("")
        # Update column right
        self.right_column_upper_content.update(
            self.cli.two_column_view(
                {
                    "Release": release_id,
                    "Collection Instance": instance_id,
                    "Release URL": self.cli.link_to("discogs release", release_id),
                },
                as_is=True,
            )
        )
        if self.right_column_current:
            # self.right_column_content.styles.text_style = "none"
            title = "YouTube (outdated, press v!)"
            render_videos = self.cli.two_column_view(
                self.right_column_current, as_is=True, title=title
            )
            self.right_column_content.update(render_videos)
            return
        self.right_column_content.update("Press v to fetch video links!")

    def action_fetch_marketplace(self):
        """Fetch Discogs listing details and Marketplace stats for selected row."""
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
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
            return
        self.middle_column_lower_content.update(
            f"Suggested VG+ price: {round(p.value, 1)}"
        )
        if s_err or not p:
            return
        self.rlog.write(
            f"Fetched release {release_id} Marketplace stats & suggested price."
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
