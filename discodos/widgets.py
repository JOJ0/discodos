import tkinter as tk
from tkinter import ttk
from discodos import log
from discodos import models
from discodos import ctrls


class widget_frame():
    def __init__(self, parent, title, gui_ctrl):
        self.dock_win = tk.Toplevel(parent)
        log.debug("Window State is " + self.dock_win.state())
        self.win_state = self.dock_win.state()

        self.dock_win.geometry("350x600")               
        self.dock_win.resizable(False, False) 
        self.parent = parent

        self.dock_win.title(title)
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.dock_win.geometry("+%d+%d" % (x + 800, y))
        

    def _quit(self):
        self.dock_win.destroy()
        
############ EDIT MIX ###########################

class search_gui(widget_frame):
    def __init__(self, parent, title, gui_ctrl):
        super().__init__(parent, title, gui_ctrl)
        self.gui_ctrl = gui_ctrl
        self.build_search_frame()
        self.search_tv_config()
    

    def build_search_frame(self):

        self.bar_grid = tk.Frame(self.dock_win)

        self.artist_bar = tk.Entry(self.bar_grid)
        self.artist_bar.grid(row=0, column=0, columnspan=6, rowspan=1, sticky="we")

        self.release_bar = tk.Entry(self.bar_grid)
        self.release_bar.grid(row=1, column=0, columnspan=6, rowspan=1, sticky="we")

        self.track_bar = tk.Entry(self.bar_grid)
        self.track_bar.grid(row=2, column=0, columnspan=6, rowspan=1, sticky="we")

        self.bar_grid.grid(row=0, column=0, sticky="we")

        self.online = tk.IntVar()
        tk.Checkbutton(self.dock_win, text="online", variable=self.online).grid(row=0, column=8, columnspan=2, rowspan=1, sticky="w")

        self.search_button = tk.Button(self.dock_win, 
                                        text="Search...", 
                                        command=lambda : 
                                                            self.gui_ctrl.display_searched_releases((self.artist_bar.get(), 
                                                                                                    self.release_bar.get(),
                                                                                                    self.track_bar.get()),
                                                                                                    self.search_tv,
                                                                                                    self.online.get()))
        # self.search_bar.bind("<Return>", lambda srch=self.search_bar.get(): 
        #                                                     self.gui_ctrl.display_searched_releases(srch, 
        #                                                                                             self.search_tv,
        #                                                                                             self.online.get())) 

        self.search_button.grid(row=0, column=1, columnspan=2, sticky="we")
        
        self.search_tv = ttk.Treeview(self.dock_win)
        self.search_tv.grid(row=3, column=0, columnspan=10, rowspan=6, sticky="nsew")

        self.pg_bar = ttk.Progressbar(self.dock_win, orient="horizontal",mode='indeterminate')
        self.pg_bar.grid(row=10, column=0, columnspan=10, rowspan=1, sticky="we")

        for i in range(10):
            self.dock_win.columnconfigure(i, weight=1)
            self.dock_win.rowconfigure(i, weight=1)


    def search_tv_config(self):
        # self.search_tv['show'] = 'headings'
        self.search_cols = {
                        "name" : "Name", 
                        "artist" : "Artist", 
                        "id" : "ID", 
                        }

        self.search_tv["columns"] = tuple(self.search_cols)

        self.search_tv.column('#0', width=20, stretch=0)
        
        for col_id, heading in self.search_cols.items():
            self.search_tv.column(col_id, width=5, stretch=1)
            self.search_tv.heading(col_id,text=heading, anchor="w")


    def progress(self, currentValue):
        pg_bar["value"]=currentValue

    



