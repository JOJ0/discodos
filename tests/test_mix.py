import unittest
from discodos.models import *
from discodos.utils import *


class TestMix(unittest.TestCase):
    def setUp(self):
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        conf = Config()
        db_path = "{}/tests/fixtures/discobase.db ".format(conf.discodos_root)
        log.warning("db path: {}".format(db_path))
        # instantiate the Mix model class (empty, mix 123 = non-existent)
        self.mix = Mix(False, 123, db_path) 
        log.info("TestMix.setUp: done")

    def test_mix_non_existent(self):
        self.assertFalse(self.mix.id_existing)
        log.info("TestMix.mix_non_existent: done")

    #def test_existence_of_customer(self):
    #    customer = self.app.get_customer(id=10)
    #    self.assertEqual(customer.name, "Org XYZ")
    #    self.assertEqual(customer.address, "10 Red Road, Reading")

if __name__ == '__main__':
    unittest.main()
