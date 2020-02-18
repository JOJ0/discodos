import tkinter as tk
from tkinter import ttk
from discodos import log
from discodos import models


class widget_frame():
    def __init__(self, parent, title):
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
    def __init__(self, parent, title):
        super().__init__(parent, title)

        self.build_search_frame()
        self.search_tv_config()
    

    def build_search_frame(self):
        self.search_bar = tk.Entry(self.dock_win)
        self.search_bar.grid(row=0, column=0, columnspan=10, rowspan=1, sticky="we")

        self.search_tv = ttk.Treeview(self.dock_win)
        self.search_tv.grid(row=1, column=0, columnspan=10, rowspan=8, sticky="nsew")

        self.pg_bar = ttk.Progressbar(self.dock_win, orient="horizontal",mode='indeterminate')
        self.pg_bar.grid(row=10, column=0, columnspan=10, rowspan=1, sticky="we")

        for i in range(10):
            self.dock_win.columnconfigure(i, weight=1)
            self.dock_win.rowconfigure(i, weight=1)


    def search_tv_config(self):
        pass



    def progress(self, currentValue):
        pg_bar["value"]=currentValue


