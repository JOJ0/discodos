import logging
# import pprint
from sqlite3 import Error as sqlerr
import sqlite3

log = logging.getLogger('discodos')


class Database():
    """Shared database backend methods."""

    def __init__(self, db_conn=False, db_file=False, setup=False):
        self.db_not_found = False
        self.lastrowid = None
        if db_conn:
            log.debug("DB: db_conn argument was handed over.")
            self.db_conn = db_conn
        else:
            log.debug("DB: Creating connection to db_file.")
            if not db_file:
                log.debug("DB: No db_file given, using default name.")
                db_file = "./discobase.db"
            self.db_conn = self.create_conn(
                db_file, setup
            )  # setup=True creates empty db
            if self.db_conn is None:
                log.debug("DB: Creating database.")
                self.db_conn = self.create_conn(db_file, setup=True)
        self.db_conn.row_factory = (
            sqlite3.Row
        )  # also this was in each db.function before
        self.cur = (
            self.db_conn.cursor()
        )  # we had this in each db function before
        self.configure_db()  # set PRAGMA options

    def create_conn(self, db_file, setup=False):
        # format() ensures db_file is string. uri rw mode throws error if
        # non-existent
        try:
            if setup:
                conn = sqlite3.connect("file:{}".format(db_file), uri=True)
            else:
                conn = sqlite3.connect(
                    "file:{}?mode=rw".format(db_file), uri=True
                )
            return conn
        except sqlerr as e:
            if e.args[0] == "unable to open database file":
                e = "DB: create_conn: Database {} can't be opened.".format(
                    db_file
                )
                log.debug(e)
                self.db_not_found = True
                return None
            else:
                log.error("DB: Connection error: %s", e)
                # 4 = other db error. will SystemExit break gui?
                raise SystemExit(4)

    def execute_sql(self, sql, values_tuple=False, raise_err=False):
        """used for eg. creating tables or inserts"""
        log.info("DB: execute_sql: %s", sql)
        try:
            with self.db_conn:  # auto commits and auto rolls back on exceptions
                c = (
                    self.cur
                )  # connection close has to be done manually though!
                if values_tuple:
                    log.info("DB: ...with tuple: %s", values_tuple)
                    c.execute(sql, values_tuple)
                else:
                    c.execute(sql)
                log.debug("DB: Committing NOW")
                self.db_conn.commit()
                log.debug("DB: rowcount: %s, lastrowid: %s", c.rowcount, c.lastrowid)
            log.debug("DB: Committing via context close NOW")
            log.debug("DB: rowcount: %s, lastrowid: %s", c.rowcount, c.lastrowid)
            self.lastrowid = c.lastrowid
            return c.rowcount
        except sqlerr as e:
            if raise_err:
                log.debug("DB: Raising error to upper level.")
                raise e
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
        as_dict=False,
        union=None,
        reverse_order=False,
        limit=None
    ):
        """Wrapper around the _select method. Puts together SELECT as string.

        Args:
            fields_list (list): Rields to select.
            table (str): Primary table.
            condition (str, optional): WHERE clause condition.
            offset (int, optional): Offset for pagination.
            fetchone (bool, optional): Fetch only one row.
            orderby (str, optional): ORDER BY clause.
            distinct (bool, optional): Use SELECT DISTINCT.
            join (list, optional): List of tuples specifying JOINs.
                Format: [(join_type, table, condition), ...].
            as_dict (bool, optional): Return results as a dictionary.
            union (list, optional): List of dicts representing UNION statements.
                Each dict has keys: fields_list, table, condition, join.
            limit (int, optional): limit results.

        Returns:
            Query results from _select.
        """
        log.debug("DB: _select_simple: fetchone = %s", fetchone)
        fields_str = ", ".join(fields_list)
        join_clause = ""
        limit_clause = ""
        if join:
            # Expecting join as a list of tuples: [(join_type, table, condition), ...]
            for join_type, join_table, join_cond in join:
                join_clause += f" {join_type} JOIN {join_table} ON {join_cond}"
        where_clause = f"WHERE {condition}" if condition else ""
        orderby_clause = f"ORDER BY {orderby}" if orderby else ""
        orderby_clause += " DESC" if reverse_order else ""
        select = "SELECT DISTINCT" if distinct else "SELECT"
        if offset and limit:
            limit_clause = f"LIMIT {limit} OFFSET {offset}"
        elif offset:
            limit_clause = f"LIMIT -1 OFFSET {offset}"
        elif limit:
            limit_clause = f"LIMIT {limit}"

        # Build the main SELECT query
        main_select = (
            f"{select} {fields_str} FROM {table} {join_clause} {where_clause}"
        )
        # Build and combine UNION queries with the main SELECT
        union_queries = []
        if union:
            for union_part in union:
                union_fields = ", ".join(union_part["fields_list"])
                union_join_clause = ""
                if union_part.get("join"):
                    for join_type, join_table, join_condition in union_part["join"]:
                        union_join_clause += (
                            f" {join_type} JOIN {join_table} " f" ON {join_condition}"
                        )
                union_where_clause = (
                    f"WHERE {union_part['condition']}"
                    if union_part.get("condition")
                    else ""
                )
                union_queries.append(
                    f"{select} {union_fields} FROM {union_part['table']} "
                    f"{union_join_clause} {union_where_clause}"
                )

        select_str = (
            f"{main_select} UNION {' UNION '.join(union_queries)} "
            f"{orderby_clause} {limit_clause}"
            if union_queries
            else f"{main_select} {orderby_clause} {limit_clause}"
        )
        return self._select(select_str, fetchone, as_dict=as_dict)

    def _select(self, sql_select, fetchone=False, as_dict=False):
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
            as_dict = True:
                return as a key value dict. This is only available when fetchone is also
                enabled! Silently ignored if fetchone is False.
        """
        log.info("DB: _select: %s", sql_select)
        self.cur.execute(sql_select)
        try:
            rows = self.cur.fetchone() if fetchone else self.cur.fetchall()
            log.debug("DB: _select: fetchone() or fetchall() successful.",)
        except Exception as e:
            log.error("DB: _select: %s", e.args[0])
            rows = None

        # Returns either empty list or NoneType depending on fetchone flag
        # (was always empty list in old code)
        if not rows:
            log.info("DB: Nothing found - Returning type: %s.", type(rows).__name__)
            return rows

        # The default, we return a list of Rows
        if not fetchone:
            log.info(
                "DB: Found %s rows with %s columns.", len(rows), len(rows[0])
            )

        # The fetchone flag is set, we return one Row
        if fetchone:
            log.info("DB: Found 1 row with %s columns.", len(rows.keys()))

        # A final log statement clarifying what is returned
        log.debug("DB: Returning row(s) as type: %s.", type(rows).__name__)

        # The as_dict flag enables returning a dictionary instead of a Row object.
        if as_dict and fetchone:
            log.debug("DB: Returning Row as dict.")
            return dict(rows) if rows else None
        if as_dict:
            log.debug("DB: Returning rows as list of dicts.")
            dict_rows = [ {**row} for row in rows ]
            return dict_rows
        return rows

    def debug_db(self, db_return):
        # print(dbr.keys())
        print()
        for i in db_return:
            # print(i.keys())
            stringed = ""
            for j in i:
                stringed += "{}, ".format(j)
            print(stringed)
            print()
        return True
