from . import views
from . import ctrls
import tkinter as tk
from tkinter import ttk

class main_frame():
    def __init__(self):
        self.main_win = tk.Tk()                           
        self.main_win.geometry("860x500")                # Fixed size for now, maybe scalable later
        self.main_win.resizable(False, False)    
        
    
        self.main_win.title("Language Construction Tool") # EDIT: Add relevant Information to title, like Titles in Mix etc

        # Create all Widgets, outsourced to its own function
        self.create_widgets()
        
        
                    
    # Exit GUI cleanly
    def _quit(self):
        self.main_win.quit()
        self.main_win.destroy()
        exit() 


    #####################################################################################    
    # CREATE WIDGETS

    def create_widgets(self):
        self.mix_list = ttk.Treeview(self.main_win )
        self.mix_list.grid(row=0, column=0, sticky="ns")

        self.mix_list["columns"]=("one","two","three")
        self.mix_list.column("#0",  minwidth=4, stretch=tk.NO)
        self.mix_list.column("name", minwidth=80)
        self.mix_list.column("played",  minwidth=20, stretch=tk.NO)
        self.mix_list.column("venue", width=80, minwidth=25, stretch=tk.NO)
        self.mix_list.column("created", width=80, minwidth=20, stretch=tk.NO)
        self.mix_list.column("updated", width=80, minwidth=20, stretch=tk.NO)

        self.mix_list.heading("#0",text="Mix #",anchor=tk.W)
        self.mix_list.heading("name", text="Name", anchor=tk.W)
        self.mix_list.heading("played", text="Played",anchor=tk.W)
        self.mix_list.heading("venue", text="Venue",anchor=tk.W)
        self.mix_list.heading("created", text="Created",anchor=tk.W)
        self.mix_list.heading("updated", text="Updated",anchor=tk.W)

    
