#!/usr/bin/env python
import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *
#import inspect


class TestBrainz(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        conf = Config() # doesn't get path of test-db, so...
        empty_db_path = conf.discodos_root / 'tests' / 'fixtures' / 'discobase_empty.db'
        self.db_path = conf.discodos_root / 'tests' / 'discobase.db'
        self.clname = self.__name__ # just handy a shortcut, used in test output
        self.mb_user = conf.musicbrainz_user
        self.mb_pass = conf.musicbrainz_password
        self.mb_appid = conf.discogs_appid
        print('TestBrainz.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestBrainz.setUpClass: done\n")


    def test_search_release_online_number(self):
        print("\nTestBrainz.search_release_online_number: BEGIN")
        self.brainz = Brainz(False, self.db_path)
        if self.brainz.musicbrainz_connect(self.mb_user, self.mb_pass,
                  self.mb_appid):
            print('We are ONLINE')
            #d_return = self.brainz.search_release_online('69092') # artist or title
            ##print(dir(d_return))
            #self.assertEqual(len(d_return), 1) # should be single release in a list!
            #self.assertEqual(int(d_return[0].id), 69092) # we get it as a string!
            #self.assertEqual(d_return[0].artists[0].name, 'Amon Tobin')
            #self.assertEqual(d_return[0].title, 'Out From Out Where')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            #db_return = self.brainz.search_release_online('Amon Tobin') # artist or title
            #self.assertFalse(db_return)
        print("TestBrainz.search_release_online_number: DONE\n")

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestBrainz.teardownClass: done")