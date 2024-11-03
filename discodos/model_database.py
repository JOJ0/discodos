import logging
# import pprint
from sqlite3 import Error as sqlerr
import sqlite3

log = logging.getLogger('discodos')


class Database():
    """Shared database backend methods."""

    def __init__(self, db_conn=False, db_file=False, setup=False):
        self.db_not_found = False
        if db_conn:
            log.debug("DB: db_conn argument was handed over.")
            self.db_conn = db_conn
        else:
            log.debug("DB: Creating connection to db_file.")
            if not db_file:
                log.debug("DB: No db_file given, using default name.")
                db_file = './discobase.db'
            self.db_conn = self.create_conn(db_file, setup)  # setup=True creates empty db
            if self.db_conn is None:
                log.debug("DB: Creating database.")
                self.db_conn = self.create_conn(db_file, setup=True)
        self.db_conn.row_factory = sqlite3.Row  # also this was in each db.function before
        self.cur = self.db_conn.cursor()  # we had this in each db function before
        self.configure_db()  # set PRAGMA options

    def create_conn(self, db_file, setup=False):
        try:  # format ensures db_file is string. uri rw mode throws error if non-existen
            if setup:
                conn = sqlite3.connect('file:{}'.format(db_file), uri=True)
            else:
                conn = sqlite3.connect('file:{}?mode=rw'.format(db_file), uri=True)
            return conn
        except sqlerr as e:
            if e.args[0] == 'unable to open database file':
                e = "DB: create_conn: Database {} can't be opened.".format(db_file)
                log.debug(e)
                self.db_not_found = True
                return None
            else:
                log.error("DB: Connection error: %s", e)
                raise SystemExit(4)  # 4 = other db error. will SystemExit break gui?

    def execute_sql(self, sql, values_tuple=False, raise_err=False):
        '''used for eg. creating tables or inserts'''
        log.info("DB: execute_sql: %s", sql)
        try:
            with self.db_conn:  # auto commits and auto rolls back on exceptions
                c = self.cur  # connection close has to be done manually though!
                if values_tuple:
                    log.info("DB: ...with this tuple: {%s}", values_tuple)
                    c.execute(sql, values_tuple)
                else:
                    c.execute(sql)
                log.info("DB: rowcount: {}, lastrowid: {}".format(c.rowcount,
                         c.lastrowid))
                # log.info("DB: Committing NOW")
                # self.db_conn.commit()
            log.debug("DB: Committing via context close NOW")
            self.lastrowid = c.lastrowid
            return c.rowcount
        except sqlerr as e:
            # log.error("DB: %s", dir(e))
            if raise_err:
                log.debug("DB: Raising error to upper level.")
                raise e
            else:
                log.error("DB: %s", e.args[0])
            return False

    def configure_db(self):
        settings = "PRAGMA foreign_keys = ON;"
        self.execute_sql(settings)

    def _select_simple(
        self,
        fields_list,
        table,
        condition=False,
        offset=0,
        fetchone=False,
        orderby=False,
        distinct=False,
        join=None,
    ):
        """This is a wrapper around the _select method.
        It puts together SQL select statements as strings with support for JOIN.
        """
        log.info(f"DB: _select_simple: fetchone = {fetchone}")
        fields_str = ", ".join(fields_list)
        join_clause = ""
        if join:
            # Expecting join as a list of tuples: [(join_type, table, condition), ...]
            for join_type, join_table, join_condition in join:
                join_clause += f" {join_type.upper()} JOIN {join_table} ON {join_condition}"
        where_or_not = f"WHERE {condition}" if condition else ""
        orderby_or_not = f"ORDER BY {orderby}" if orderby else ""
        select = "SELECT DISTINCT" if distinct else "SELECT"
        limit = f"LIMIT -1 OFFSET {offset}" if offset else ""
        select_str = (
            f"{select} {fields_str} FROM {table} {join_clause} {where_or_not} "
            f"{orderby_or_not} {limit};"
        )
        return self._select(select_str, fetchone)

    def _select(self, sql_select, fetchone=False):
        """Executes sql selects in two possible ways: fetchone or fetchall
           It's completely string based and not aware of tuple based
           values substitution in sqlite3 cursor objects.

        @param sql_select (string): the complete sql select statement
        @param fetchone (bool): defaults to False (return multiple rows)
        @return (type is depending on running mode)
            fetchone = True:
                something found: sqlite3.Row (dict-like) object
                nothing found: None
            fetchone = False (fetchall, this is the default)
                something found: a list of sqlite3.Row (dict-like) objects
                nothing found: an empty list
        """
        log.info("DB: _select: {}".format(sql_select))
        self.cur.execute(sql_select)
        if fetchone:
            rows = self.cur.fetchone()
        else:
            rows = self.cur.fetchall()

        if rows:
            # log.debug("DB: rowcount: {}, lastrowid: {} (irrelevant in selects)".format(
            #     self.cur.rowcount, self.cur.lastrowid))
            if fetchone:  # len will return column count
                log.info('DB: Found 1 row containing {} columns.'.format(len(rows.keys())))
            else:  # len will return rows count
                log.info('DB: Found {} rows containing {} columns.'.format(
                    len(rows), len(rows[0])))
            log.debug("DB: Returning row(s) as type: {}.".format(type(rows).__name__))
            return rows
        else:
            log.info('DB: Nothing found - Returning type: {}.'.format(type(rows).__name__))
            return rows  # was empty list before, now it's either empty list or NoneType

    def debug_db(self, db_return):
        # print(dbr.keys())
        print()
        for i in db_return:
            # print(i.keys())
            stringed = ''
            for j in i:
                stringed+='{}, '.format(j)
            print(stringed)
            print()
        return True
