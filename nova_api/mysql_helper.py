import logging
import os
from typing import Any, List

import mysql.connector
from mysql.connector import Error, InterfaceError, DatabaseError


class MySQLHelper:

    def __init__(self, host=os.environ.get('DB_URL'),
                 user=os.environ.get('DB_USER'),
                 password=os.environ.get('DB_PASSWORD'),
                 database=os.environ.get('DB_NAME')):

        self.logger = logging.getLogger(__name__)

        if host is None:
            host = 'localhost'

        if user is None:
            user = 'root'

        if password is None:
            self.logger.warning("No password provided to database. Using "
                                "default insecure password 'root'")
            password = 'root'

        if database is None:
            database = "default"

        try:
            self.logger.info("Connecting to database %s at %s "
                             "with username %s", database, host, user)
            self.db_conn = mysql.connector.connect(host=str(host),
                                                   user=str(user),
                                                   passwd=str(password),
                                                   database=str(database))
            self.cursor = self.db_conn.cursor()
        except (InterfaceError, ValueError, DatabaseError) as err:
            self.logger.critical("Unable to connect to database!",
                                 exc_info=True)
            raise ConnectionError("\nSomething went wrong when connecting "
                                  "to mysql: {err}\n\n".format(err=err)) \
                from err

    def query(self, query: str, params: List = None) -> (int, int):
        try:
            self.logger.debug("Query to execute is %s, params %s",
                              query,
                              params)
            if params is not None:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            if (query.__contains__('INSERT')
                    or query.__contains__('UPDATE')
                    or query.__contains__('DELETE')):
                self.logger.debug("Committing query.")
                self.db_conn.commit()
            self.logger.debug("Row count %s and last row id %s",
                              self.cursor.rowcount,
                              self.cursor.lastrowid)
            return self.cursor.rowcount, self.cursor.lastrowid
        except Error as err:
            self.logger.critical("Unable to execute query in database!",
                                 exc_info=True)
            raise RuntimeError(
                "\nSomething went wrong with the query: {}\n\n".format(err)
            ) from err

    def get_results(self) -> List[Any]:
        try:
            results = self.cursor.fetchall()
            self.logger.debug("Got results from database: %s", results)
            return results if len(results) > 0 else None
        except Error as err:
            self.logger.critical("Unable to get query results!",
                                 exc_info=True)
            raise RuntimeError("\nSomething went wrong: {}\n\n".format(err)) \
                from err

    def close(self):
        self.logger.info("Closing connection to database!")
        self.cursor.close()
        self.db_conn.close()
