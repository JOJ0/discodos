#!/usr/bin/env python
import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *
import inspect


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


    def test_get_mb_artist_by_id(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(False, self.db_path)
        if self.brainz.musicbrainz_connect(self.mb_user, self.mb_pass,
                  self.mb_appid):
            print('We are ONLINE')
            mb_return = self.brainz.get_mb_artist_by_id('952a4205-023d-4235-897c-6fdb6f58dfaa')
            #print(dir(mb_return))
            #print(mb_return)
            self.assertEqual(len(mb_return), 1) # should be single release in a list!
            self.assertEqual(mb_return['artist']['name'], 'Dynamo Go')
            self.assertEqual(mb_return['artist']['country'], 'NZ')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            mb_return = self.brainz.get_mb_artist_by_id('952a4205-023d-4235-897c-6fdb6f58dfaa')
            self.assertFalse(mb_return)
        print("{} - {} - END".format(self.clname, name))

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestBrainz.teardownClass: done")