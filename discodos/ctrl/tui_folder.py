import logging
from textual.screen import Screen
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import RadioSet, Button, RadioButton

log = logging.getLogger('discodos')


class EditFolderScreen(Screen):
    """Change a collection item's folder in a separate screen."""
    CSS = """
    Horizontal {
        align: center middle;
    }
    VerticalScroll {
        width: auto;
    }
    RadioSet {
        width: auto;
    }
    """

    def __init__(
        self,
        on_save,
        instance_id,
        release_id,
        folder_id,
        folders,
    ):
        super().__init__()
        self.caption = instance_id
        self.release_id = release_id
        self.initial_folder = folder_id
        self.folders = folders
        self.on_save = on_save

    def compose(self):
        with Horizontal():
            with VerticalScroll():
                with RadioSet(id="folder_id"):
                    for folder in self.folders:
                        active = folder["d_collfolder_id"] == self.initial_folder
                        yield RadioButton(
                            folder["d_collfolder_name"],
                            value=active,
                            name=folder["d_collfolder_id"],
                        )
            with VerticalScroll():
                yield Button("Save", id="save_edit_folder")
                yield Button("Back", id="back")

    def on_mount(self):
        """Do when widgets are loaded"""
        self.query_one(RadioSet).focus()


    def on_button_pressed(self, event):
        if event.button.id == "save_edit_folder":
            folder_id = self.query_one("#folder_id").pressed_button.name
            # log.error(folder_id)
            self.on_save(
                instance_id=self.caption,
                release_id=self.release_id,
                folder_id=folder_id,
            )
            # pop_screen is happening within the callback method
        elif event.button.id == "back":
            self.app.pop_screen()  # Return to the main screen
