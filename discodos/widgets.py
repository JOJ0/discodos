import tkinter as tk
from tkinter import ttk
from discodos import log

class widget_frame():
    def __init__(self, parent, title):
        self.edit_win = tk.Toplevel(parent)
        self.edit_win.title(title)
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.edit_win.geometry("+%d+%d" % (x + 100, y + 100))
        


class edit_mix_view(widget_frame):
    def __init__(self, parent):
        self.title = "Edit Mix Info"
        super().__init__(parent, self.title)
        self.view_mix_content()


    def view_mix_content(self):

        self.mix_info_frame = tk.LabelFrame(self.edit_win, text="Mix Info")
        self.pool_frame = tk.LabelFrame(self.edit_win, text="Discogs Track Pool")

        #############################################
        # Mix Info edit
        #############################################

        # "name","played", "venue", "created", "updated"

        tk.Label(self.mix_info_frame, text="Name").pack(side="left")
        name_entry = tk.Entry(self.mix_info_frame)
        name_entry.pack(side="right")

        tk.Label(self.mix_info_frame, text="Played").pack(side="left")
        played_entry = tk.Entry(self.mix_info_frame)
        played_entry.pack(side="right")

        tk.Label(self.mix_info_frame, text="Venue").pack(side="left")
        venue_entry = tk.Entry(self.mix_info_frame)
        venue_entry.pack(side="right")

        tk.Label(self.mix_info_frame, text="Created").pack(side="left")
        created_entry = tk.Entry(self.mix_info_frame)
        created_entry.pack(side="right")

        tk.Label(self.mix_info_frame, text="Updated").pack(side="left")
        updated_entry = tk.Entry(self.mix_info_frame)
        updated_entry.pack(side="right")


        #############################################
        # Track Pool
        #############################################

        self.tracks_list = ttk.Treeview(self.pool_frame)
        self.tracks_list.pack(fill="both", expand=1)

        self.tracks_list["columns"]=("artist", "track", "trackpos", "key", "bpm", "keynotes")
        self.tracks_list.column("#0", width=20,  minwidth=10)
        self.tracks_list.column("artist", width=20, minwidth=10)
        self.tracks_list.column("track", width=20,  minwidth=10)
        self.tracks_list.column("trackpos", width=10, minwidth=10)
        self.tracks_list.column("key", width=8, minwidth=8)
        self.tracks_list.column("bpm", width=8, minwidth=8)

        self.tracks_list.heading("#0",text="Release",anchor=tk.W)
        self.tracks_list.heading("artist", text="Artist", anchor=tk.W)
        self.tracks_list.heading("track", text="Track Name",anchor=tk.W)
        self.tracks_list.heading("trackpos", text="Track Pos",anchor=tk.W)
        self.tracks_list.heading("key", text="Key",anchor=tk.W)
        self.tracks_list.heading("bpm", text="BPM",anchor=tk.W)


        ###############################################

        # Display Frames

        self.mix_info_frame.pack(fill="both", expand=1, side = "top")
        self.pool_frame.pack(fill="both", expand=1, side = "bottom")


class edit_track_info(widget_frame):

    def __init__(self, parent):
        self.title = "Edit Track Info"
        super().__init__(parent, self.title)
        self.view_track_content()


    def view_track_content(self):
        pass




