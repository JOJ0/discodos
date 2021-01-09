#!/usr/bin/env python
import inspect
import os
import unittest
from pathlib import Path
from shutil import copy2

from discodos.config import Config, Db_setup, create_data_dir
from discodos.models import Collection, log


class TestConfig(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        name = inspect.currentframe().f_code.co_name
        self.clname = self.__name__ # just handy a shortcut, used in test output
        print("\n{} - {} - BEGIN".format(self.clname, name))
        #log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        # first ever config init prints info and raises SystemExit(0)
        self.conf = Config()
        #discodos_tests = Path(os.path.dirname(os.path.abspath(__file__)))
        #empty_db_path = discodos_tests / 'fixtures' / 'discobase_empty.db'
        #self.db_path = discodos_tests / 'discobase.db'
        #print('Database: {}'.format(copy2(empty_db_path, self.db_path)))
        print("{} - {} - END\n".format(self.clname, name))

    def test_config_secondrun(self):
        self.conf = Config()
        self.assertIsInstance(self.conf, Config)

    def debug_db(self, db_return):
        #print(db_return.keys())
        print()
        if isinstance(db_return, list):
            print('db_return is a list')
            for i in db_return:
                stringed = ''
                for j in i:
                    stringed+='{}, '.format(j)
                print(stringed)
                print()
        elif isinstance(db_return, sqlite3.Row):
            print('db_return is a Row')
            stringed = ''
            for i in db_return:
                stringed+='{}, '.format(i)
            print(stringed)
            print()
        else:
            print('unknown datatype, cannot debug')
        return True


    @classmethod
    def tearDownClass(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        #os.remove(self.db_path)
        print("{} - {} - END\n".format(self.clname, name))

if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestConfig, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)
