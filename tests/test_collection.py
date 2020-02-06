#!/usr/bin/env python
import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *


class TestCollection(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        self.conf = Config() # doesn't get path of test-db, so...
        empty_db_path = self.conf.discodos_root / 'tests' / 'fixtures' / 'discobase_empty.db'
        self.db_path = self.conf.discodos_root / 'tests' / 'discobase.db'
        print('TestMix.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestMix.setUpClass: done\n")

    def test_get_all_db_releases(self):
        print("\nTestMix.get_all_db_releases: BEGIN")
        # instantiate the Collection model class
        self.collection = Collection(False, self.db_path) 
        db_return = self.collection.get_all_db_releases()
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 4)
        self.assertEqual(db_return[2]['discogs_id'], 123456)
        self.assertEqual(db_return[2]['discogs_title'], 'Material Love')
        #self.assertEqual(db_return[2]['import_timestamp'], '2020-01-25 22:33:35')
        self.assertEqual(db_return[2]['d_artist'], 'Märtini Brös.')
        #self.assertEqual(db_return[2]['in_d_collection'], 1)
        self.assertEqual(db_return[3]['discogs_id'], 8620643)
        self.assertEqual(db_return[3]['discogs_title'], 'The Crane')
        #self.assertEqual(db_return[3]['import_timestamp'], '2020-01-30 10:06:26')
        self.assertEqual(db_return[3]['d_artist'], 'Source Direct')
        #self.assertEqual(db_return[3]['in_d_collection'], 1)
        print("TestMix.get_all_db_releases: DONE\n")

    def test_search_release_id(self):
        print("\nTestMix.search_release_id: BEGIN")
        # instantiate the Collection model class
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_id('123456')
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 5) # should be 5 columns
        self.assertEqual(db_return['discogs_id'], 123456)
        self.assertEqual(db_return['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return['discogs_title'], 'Material Love')
        print("TestMix.search_release_id: DONE\n")

    def test_search_release_offline_number(self):
        print("\nTestMix.search_release_offline_number: BEGIN")
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_offline('123456')
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 5) # should be 5 columns
        self.assertEqual(db_return['discogs_id'], 123456)
        self.assertEqual(db_return['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return['discogs_title'], 'Material Love')
        print("TestMix.search_release_offline_number: DONE\n")

    def test_search_release_offline_number_error(self):
        print("\nTestMix.search_release_offline_number_error: BEGIN")
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_offline('999999')
        self.assertIsNone(db_return)
        print("TestMix.search_release_offline_number_error: DONE\n")

    def test_search_release_offline_text(self):
        print("\nTestMix.search_release_offline_text: BEGIN")
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_offline('Märtini') # artist or title
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 1) # should be a list with 1 Row
        self.assertEqual(db_return[0]['discogs_id'], 123456)
        self.assertEqual(db_return[0]['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return[0]['discogs_title'], 'Material Love')
        print("TestMix.search_release_offline_text: DONE\n")

    def test_search_release_offline_text_multiple(self):
        print("\nTestMix.search_release_offline_text_multiple: BEGIN")
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_offline('Amon') # artist or title
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 2) # should be a list with 2 Rows
        self.assertEqual(db_return[0]['discogs_id'], 69092)
        self.assertEqual(db_return[0]['d_artist'], 'Amon Tobin')
        self.assertEqual(db_return[0]['discogs_title'], 'Out From Out Where')
        self.assertEqual(db_return[1]['discogs_id'], 919698)
        self.assertEqual(db_return[1]['d_artist'], 'Amon Tobin')
        self.assertEqual(db_return[1]['discogs_title'], 'Foley Room')
        print("TestMix.search_release_offline_text_multiple: DONE\n")

    def test_search_release_offline_text_error(self):
        print("\nTestMix.search_release_offline_text_error: BEGIN")
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_offline('XXX') # artist or title
        self.assertIsNone(db_return) # returns None if nothing found
        #self.assertEqual(db_return, []) # FIXME should this better be empty list?
        print("TestMix.search_release_offline_text_error: DONE\n")

    def test_search_release_online_text_multiple(self):
        print("\nTestMix.search_release_online_text_multiple: BEGIN")
        self.collection = Collection(False, self.db_path)
        if self.collection.discogs_connect(self.conf.discogs_token,
            self.conf.discogs_appid):
            print('We are ONLINE')
            d_return = self.collection.search_release_online('Amon Tobin') # artist or title
            self.assertEqual(len(d_return), 770) # _currently_ list with 770 Release objects
            self.assertEqual(d_return.pages, 16) # _currently_ 16 pages
            self.assertEqual(d_return.per_page, 50) # 50 per_page
            self.assertEqual(d_return[0].id, 3618346)
            self.assertEqual(d_return[0].artists[0].name, 'Amon Tobin')
            self.assertEqual(d_return[0].title, 'Amon Tobin') # yes, really!
            self.assertEqual(d_return[1].id, 3620565)
            self.assertEqual(d_return[1].artists[0].name, 'Amon Tobin')
            self.assertEqual(d_return[1].title, 'Amon Tobin') # yes, really!
            self.assertEqual(d_return[1].tracklist[0].title, 'ISAM Live')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            db_return = self.collection.search_release_online('Amon Tobin') # artist or title
            self.assertFalse(db_return)
        print("TestMix.search_release_online_text_multiple: DONE\n")

    def test_search_release_online_number(self):
        print("\nTestMix.search_release_online_number: BEGIN")
        self.collection = Collection(False, self.db_path)
        if self.collection.discogs_connect(self.conf.discogs_token,
            self.conf.discogs_appid):
            print('We are ONLINE')
            d_return = self.collection.search_release_online('69092') # artist or title
            #print(dir(d_return))
            self.assertEqual(len(d_return), 1) # should be single release in a list!
            self.assertEqual(int(d_return[0].id), 69092) # we get it as a string!
            self.assertEqual(d_return[0].artists[0].name, 'Amon Tobin')
            self.assertEqual(d_return[0].title, 'Out From Out Where')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            db_return = self.collection.search_release_online('Amon Tobin') # artist or title
            self.assertFalse(db_return)
        print("TestMix.search_release_online_number: DONE\n")

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestMix.teardownClass: done")

if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestCollection, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)
