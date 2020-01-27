import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *


class TestMix(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        conf = Config() # doesn't get path of test-db, so...
        empty_db_path = conf.discodos_root / 'tests' / 'fixtures' / 'discobase_empty.db'
        self.db_path = conf.discodos_root / 'tests' / 'discobase.db'
        print('TestMix.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestMix.setUpClass: done\n")

    def test_mix_non_existent(self):
        print("\nTestMix.mix_non_existent: BEGIN")
        # instantiate the Mix model class (empty, mix 123 = non-existent)
        self.mix = Mix(False, 123, self.db_path) 
        self.assertFalse(self.mix.id_existing)
        print("TestMix.mix_non_existent: DONE\n")

    def test_mix_create(self):
        print("\nTestMix.mix_create: BEGIN")
        self.mix = Mix(False, 123, self.db_path) 
        db_return = self.mix.create("2020-01-01", "test venue", "test mix 1")
        self.assertEqual(db_return, 1)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test mix 1")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("TestMix.mix_create: DONE\n")

    def test_mix_delete(self):
        print("\nTestMix.mix_delete: BEGIN")
        self.mix = Mix(False, 124, self.db_path)
        db_return = self.mix.delete()
        self.assertEqual(db_return, 1)
        self.assertFalse(self.mix.id_existing)
        self.assertFalse(self.mix.name_existing)
        # self.mix.name is kept for user help output
        self.assertFalse(self.mix.venue)
        self.assertFalse(self.mix.played)
        print("TestMix.mix_delete: DONE\n")

    def test_mix_get_one_mix_track(self):
        print("\nTestMix.mix_get_one_mix_track: BEGIN")
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_one_mix_track(2) # get track #2
        #print(db_return.keys())
        #for col in db_return:
        #    log.debug(col)
        self.assertEqual(len(db_return), 12) # select returns 12 cols
        self.assertEqual(db_return["track_pos"], 2)
        self.assertEqual(db_return["discogs_title"], "Material Love")
        self.assertEqual(db_return["d_track_name"], "Hedup!")
        self.assertEqual(db_return["d_track_no"], "B2")
        self.assertEqual(db_return["trans_rating"], "++++")
        self.assertEqual(db_return["trans_notes"], "test trans 4")
        self.assertEqual(db_return["key"], "C")
        self.assertEqual(db_return["key_notes"], "test key note B2")
        self.assertEqual(db_return["bpm"], 130)
        self.assertEqual(db_return["notes"], "test note B2")
        # how would I test this? db_return["mix_track_id"], "")
        self.assertEqual(db_return["d_release_id"], 123456)
        print("TestMix.mix_get_one_mix_track: DONE\n")

    def test_mix_get_tracks_of_one_mix(self):
        print("\nTestMix.mix_get_tracks_of_one_mix: BEGIN")
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_tracks_of_one_mix()
        self.assertEqual(len(db_return), 2)
        self.assertEqual(db_return[0]["mix_id"], 125)
        self.assertEqual(db_return[0]["d_release_id"], 123456)
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[1]["mix_id"], 125)
        self.assertEqual(db_return[1]["d_release_id"], 123456)
        self.assertEqual(db_return[1]["d_track_no"], "B2")
        print("TestMix.mix_get_tracks_of_one_mix: DONE\n")

    def test_get_mix_info(self):
        print("\nTestMix.get_mix_info: BEGIN")
        self.mix = Mix(False, 126, self.db_path)
        db_return = self.mix.get_mix_info()
        self.assertEqual(len(db_return), 6)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test mix 126")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("TestMix.get_mix_info: DONE\n")

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestMix.teardownClass: done")

if __name__ == '__main__':
    unittest.main()
