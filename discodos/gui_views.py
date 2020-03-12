import discodos.views as views
import discodos.ctrls as ctrls
import discodos.models as models
import discodos.utils as utils
import discodos.log as log

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from PIL import Image, ImageTk
import datetime


class main_frame(tk.Toplevel):
    def __init__(self, master, editor_funcs):
        tk.Toplevel.__init__(self, master)
        log.debug("############################################################")
        log.debug("###########DISCODOS#LOG#START##############################")
        log.debug("############################################################")
        image = Image.open("assets/editor.png")
        self.editor_funcs = editor_funcs
        self.background_image = ImageTk.PhotoImage(image)
        self.main_win = master 
        self.protocol('WM_DELETE_WINDOW', self.main_win.destroy)
        
        
        self.main_win.geometry("1200x700")     
        self.main_win.minsize(1200, 700)


        self.main_win.title("Discodos") # TODO: Add relevant Information to title, like Titles in Mix etc


        # Create all Widgets, outsourced to its own function
        self.create_lists()
        self.create_toolbars()
        self.spawn_editor("start")
        self.search_tv_config()

    #############################################################
    # COLUMN SORTING FUNCTION
    ############################################################

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        for i in l:
            i = list(map(int, i[0]))

        l.sort(reverse=reverse)
        print(l)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # reverse sort next time
        self.mix_list.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))

    #####################################################################################    
    # CREATE WIDGETS
    ######################################################################

    def create_lists(self):

        self.mix_frame = tk.LabelFrame(self.main_win, text="Mixes")
        self.tracks_frame = tk.LabelFrame(self.main_win, text="Tracks in Mix")

        ########################################################################
        # MIXES LISTVIEW

        self.mix_list = ttk.Treeview(self.mix_frame)
        self.mix_list.pack(fill="both", expand=1)
        self.mix_list['show'] = 'headings'

        # TRACKS LISTVIEW

        self.tracks_list = ttk.Treeview(self.tracks_frame)
        self.tracks_list.pack(fill="both", expand=1)
        self.tracks_list['show'] = 'headings'

        # CREATING ALL COLUMNS

        self.mix_cols = {
                        "mix_id" : "Mix #", 
                        "name" : "Name", 
                        "venue" : "Venue", 
                        "played" : "Played"                        
                        # "created" : "Created", 
                        # "updated" : "Updated"
                        }

        self.track_cols = {
                            "track_pos" : "#", 
                            "artist" : "Artist", 
                            "track" : "Track Name", 
                            "key" : "Key", 
                            "bpm" : "Bpm", 
                            "keynotes" : "Key Notes", 
                            "transr" : "Trans. Rating", 
                            "transnotes" : "Trans. Notes", 
                            "notes" : "Notes"
                            }


        self.mix_list["columns"] = tuple(self.mix_cols)
        self.tracks_list["columns"] = tuple(self.track_cols)


        for col_id, heading in self.mix_cols.items():
            self.mix_list.column(col_id, width=2, stretch=1)
            self.mix_list.heading(col_id,text=heading, anchor=tk.W, command=lambda _col=col_id: self.treeview_sort_column(self.mix_list, _col, False))


        for col_id, heading in self.track_cols.items():
            self.tracks_list.column(col_id, width=2, stretch=1)
            self.tracks_list.heading(col_id, text=heading,anchor=tk.W)


    #####################################
    # SPAWN EDITOR
    #####################################

    def spawn_editor(self, editor_view):

        ########### PREPARATION ###############
        
        self.editor_frame = tk.LabelFrame(self.main_win, text="Editor")
        self.move_frame = tk.Frame(self.editor_frame)

        try: 
            for name, lst in self.editor_entries.items():
                for elem in lst:
                        elem.destroy()
        except:
            pass
           
        ############### SWITCH ###################

        self.editor_entries = {
            "labels" : [],
            "entries": [],
            "buttons": []
        }

        if editor_view == 0:
            show_entries = True
            headings = list(self.mix_cols.values())
            data = self.mix_list.item(self.mix_list.focus())


            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save Mix", command=lambda : self.editor_funcs["save_mix"]( self.editor_entries["entries"],
                                                                                                                 self.mix_list.item(self.mix_list.focus(),"text"))),
                tk.Button(self.editor_frame, text="Delete Mix", command=lambda : self.editor_funcs["delete_mix"](self.mix_list.item(self.mix_list.focus(),"text")))
            ])

        elif editor_view == 1:
            show_entries = True
            headings = list(self.track_cols.values()) 
            data = self.tracks_list.item(self.tracks_list.focus())

            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save Track", command=lambda : self.editor_funcs["save_track"](  self.editor_entries["entries"],
                                                                                                                    self.mix_list.item(self.mix_list.focus(),"text"))),
                tk.Button(self.editor_frame, text="Remove Track", command=lambda : self.editor_funcs["remove_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0])),
                tk.Button(self.move_frame, text="^", command=lambda : self.editor_funcs["move_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0],
                                                                                                                "up")),
                tk.Button(self.move_frame, text="V", command=lambda : self.editor_funcs["move_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0],
                                                                                                                "down"))
            ])
            
        elif editor_view == 2:
            show_entries = True
            headings = list(self.mix_cols.values())
            data = {}
            data["values"] = []
            for elem in headings:  
                data["values"].append("")

            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save New Mix", command=lambda : self.editor_funcs["save_mix"](self.editor_entries["entries"],0))
            ])
        
        elif editor_view == "start":
            editor_image = tk.Label(self.editor_frame, image=self.background_image)
            editor_image.grid(row=0, column=0, sticky="nsew")
            headings = []
            data = {}
            data["values"] = []

        ######### DESTILLERY ###########

        try:
            for i, val  in enumerate(data["values"]):
                lab = tk.Label(self.editor_frame, text=headings[i])
                lab.grid(row=i, column=0, sticky="w")
                self.editor_entries["labels"].append(lab)
                en = tk.Entry(self.editor_frame)
                en.grid(row=i, column=1, sticky="w")
                
                en.insert(0, data["values"][i])
                self.editor_entries["entries"].append(en) 
        except:
            pass

        ######## WHICH ENTRIES ARE DISABLED ###########
        
        for i, en in enumerate(self.editor_entries["entries"]):
            if editor_view == 0:
                self.editor_entries["entries"][0].config(state='disabled')
            elif editor_view == 1:  
                if i == 0 or i == 1 or i == 2:
                    self.editor_entries["entries"][i].config(state='disabled')
            elif editor_view == 2:
                self.editor_entries["entries"][0].config(state='disabled')

        ########### BUTTONS ###########
        
        if data["values"] != "":
            col_count = 0
            row_count = 2
            for lst in self.editor_entries["buttons"]:
                for obj in lst:
                    if col_count == 1:
                        count = 0
                    obj.grid(row=len(self.editor_entries["entries"])+row_count, column=col_count, sticky="w")
                    if col_count == 1:
                        row_count += 1
                    col_count += 1

        ########### SHOW ##############

        if editor_view == 1:
            self.move_frame.grid(row=len(self.editor_entries["entries"])+1, column=1, sticky="w")

        self.editor_frame.grid(row=0, column=5, columnspan=5, rowspan=5, sticky="news")


    def create_toolbars(self):

        #########################################################################

        # STATUS BAR

        self.status=tk.StringVar()  
        self.status_bar = tk.Label(self.main_win, textvariable=self.status, anchor=tk.W, bd=1, relief=tk.SUNKEN)

        self.status.set("Ready...")

        #########################################################################
        # BUTTON AREA
        #########################################################################

        self.toolbox = tk.LabelFrame(self.main_win, text="Toolbox")
        
        self.new_mix_btn = tk.Button(self.toolbox, text="New Mix")
        self.new_mix_btn.grid(row=0, column=0, sticky="w")

        #######################################################
        # SEARCH AREA
        ##################################################################

        self.search_frame = ttk.LabelFrame(self.main_win, text="Search Releases")

        self.bar_grid = tk.Frame(self.search_frame)

        tk.Label(self.bar_grid, text="Artist").grid(row=0, column=0, sticky="e")
        self.artist_bar = tk.Entry(self.bar_grid)
        self.artist_bar.grid(row=0, column=1, columnspan=3, rowspan=1, sticky="we")

        tk.Label(self.bar_grid, text="Release").grid(row=1, column=0, sticky="e")
        self.release_bar = tk.Entry(self.bar_grid)
        self.release_bar.grid(row=1, column=1, columnspan=3, rowspan=1, sticky="we")

        tk.Label(self.bar_grid, text="Track").grid(row=2, column=0, sticky="e")
        self.track_bar = tk.Entry(self.bar_grid)
        self.track_bar.grid(row=2, column=1, columnspan=3, rowspan=1, sticky="we")

        self.search_button = tk.Button(self.bar_grid, text="Search...")
        self.search_button.grid(row=4, column=1, sticky="we", columnspan=3)

        self.online = tk.IntVar()
        tk.Checkbutton(self.bar_grid, text="online", variable=self.online).grid(row=0, column=4, sticky="ne")

        self.bar_grid.grid(row=0, column=0, columnspan=20, sticky="nw")

        # SEARCH TREEVIEW

        self.search_tv = ttk.Treeview(self.search_frame)
        self.search_tv.grid(row=3, column=0, columnspan=20, rowspan=30, sticky="nsew")

        # SEARCH TOOLS
        ###############

        self.search_tools = tk.Frame(self.search_frame)
        self.add_btn = tk.Button(self.search_tools, text="Add Track to Mix", state="disabled") 
        self.add_btn.grid(row=0, column=0, sticky="ws")

        self.search_tools.grid(row=35, column=0, columnspan=20, sticky="nsew")

        # self.pg_bar = ttk.Progressbar(self.search_frame, orient="horizontal", mode='indeterminate')
        # self.pg_bar.grid(row=15, column=0, columnspan=15, rowspan=1, sticky="we")
        
        # DISPLAY
           
        self.status_bar.grid(row=15, column=0, columnspan=15, rowspan=1, sticky="wes")
        self.mix_frame.grid(row=0, column=0, columnspan=5, rowspan=5, sticky="nwes")
        self.tracks_frame.grid(row=5, column=0, columnspan=7, rowspan=10, sticky="swen")
        self.toolbox.grid(row=5, column=7, columnspan=3,rowspan=10, sticky="sewn")
        self.search_frame.grid(row=0, column=10, columnspan=5, rowspan=40, sticky="nsew")

        # WEIGHTS

        for i in range(15):
            self.main_win.rowconfigure(i, weight=1)
            self.main_win.columnconfigure(i, weight=1)

        for i in range(20):
            self.search_frame.columnconfigure(i, weight=1)

        for i in range(40):
            self.search_frame.rowconfigure(i, weight=1)

    
    def search_tv_config(self):
        self.search_cols = {
                        "1" : "Release", 
                        "2" : "", 
                        "3" : "", 
                        }

        self.search_tv["columns"] = tuple(self.search_cols)

        self.search_tv.column('#0', width=80, stretch=0)
        
        for col_id, heading in self.search_cols.items():
            self.search_tv.column(col_id, width=5, stretch=1, anchor="w")
            self.search_tv.heading(col_id,text=heading, anchor="w")
        
        self.search_tv.bind('<<TreeviewSelect>>', lambda a : self.search_tools_config())


    def search_tools_config(self):
        if self.add_btn['state'] == "disabled":
            self.add_btn.config(state='normal')

    
    def progress(self, currentValue):
        pg_bar["value"]=currentValue
            

class setup_frame():
    def __init__(self, conn=False):

        self.setup_win = tk.Tk()  

        # self.setup_win.geometry("300x200")     
        # self.setup_win.minsize(300, 200)
        self.setup_win.resizable(False, False)  

        self.setup_win.title("Discodos Setup GUI") 
        self.conn = conn
        self.setup_ctrl = ctrls.setup_controller(self.conn)

        self.create_interface()
    
    
    def create_interface(self):
        labels = ["Discogs Token", "Discogs AppID", "Log Level"]
        self.entries = {key: None for key in labels}
        i = 0
        for label, entry in self.entries.items():
            self.entries[label] = tk.Entry(self.setup_win)
            self.entries[label].grid(row=i, column=1, sticky="we")
            tk.Label(self.setup_win, text=label).grid(row=i, column =0, sticky="we")
            i += 1
        
        self.btn_frame = tk.Frame(self.setup_win)

        self.start_setup_btn = tk.Button(self.btn_frame, text="Start Setup")
        self.start_setup_btn.grid(row=0, column=0, sticky="w")
        # When Done, change this Button text to "Done!"
        tk.Button(self.btn_frame, text="Cancel").grid(row=0, column=1, sticky="w")

        

        self.btn_frame.grid(row=len(self.entries)+1, column=1, sticky="w")

        self.log_window = tk.Text(self.setup_win, width=40, height=5)
        self.log_window.grid(row=len(self.entries)+2, column=0, columnspan=2, sticky="wens")

        self.log_window.insert(tk.END,"Logging...")