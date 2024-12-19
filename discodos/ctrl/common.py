import logging
from abc import ABC

from discodos.config import Db_setup

log = logging.getLogger('discodos')


class ControlCommon (ABC):
    """Common controller functionality"""
    def setup_db(self, db_file):
        """Manages database initialization and schema upgrades"""
        db_setup = Db_setup(db_file)
        db_setup.create_tables()
        db_setup.upgrade_schema()
