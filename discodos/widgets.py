import tkinter as tk
from tkinter import ttk
from discodos import log

class widget_frame():
    def __init__(self, parent, title):
        self.edit_win = tk.Toplevel(parent)

        self.edit_win.geometry("350x600")               
        self.edit_win.resizable(False, False) 

        self.edit_win.title(title)
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.edit_win.geometry("+%d+%d" % (x + 800, y))

    def _quit(self):
        self.edit_win.quit()
        self.edit_win.destroy()
        exit() 
        


class edit_mix_view(widget_frame):
    def __init__(self, parent, mix_data):
        self.title = "Edit Mix Info"
        super().__init__(parent, self.title)
        self.mix_data = mix_data
        self.view_mix_content()
        

        # log.debug(mix_data["venue"])


    def view_mix_content(self):

        self.mix_info_frame = tk.LabelFrame(self.edit_win, text="Mix Info")
        self.pool_frame = tk.LabelFrame(self.edit_win, text="Discogs Track Pool")
        self.buttons_frame = tk.Frame(self.edit_win)

        #############################################
        # Mix Info edit
        #############################################


        tk.Label(self.mix_info_frame, text="Name").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(self.mix_info_frame)
        self.name_entry.grid(row=0, column=1, sticky="w")
        try:
            self.name_entry.insert(0, self.mix_data["name"])
        except:
            log.error("Couldn't insert Data")

        tk.Label(self.mix_info_frame, text="Played").grid(row=1, column=0, sticky="w")
        self.played_entry = tk.Entry(self.mix_info_frame)
        self.played_entry.grid(row=1, column=1, sticky="w")
        self.played_entry.insert(0, self.mix_data["played"])

        tk.Label(self.mix_info_frame, text="Venue").grid(row=2, column=0, sticky="w")
        self.venue_entry = tk.Entry(self.mix_info_frame)
        self.venue_entry.grid(row=2, column=1, sticky="w")
        self.venue_entry.insert(0, self.mix_data["venue"])

        tk.Label(self.mix_info_frame, text="Created").grid(row=3, column=0, sticky="w")
        tk.Label(self.mix_info_frame, text=self.mix_data["created"]).grid(row=3, column=1, sticky="w")

        tk.Label(self.mix_info_frame, text="Last Updated").grid(row=4, column=0, sticky="w")
        tk.Label(self.mix_info_frame, text=self.mix_data["updated"]).grid(row=4, column=1, sticky="w")


        #############################################
        # Track Pool
        #############################################

        self.tracks_list = ttk.Treeview(self.pool_frame)
        self.tracks_list.pack(fill="both", expand=1)

        self.tracks_list["columns"]=("artist", "track", "trackpos", "key", "bpm")
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

        # Buttons Area

        tk.Button(self.buttons_frame, text="Save").pack(side="left")
        tk.Button(self.buttons_frame, text="Add Track to Mix").pack(side="right")

        # Display Frames

        self.mix_info_frame.pack(fill="both", expand=1, side = "top")
        self.buttons_frame.pack(side="bottom")
        self.pool_frame.pack(fill="both", expand=1, side = "bottom")
        

        



class edit_track_info(widget_frame):

    def __init__(self, parent):
        self.title = "Edit Track Info"
        super().__init__(parent, self.title)
        self.view_track_content()


    def view_track_content(self):
        pass




