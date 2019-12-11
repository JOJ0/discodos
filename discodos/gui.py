from . import views
from . import ctrls
import tkinter as tk
from tkinter import ttk

class main_frame():
    def __init__(self):


        self.main_win = tk.Tk()                           
        self.main_win.geometry("860x500")                # Fixed size for now, maybe scalable later
        self.main_win.resizable(False, False)    
        
    
        self.win.title("Language Construction Tool") # EDIT: Add relevant Information to title, like Titles in Mix etc

        # Create all Widgets, outsourced to its own function
        self.create_widgets()
        
        
                    
    # Exit GUI cleanly
    def _quit(self):
        self.win.quit()
        self.win.destroy()
        exit() 


    #####################################################################################    
    # CREATE WIDGETS

    def create_widgets(self):
        pass
