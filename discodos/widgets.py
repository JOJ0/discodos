import tkinter as tk
from tkinter import ttk
from discodos import log
from discodos import models

class widget_frame():
    def __init__(self, parent, title):
        self.edit_win = tk.Toplevel(parent)
        # log.debug("Window State is " + self.edit_win.state())
        global win_state 
        self.win_state = self.edit_win.state()

        self.edit_win.geometry("350x600")               
        self.edit_win.resizable(False, False) 
        self.parent = parent

        self.edit_win.title(title)
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.edit_win.geometry("+%d+%d" % (x + 800, y))

    def _quit(self):
        self.edit_win.destroy()
        
############ EDIT MIX ###########################

class edit_mix_view(widget_frame):
    def __init__(self, parent, mix):
        self.title = "Edit Mix"
        super().__init__(parent, self.title)
        self.parent = parent
        self.mix = mix

        try:
            self.mix_data = mix.get_mix_info() 
            log.debug("GUI: Got Mix data for widget Window") 

        except:
            log.error("GUI: Couldn't get mix data for Widget Window")

        try:
            self.view_mix_content()
            log.debug("GUI: Loaded Mix Edit Content")
        except:
            log.error("GUI: Mix Edit Content failed loading.")

        # self.insert_track_pool()
        

        # log.debug(mix_data["venue"])


    def view_mix_content(self):

        self.mix_info_frame = tk.LabelFrame(self.edit_win, text="Mix Info")
        self.pool_frame = tk.LabelFrame(self.edit_win, text="Discogs Track Pool")
        self.buttons_frame = tk.Frame(self.edit_win)

        #############################################
        # Mix Info edit
        #############################################


        tk.Label(self.mix_info_frame, text="Name").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(self.mix_info_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky="w")
        try:
            self.name_entry.insert(0, self.mix_data["name"])
        except:
            log.error("Couldn't insert Data")

        tk.Label(self.mix_info_frame, text="Played").grid(row=1, column=0, sticky="w")
        self.played_entry = tk.Entry(self.mix_info_frame, width=30)
        self.played_entry.grid(row=1, column=1, sticky="w")
        self.played_entry.insert(0, self.mix_data["played"])

        tk.Label(self.mix_info_frame, text="Venue").grid(row=2, column=0, sticky="w")
        self.venue_entry = tk.Entry(self.mix_info_frame, width=30)
        self.venue_entry.grid(row=2, column=1, sticky="w")
        self.venue_entry.insert(0, self.mix_data["venue"])

        tk.Label(self.mix_info_frame, text="Created").grid(row=3, column=0, sticky="w")
        tk.Label(self.mix_info_frame, text=self.mix_data["created"]).grid(row=3, column=1, sticky="w")

        tk.Label(self.mix_info_frame, text="Last Updated").grid(row=4, column=0, sticky="w")
        tk.Label(self.mix_info_frame, text=self.mix_data["updated"]).grid(row=4, column=1, sticky="w")

        for i in range(5,9):
            self.mix_info_frame.rowconfigure(i, weight=1)

        self.update_mix_btn = tk.Button(self.mix_info_frame, text="Update Mix", command=update_mix)
        self.update_mix_btn.grid(row=8, column=0, sticky="s")
        self.quit_btn = tk.Button(self.mix_info_frame, text="Cancel", command=self._quit)
        self.quit_btn.grid(row=8, column=1, sticky="s")


        #############################################
        # Track Pool
        #############################################

        self.coll_list = ttk.Treeview(self.pool_frame)
        self.coll_list.pack(fill="both", expand=1)

        self.coll_list["columns"]=("artist", "id")
        self.coll_list.column("#0", width=25,  minwidth=10)
        self.coll_list.column("artist", width=30, minwidth=10)
        self.coll_list.column("id", width=5,  minwidth=3)

        self.coll_list.heading("#0",text="Release",anchor=tk.W)
        self.coll_list.heading("artist", text="Artist", anchor=tk.W)
        self.coll_list.heading("id", text="Discogs ID",anchor=tk.W)

    
    def update_mix(self):
        pass



        ###############################################

        # Buttons Area

        tk.Button(self.buttons_frame, text="<- Add Track to Mix").pack(side="left")
        tk.Button(self.buttons_frame, text="Save Mix", command=update_mix).pack(side="right")

        # Display Frames

        self.mix_info_frame.pack(fill="both", expand=1, side = "top")
        self.buttons_frame.pack(side="bottom", fill="x")
        self.pool_frame.pack(fill="both", expand=1, side = "bottom")

    
    def insert_track_pool(self):
        self.collection = models.Collection(self.conn)
        try:
            self.all_releases = self.collection.get_all_db_releases()
            log.debug("GUI: Got all releases from Collection Model")
        except:
            log.error("GUI: Couldn't get all releases from Collection Model")

        # TODO
        # View only Values, only Headings, "text" should be empty
        
        for i, row in enumerate(self.all_releases):
            self.coll_list.insert("" , i, text=row["discogs_title"], 
                                        values=(row["d_artist"], 
                                                row["discogs_id"]))



    def add_track_to_mix(self):

        pass


####### CREATE NEW MIX #############################

class add_mix_view(widget_frame):
    def __init__(self, parent, conn):
        self.title = "Add Mix"
        super().__init__(parent, self.title)
        self.view_mix_content()
        self.conn = conn
        self.insert_track_pool()
        
    
    def view_mix_content(self):

        self.mix_info_frame = tk.LabelFrame(self.edit_win, text="Mix Info")
        self.pool_frame = tk.LabelFrame(self.edit_win, text="Discogs Track Pool")
        self.buttons_frame = tk.Frame(self.edit_win)

        #############################################
        # Mix Info View
        #############################################


        tk.Label(self.mix_info_frame, text="Name").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(self.mix_info_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky="w")


        tk.Label(self.mix_info_frame, text="Played").grid(row=1, column=0, sticky="w")
        self.played_entry = tk.Entry(self.mix_info_frame, width=30)
        self.played_entry.grid(row=1, column=1, sticky="w")

        tk.Label(self.mix_info_frame, text="Venue").grid(row=2, column=0, sticky="w")
        self.venue_entry = tk.Entry(self.mix_info_frame, width=30)
        self.venue_entry.grid(row=2, column=1, sticky="w")

        tk.Label(self.mix_info_frame, text="Created").grid(row=3, column=0, sticky="w")
        tk.Label(self.mix_info_frame, text="NOW??").grid(row=3, column=1, sticky="w")

        tk.Label(self.mix_info_frame, text="Last Updated").grid(row=4, column=0, sticky="w")
        tk.Label(self.mix_info_frame, text="").grid(row=4, column=1, sticky="w")

        for i in range(5,9):
            self.mix_info_frame.rowconfigure(i, weight=1)

        self.update_collection_btn = tk.Button(self.mix_info_frame, text="Save new Mix", command=self.create_mix)
        self.update_collection_btn.grid(row=8, column=0, sticky="s")
        self.quit_btn = tk.Button(self.mix_info_frame, text="Cancel", command=self._quit)
        self.quit_btn.grid(row=8, column=1, sticky="s")


       #############################################
        # Track Pool
        #############################################

        self.coll_list = ttk.Treeview(self.pool_frame)
        self.coll_list.pack(fill="both", expand=1)

        self.coll_list["columns"]=("artist", "id")
        self.coll_list.column("#0", width=25,  minwidth=10)
        self.coll_list.column("artist", width=30, minwidth=10)
        self.coll_list.column("id", width=5,  minwidth=3)

        self.coll_list.heading("#0",text="Release",anchor=tk.W)
        self.coll_list.heading("artist", text="Artist", anchor=tk.W)
        self.coll_list.heading("id", text="Discogs ID",anchor=tk.W)


        # Display Frames

        self.mix_info_frame.pack(fill="both", expand=1, side = "top")
        self.buttons_frame.pack(side="bottom", fill="x")
        self.pool_frame.pack(fill="both", expand=1, side = "bottom")


    def insert_track_pool(self):
        self.collection = models.Collection(self.conn)
        try:
            self.all_releases = self.collection.get_all_db_releases()
            log.debug("GUI: Got all releases from Collection Model")
        except:
            log.error("GUI: Couldn't get all releases from Collection Model")
        
        for i, row in enumerate(self.all_releases):
            self.coll_list.insert("" , i, text=row["discogs_title"], values=(row["d_artist"], row["discogs_id"]))


    def create_mix(self):
        self.mix = models.Mix(self.conn, "all")
        self.mix.create(self.played_entry.get(), self.venue_entry.get(), self.name_entry.get())
        self._quit()
        

#################### EDIT TRACK INFOS ######################

class edit_track_info(widget_frame):

    def __init__(self, parent, track_data, mix):
        self.title = "Edit Track Info"
        super().__init__(parent, self.title)
        self.track_data = track_data
        self.view_track_content()
        self.mix = mix



    def view_track_content(self):
        self.track_info_frame = tk.LabelFrame(self.edit_win, text="Track Info")
        self.buttons_frame = tk.Frame(self.edit_win)

        #############################################
        # Track edit
        #############################################

        tk.Label(self.track_info_frame, text="Track Position").grid(row=0, column=0, sticky="w")
        tk.Label(self.track_info_frame, text=self.track_data["values"][0]).grid(row=0, column=1, sticky="w")

        tk.Label(self.track_info_frame, text="Artist").grid(row=1, column=0, sticky="w")
        tk.Label(self.track_info_frame, text=self.track_data["values"][1]).grid(row=1, column=1, sticky="w")

        tk.Label(self.track_info_frame, text="Title").grid(row=2, column=0, sticky="w")
        tk.Label(self.track_info_frame, text=self.track_data["values"][2]).grid(row=2, column=1, sticky="w")

        tk.Label(self.track_info_frame, text="Key").grid(row=3, column=0, sticky="w")
        self.key_entry = tk.Entry(self.track_info_frame, width=30)
        self.key_entry.grid(row=3, column=1, sticky="w")
        try:
            self.key_entry.insert(0, self.track_data["values"][3])
        except:
            log.error("Couldn't insert Key Data")

        tk.Label(self.track_info_frame, text="BPM").grid(row=4, column=0, sticky="w")
        self.bpm_entry = tk.Entry(self.track_info_frame, width=30)
        self.bpm_entry.grid(row=4, column=1, sticky="w")
        try:
            self.bpm_entry.insert(0, self.track_data["values"][4])
        except:
            log.error("Couldn't insert Bpm Data")
        
        tk.Label(self.track_info_frame, text="Key Notes").grid(row=5, column=0, sticky="w")
        self.keynotes_entry = tk.Entry(self.track_info_frame, width=30)
        self.keynotes_entry.grid(row=5, column=1, sticky="w")
        try:
            self.keynotes_entry.insert(0, self.track_data["values"][5])
        except:
            log.error("Couldn't insert Key Notes Data")
        
        tk.Label(self.track_info_frame, text="Trans Rating").grid(row=6, column=0, sticky="w")
        self.transr_entry = tk.Entry(self.track_info_frame, width=30)
        self.transr_entry.grid(row=6, column=1, sticky="w")
        try:
            self.transr_entry.insert(0, self.track_data["values"][6])
        except:
            log.error("Couldn't insert Trans Rating Data")
        
        tk.Label(self.track_info_frame, text="Trans Notes").grid(row=7, column=0, sticky="w")
        self.transnotes_entry = tk.Entry(self.track_info_frame, width=30)
        self.transnotes_entry.grid(row=7, column=1, sticky="w")
        try:
            self.transnotes_entry.insert(0, self.track_data["values"][7])
        except:
            log.error("Couldn't insert Trans Notes Data")
        
        tk.Label(self.track_info_frame, text="Notes").grid(row=8, column=0, sticky="w")
        self.notes_entry = tk.Entry(self.track_info_frame, width=30)
        self.notes_entry.grid(row=8, column=1, sticky="w")
        try:
            self.notes_entry.insert(0, self.track_data["values"][8])
        except:
            log.error("Couldn't insert Notes Data")

        

        # for i in range(5,10):
        #     self.track_info_frame.rowconfigure(i, weight=1)



        ###############################################

        # Buttons Area

        tk.Button(self.buttons_frame, text="Save Track Data", command=self.save_track_data).pack(side="left")
        tk.Button(self.buttons_frame, text="Cancel", command=self._quit).pack(side="right")

        # Display Frames

        self.track_info_frame.pack(fill="both", expand=1, side = "top")
        self.buttons_frame.pack(side="bottom", fill="x")
    

    def save_track_data(self):

        track_details = self.mix.get_one_mix_track(self.track_data["values"][0])

        edit_answers = {}
        edit_answers["key"] = self.key_entry.get()
        edit_answers["bpm"] = self.bpm_entry.get()
        edit_answers["key_notes"] = self.keynotes_entry.get()
        edit_answers["trans_rating"] = self.transr_entry.get()
        edit_answers["trans_notes"] = self.transnotes_entry.get()
        edit_answers["notes"] = self.notes_entry.get()


        self.mix.update_mix_track_and_track_ext(track_details, edit_answers)

        log.debug("GUI: Saving Track Data: DONE")

        self._quit()



        



