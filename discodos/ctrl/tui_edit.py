from textual.screen import Screen
from textual.containers import Vertical, Horizontal, VerticalScroll, HorizontalScroll
from textual.widgets import Input, RadioSet, Button, Label, Static, RadioButton

CONDITIONS = {
    "M": "Mint",
    "NM": "Near Mint",
    "VG+": "Very Good Plus",
    "VG": "Very Good",
    "G+": "Good Plus",
    "G": "Good",
    "F": "Fair",
}

STATUS_OPTIONS = {
    "draft": "Draft",
    "forsale": "For Sale",
    "expired": "Expired",
}


class EditScreen(Screen):
    """Edit a table entry in a separate screen."""

    def __init__(
        self,
        location=None,
        price=None,
        condition=None,
        sleeve_condition=None,
        status=None,
    ):
        super().__init__()

        # Initialize the input fields with provided or default values
        self.location = Input(value=location or "", placeholder="Location")
        self.price = Input(value=price or "", placeholder="Price")

        # Store the initial values for condition, sleeve_condition, and status
        self.initial_condition = condition
        self.initial_sleeve_condition = sleeve_condition
        self.initial_status = status

        # Info panel
        self.info_panel = Static("")

    def compose(self):
        with VerticalScroll():  # Make the entire form scrollable vertically
            yield Button("Back", id="back")  # Add Back button at the top
            yield Label("Location")
            yield self.location
            yield Label("Price")
            yield self.price

            # HorizontalScroll for RadioSets, placed next to each other
            with HorizontalScroll():
                # Condition RadioSet
                with Vertical():
                    yield Label("Condition")
                    with RadioSet():
                        for key, label in CONDITIONS.items():
                            yield RadioButton(label, value=key)

                # Sleeve Condition RadioSet
                with Vertical():
                    yield Label("Sleeve Condition")
                    with RadioSet():
                        for key, label in CONDITIONS.items():
                            yield RadioButton(label, value=key)

                # Status RadioSet
                with Vertical():
                    yield Label("Status")
                    with RadioSet():
                        for key, label in STATUS_OPTIONS.items():
                            yield RadioButton(label, value=key)

            yield Button("Save", id="save")
            yield self.info_panel

    def on_mount(self) -> None:
        # Set the initial selected values for each radio button set
        condition_radio_set = self.query_one(RadioSet)
        condition_radio_set.selected_value = self.initial_condition

        sleeve_condition_radio_set = self.query_one(RadioSet)
        sleeve_condition_radio_set.selected_value = self.initial_sleeve_condition

        status_radio_set = self.query_one(RadioSet)
        status_radio_set.selected_value = self.initial_status

    def on_button_pressed(self, event):
        if event.button.id == "save":
            # Collect the values from the form inputs
            location = self.location.value
            price = self.price.value
            condition = self.query_one(RadioSet).selected_value
            sleeve_condition = self.query_one(RadioSet).selected_value
            status = self.query_one(RadioSet).selected_value
        elif event.button.id == "back":
            self.app.pop_screen()  # Return to the main screen

            # Process saving the changes here (DB/API logic can be added)
            # print(f"Saved: Location={location}, Price={price}, Condition={condition}, "
            #       f"Sleeve Condition={sleeve_condition}, Status={status}")

            # Update the info panel after saving
            self.info_panel.update(f"Saved successfully!")

