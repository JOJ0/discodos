import logging
from rich.table import Table as rich_table
from textual.app import App
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Digits, Footer, Label, Static

from discodos.model import DiscogsMixin

log = logging.getLogger('discodos')


class DiscodosListApp(App, DiscogsMixin):
    """Inline Textual app to view and edit dsc ls results."""
    CSS_PATH = "tui_ls.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("l", "list_sale", "List for sale"),
        ("d", "draft_sale", "Set to draft"),
        ("e", "edit_release", "Edit release"),
        ("E", "edit_sale", "Edit sales listing"),
    ]

    def __init__(self, rows, headers, discogs=None):
        super().__init__()
        super().discogs_connect(
            user_token=None,
            app_identifier=None,
            discogs=discogs,
        )
        self.table = None
        self.rows = rows
        self.headers = headers
        self.left_column_headline = None
        self.middle_column_headline = None
        self.right_column_headline = None
        self.left_column_content = None
        self.middle_column_content = None
        self.right_column_content = None
        self.sales_price = None

    def action_toggle_dark(self):
        self.dark = not self.dark

    def action_request_quit(self):
        self.exit()

    def action_list_sale(self):
        pass

    def action_draft_sale(self):
        pass

    def action_edit_release(self):
        pass

    def action_edit_sale(self):
        pass

    def _load_ls_results(self):
        table_widget = self.query_one(DataTable)
        for row_id, row in enumerate(self.rows):
            #row_id = row['discogs_id']
            table_widget.add_row(*row.values(), key=row_id)

    def on_mount(self):
        self.title = "DiscoDOS ls results"
        self.sub_title = "Use keystrokes to edit/sell/view details, ..."
        self._load_ls_results()

    def _two_column_rich_table(self, listing_details):
        # Create a rich Table
        table = rich_table(box=None)
        # Add columns for the table
        table.add_column("Field", style="cyan", justify="right")
        table.add_column("Value", style="white")
        if not listing_details:
            return table
        # Add rows with capitalized keys and their corresponding values
        for key, value in listing_details.items():
            if key == "status":
                if value == "Sold":
                    table.add_row(
                        f"[bold]{key.capitalize()}[/bold]",
                        f"[magenta]{value}[/magenta]"
                    )
                    continue
            table.add_row(f"[bold]{key.capitalize()}[/bold]", str(value))
        return table

    def on_data_table_cell_selected(self, event):
        log.debug(event.coordinate)
        if event.coordinate.column == 5 and event.value is not None:
            listing = self.get_sales_listing_details(event.value)
            self.left_column_content.update(self._two_column_rich_table(listing))
            self.sales_price.update(listing['price'])
        if event.coordinate.column == 0 and event.value is not None:
            stats = self.get_marketplace_stats(event.value)
            self.middle_column_content.update(self._two_column_rich_table(stats))

    def compose(self):
        # The main data widget
        self.table = DataTable()
        self.table.focus()
        self.table.add_columns(*self.headers)
        self.table.cursor_type = "cell"
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
            yield Footer()