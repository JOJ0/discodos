from textual.screen import Screen
from textual.containers import Vertical, Horizontal, VerticalScroll, HorizontalScroll
from textual.widgets import Input, RadioSet, Button, Label, Static, RadioButton, RichLog

from discodos.utils import (
    RECORD_CHOICES_RADIO,
    SLEEVE_CHOICES_RADIO,
    STATUS_CHOICES_RADIO,
    YES_NO_CHOICES_RADIO,
)


class EditScreen(Screen):
    """Edit a table entry in a separate screen."""

    def __init__(
        self,
        on_save,
        listing_id,
        release_id,
        price,
        condition,
        sleeve_condition,
        location,
        status,
        allow_offers,
        comments,
        comments_private,
    ):
        super().__init__()
        self.caption = listing_id
        self.release_id = release_id  # required for saving
        # Initialize text based fields with existing or default values
        self.price = Input(str(price))
        self.location = Input(value=location or "", placeholder="Location")
        self.comments = Input(value=comments or "", placeholder="Public comments")
        self.comments_private = Input(value=comments_private or "",
                                      placeholder="Private comments")
        # Store the initial values for choices based fields
        self.initial_condition = condition
        self.initial_sleeve_condition = sleeve_condition
        self.initial_status = status
        self.initial_allow_offers = allow_offers
        # Info / Log Panel
        self.log_panel = RichLog()
        self.on_save = on_save  # Callback to save changes

    def compose(self):
        with Horizontal():  # Contains one big column
            with VerticalScroll():
                yield Label("Price")
                yield self.price
                yield Label("Location")
                yield self.location
        with Horizontal():  # Contains 4 columns
            with VerticalScroll():
                yield Label("Condition")
                with RadioSet(id="condition"):
                    for key, label in RECORD_CHOICES_RADIO.items():
                        active = key == self.initial_condition
                        yield RadioButton(label, value=active, name=key)
            with VerticalScroll():
                yield Label("Sleeve Condition")
                with RadioSet(id="sleeve_condition"):
                    for key, label in SLEEVE_CHOICES_RADIO.items():
                        active = key == self.initial_sleeve_condition
                        yield RadioButton(label, value=active, name=key)
            with VerticalScroll():
                yield Label("Status")
                with RadioSet(id="status"):
                    for key, label in STATUS_CHOICES_RADIO.items():
                        active = key == self.initial_status
                        yield RadioButton(label, value=active, name=key)
                yield Label("Allow offers")
                with RadioSet(id="allow_offers"):
                    for key, label in YES_NO_CHOICES_RADIO.items():
                        active = key == self.initial_allow_offers
                        yield RadioButton(label, value=active, name=key)
            with VerticalScroll():
                yield Label("Public comments")
                yield self.comments
                yield Label("Private comments")
                yield self.comments_private
        with Horizontal():
            yield Button("Save", id="save")  # is in top vertical widget
            yield Button("Back", id="back")  # Add Back button at the top

    def on_button_pressed(self, event):
        if event.button.id == "save":
            condition = self.query_one("#condition")
            sleeve_condition = self.query_one("#sleeve_condition")
            status = self.query_one("#status")
            allow_offers = self.query_one("#allow_offers")
            self.on_save(
                release_id=self.release_id,
                price=self.price.value,
                condition=condition.pressed_button.name,
                sleeve_condition=sleeve_condition.pressed_button.name,
                location=self.location.value,
                status=status.pressed_button.name,
                allow_offers=allow_offers.pressed_button.name,
                comments=self.comments.value,
                comments_private=self.comments_private.value,
            )
            # pop_screen is happening within the callback method
        elif event.button.id == "back":
            self.app.pop_screen()  # Return to the main screen
