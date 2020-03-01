################################
# IMPORTS
import discodos.views as views
import discodos.ctrls as ctrls
import discodos.models as models
import discodos.utils as utils
import discodos.log as log
from discodos.widgets import search_gui

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tabulate import tabulate as tab
from PIL import Image, ImageTk



#################################

class main_frame():
    def __init__(self, conn=False):

        

        log.debug("############################################################")
        log.debug("###########DISCODOS#LOG#START##############################")
        log.debug("############################################################")
        self.search_open = False
        self.main_win = tk.Tk()  

        image = Image.open("assets/editor.png")
        self.background_image = ImageTk.PhotoImage(image)
        
        

        self.main_win.geometry("800x600")     
        self.main_win.minsize(800, 600)

        
        

        self.main_win.title("Discodos") # TODO: Add relevant Information to title, like Titles in Mix etc
        self.conn = conn

        ########################################## GUI CONTROLLER
        
        

        # Create all Widgets, outsourced to its own function
        self.create_lists()
        self.gui_ctrl = ctrls.mix_ctrl_gui( self.conn, 
                                            self.mix_cols, 
                                            self.track_cols, 
                                            self.mix_list, 
                                            self.tracks_list)

        self.save_funcs =   {
                            "save_track" : self.gui_ctrl.save_track_data,
                            "save_mix" : self.gui_ctrl.save_mix_data,
                            "delete_mix" : self.gui_ctrl.delete_selected_mix,
                            "remove_track" : self.gui_ctrl.remove_track_from_mix,
                            "move_track" : self.gui_ctrl.move_track_pos
                            }


        self.create_toolbars()
        # self.focus_first_object(self.mix_list)
        self.gui_ctrl.display_all_mixes()
        self.show_tracklist()
        self.spawn_editor("start")

        
                    
    # Exit GUI cleanly
    def _quit(self):
        self.main_win.quit()
        self.main_win.destroy()
        exit() 

    # Instantiate the DB-Connector and load the Data


# EVENT TRIGGER UNCTION - UPDATE TRACK LIST            
        
    def show_tracklist(self):
        self.gui_ctrl.display_tracklist(self.mix_list.item(self.mix_list.focus(),"text"))
        self.spawn_editor(0)


    
    #############################################################
    # COLUMN SORTING FUNCTION
    ############################################################

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

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

        self.mix_list.bind('<<TreeviewSelect>>', lambda a : self.show_tracklist())
        self.tracks_list.bind('<<TreeviewSelect>>', lambda a : self.spawn_editor(1))


    ####################################
    # EDITOR
    ###################################

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
                tk.Button(self.editor_frame, text="Save Mix", command=lambda : self.save_funcs["save_mix"]( self.editor_entries["entries"],
                                                                                                                 self.mix_list.item(self.mix_list.focus(),"text"))),
                tk.Button(self.editor_frame, text="Delete Mix", command=lambda : self.save_funcs["delete_mix"](self.mix_list.item(self.mix_list.focus(),"text")))
            ])


        elif editor_view == 1:
            show_entries = True
            headings = list(self.track_cols.values()) 
            data = self.tracks_list.item(self.tracks_list.focus())

            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save Track", command=lambda : self.save_funcs["save_track"](  self.editor_entries["entries"],
                                                                                                                    self.mix_list.item(self.mix_list.focus(),"text"))),
                tk.Button(self.editor_frame, text="Remove Track", command=lambda : self.save_funcs["remove_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0])),
                tk.Button(self.move_frame, text="^", command=lambda : self.save_funcs["move_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0],
                                                                                                                "up")),
                tk.Button(self.move_frame, text="V", command=lambda : self.save_funcs["move_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
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
                tk.Button(self.editor_frame, text="Save New Mix", command=lambda : self.save_funcs[1](self.editor_entries["entries"],
                                                                                                                    self.mix_list.item(self.mix_list.focus(),"text")))
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
        
        self.new_mix_btn = tk.Button(self.toolbox, text="New Mix", command=lambda: self.spawn_editor(2))
        self.new_mix_btn.grid(row=0, column=0, sticky="w")




        #########
        # SEARCH TOGGLE BUTTON
        self.search_toggle = tk.Button(self.main_win, text = ">", command=self.toggle_search_window) 
        

        # DISPLAY
           
        self.status_bar.grid(row=10, column=0, columnspan=10, rowspan=1, sticky="we")
        self.mix_frame.grid(row=0, column=0, columnspan=5, rowspan=5, sticky="nwes")
        self.tracks_frame.grid(row=5, column=0, columnspan=7, rowspan=4, sticky="swen")
        self.toolbox.grid(row=5, column=7, columnspan=3,rowspan=4, sticky="sewn")
        self.search_toggle.grid(row=0, column=11, columnspan=1,rowspan=11, sticky="sn")
        
        # WEIGHTS

        for i in range(11):
            self.main_win.columnconfigure(i, weight=1)
            self.main_win.rowconfigure(i, weight=1)

    
    def toggle_search_window(self):
        if self.search_open == False:
                self.search_window = search_gui(self.main_win, "Search Releases...", self.gui_ctrl) 
                self.search_window.dock_win.focus()
                self.search_open = True
        else:
            self.search_window._quit()
            self.search_open = False

            

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

        

                