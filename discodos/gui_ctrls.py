import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from discodos.gui_views import *
from discodos.views import View_common
from discodos import utils
from discodos.models import *
from discodos.ctrls import *

class mix_ctrl_gui(Mix_ctrl_common):

    def __init__(self, root, conn, start_up):
        self.flip = False
        self.start_up = start_up
        self.conn = conn
        self.cv = views.View_common()

        self.editor_funcs=   {
                            "save_track" : self.save_track_data,
                            "save_mix" : self.save_mix_data,
                            "delete_mix" : self.delete_selected_mix,
                            "remove_track" : self.remove_track_from_mix,
                            "move_track" : self.move_track_pos
                            }


        self.search_funcs = [
                '''self.display_searched_releases((self.main_win.artist_bar.get(), 
                                                        self.main_win.release_bar.get(),
                                                        self.main_win.track_bar.get()),
                                                        self.main_win.search_tv,
                                                        self.main_win.online.get())'''
                                    ]

        self.main_win = main_frame(root, self.editor_funcs)
        self.main_win.withdraw() 
        # Controller would create its own Toplevel Window,
        # withdraw prevents it

        self.display_all_mixes()
        self.main_frame_config()


    def main_frame_config(self):
        self.main_win.mix_list.bind('<<TreeviewSelect>>', lambda a : self.display_tracklist(self.main_win.mix_list.item(self.main_win.mix_list.focus(),"text")))
        self.main_win.tracks_list.bind('<<TreeviewSelect>>', lambda a : self.main_win.spawn_editor(1))
        self.main_win.search_button.configure(command=lambda:eval(self.search_funcs[0]))
        self.main_win.add_btn.configure(command = lambda : self.add_track_to_mix(self.main_win.search_tv))
        self.main_win.new_mix_btn.configure(command=lambda: self.main_win.spawn_editor(2))
        self.main_win.artist_bar.bind("<Return>", lambda x:eval(self.search_funcs[0]))
        self.main_win.release_bar.bind("<Return>", lambda x:eval(self.search_funcs[0]))
        self.main_win.track_bar.bind("<Return>", lambda x:eval(self.search_funcs[0]))
    

    def display_all_mixes(self, date=False):
        
        all_mix = Mix(self.conn, "all")
        if date == False:
            self.mixes_data = all_mix.get_all_mixes(order_by="played ASC")
        else:
            self.mixes_data = all_mix.get_all_mixes(order_by="played DESC")

        self.main_win.mix_list.delete(*self.main_win.mix_list.get_children())

        # self.dates = {}
        for i, row in enumerate(self.mixes_data):
            # self.dates[row["played"]] = self.cv.format_date_month(self.cv.none_replace(row["played"]))

            self.main_win.mix_list.insert("" , i, text=row["mix_id"], 
                                        values=(self.cv.none_replace(row["mix_id"]), 
                                                self.cv.none_replace(row["name"]), 
                                                self.cv.none_replace(row["venue"]), 
                                                self.cv.format_date_month(self.cv.none_replace(row["played"]))))
            # print(self.cv.none_replace(row["played"]), self.cv.format_date_month(self.cv.none_replace(row["played"])))
        if self.start_up == True:
            self.col_widths(self.main_win.mix_list, self.main_win.mix_cols)
            self.start_up = False

        if self.flip == False:
            self.main_win.mix_list.heading("played", command=lambda : self.display_all_mixes(date=True))
            self.flip = not self.flip
        else:
            self.main_win.mix_list.heading("played", command=lambda : self.display_all_mixes(date=False))
            self.flip = not self.flip

    
    def display_tracklist(self, selected_mix_id):
        self.main_win.tracks_list.delete(*self.main_win.tracks_list.get_children())

        mix = Mix(self.conn, selected_mix_id)
        mix_data = mix.get_full_mix(verbose = True) 

        for i, row in enumerate(mix_data):
            self.main_win.tracks_list.insert("", i, text="", values=( self.cv.none_replace(row["track_pos"]), 
                                                        self.cv.none_replace(row["d_artist"]), 
                                                        self.cv.none_replace(row["d_track_name"]), 
                                                        self.cv.none_replace(row["key"]), 
                                                        self.cv.none_replace(row["bpm"]), 
                                                        self.cv.none_replace(row["key_notes"]), 
                                                        self.cv.none_replace(row["trans_rating"]), 
                                                        self.cv.none_replace(row["trans_notes"]), 
                                                        self.cv.none_replace(row["notes"])))
        # if self.start_up == True:
        #     self.col_widths(self.main_win.tracks_list, self.main_win.track_cols)
        #     self.start_up = False
        
        self.main_win.spawn_editor(0)


    def col_widths(self, tree_view, headings):

        width_vals = {}     

        for col_id, heading in headings.items():
            width_vals[col_id] = []
        

        for i, row in enumerate(self.mixes_data):
            for col_id, heading in headings.items():
                try:
                    width_vals[col_id].append(tkfont.Font().measure(none_checker(row[col_id])))
                except:
                    width_vals[col_id].append(10)
                    

        for col_id, heading in headings.items():
            tree_view.column(col_id, width=max(width_vals[col_id]), minwidth=tkfont.Font().measure(heading), stretch=1)


    def delete_selected_mix(self, selected):
        mix = Mix(self.conn, selected)
        try:
            mix.delete()
            log.info("GUI: Deleted Mix from list")
        except:
            log.error("GUI; Failed to delete Mix!")

        self.display_all_mixes()

    
    def save_track_data(self, editor_entries, selected_id):
        mix = Mix(self.conn, selected_id)
        track_details = mix.get_one_mix_track(editor_entries[0].get())

        edit_answers = {}
        edit_answers["key"] = editor_entries[3].get()
        edit_answers["bpm"] = editor_entries[4].get()
        edit_answers["key_notes"] = editor_entries[5].get()
        edit_answers["trans_rating"] = editor_entries[6].get()
        edit_answers["trans_notes"] = editor_entries[7].get()
        edit_answers["notes"] = editor_entries[8].get()
        

        mix.update_mix_track_and_track_ext(track_details, edit_answers)

        log.debug("GUI: Saving Track Data: DONE")

        self.display_tracklist(selected_id)


    def save_mix_data(self, editor_entries, selected_id):
        mix = Mix(self.conn, selected_id)
        mix.create( editor_entries[3].get(),
                    editor_entries[2].get(),
                    editor_entries[1].get(),)
                    
        self.display_all_mixes()


    def remove_track_from_mix(self, selected_mix_id, selected_track_id):
        mix = Mix(self.conn, selected_mix_id)
        mix.delete_track(selected_track_id)
        mix.reorder_tracks(selected_track_id)
        self.display_tracklist(selected_mix_id)
        self.focus_object(self.main_win.tracks_list, selected_track_id-1)

    def move_track_pos(self, selected_mix_id, selected_track_id, direction):
        mix = Mix(self.conn, selected_mix_id)
        mix.shift_track(selected_track_id, direction)
        self.display_tracklist(selected_mix_id)
        # if direction == 'down':
        #     self.focus_object(self.main_win.tracks_list, selected_track_id-1)
        # elif direction == 'up':
        #     self.focus_object(self.main_win.tracks_list, selected_track_id+1)


    def display_searched_releases(self, search_terms, search_tv, online):
        # OFFLINE
        grouped_releases = []
        search_tv.delete(*search_tv.get_children())
        coll = Collection(self.conn)
        # print(search_terms)

        if online == 0:
            found_releases = coll.search_release_track_offline(search_terms[0], search_terms[1], search_terms[2])
            grouped_releases = self.group_releases(found_releases)

            release_levels = {}
            i = 0
            for release, details in grouped_releases.items():
                release_levels[i] = search_tv.insert("", i, text="", values=([release]))
                for j, track_detail in enumerate(details):
                       search_tv.insert(release_levels[i],j, text=track_detail[0], values=(track_detail[1], track_detail[2], track_detail[3]))
                i += 1

        elif online == 1:
            # ONLINE
            found_releases = coll.search_release_online(search_term)
            grouped_releases = self.group_releases(found_releases)
            release_levels = {}
            if found_releases is not None:
                for i, release in enumerate(found_releases):
                    release_levels[i] = search_tv.insert("", i, text="", values=(release["discogs_title"],release["d_artist"], release["d_track_no"]))
                    for j in range(2):
                       search_tv.insert(release_levels[i],j, text="", values=("Test Track"))
            else:
                log.error("GUI: No online Releases Found")

    
    def group_releases(self, found_releases):
        all_releases = {}
        temp = []

        for release in found_releases:
            temp.append(release["discogs_title"])
        
        unique_releases = list(set(temp))

        for uni_rel in unique_releases:
            all_releases[uni_rel] = []
            for release in found_releases:
                if release["discogs_title"] == uni_rel:
                    all_releases[uni_rel].append([release["d_track_no"], release["discogs_title"], release["d_artist"], release["d_release_id"] ])

        return all_releases


    def focus_object(self, tree_view, pos):
        # print(pos)
        child_id = tree_view.get_children()[int(pos)]
        # print(pos)
        tree_view.focus(child_id)
        tree_view.selection_set(child_id)


    def add_track_to_mix(self, search_tv):
        element = self.main_win.tracks_list.focus()
        print(element)
        try:
            pos = self.main_win.tracks_list.get_children().index(element)+1
        except:
            pos=len(self.main_win.tracks_list.get_children())+1

        sel_mix_id = self.main_win.mix_list.item(self.main_win.mix_list.focus(),"text")
        mix = Mix(self.conn, sel_mix_id)
        cur_item = search_tv.item(search_tv.focus())
        tracks_to_shift = mix.get_tracks_from_position(pos)
        print(cur_item["values"][2])
        mix.add_track(cur_item["values"][2], cur_item["text"], pos)
        mix.reorder_tracks_squeeze_in(pos, tracks_to_shift)
        self.display_tracklist(sel_mix_id)
    
        
class setup_controller():
    def __init__(self, conn=False):
        pass

    def write_yaml_file(self, setup_entries):
        pass

    def initiate_setup(self, setup_entries):
        self.write_yaml_file(setup_entries)
        pass