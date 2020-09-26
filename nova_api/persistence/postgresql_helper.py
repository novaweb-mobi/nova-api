import logging
import os
from typing import Any, List

import psycopg2
from psycopg2._psycopg import DatabaseError, Error, InterfaceError, \
    ProgrammingError
from psycopg2.pool import PoolError

from nova_api.persistence.postgresql_pool import PostgreSQLPool


class PostgreSQLHelper:

    def __init__(self, host: str = os.environ.get('DB_URL'),
                 user: str = os.environ.get('DB_USER'),
                 password: str = os.environ.get('DB_PASSWORD'),
                 database: str = os.environ.get('DB_NAME'),
                 pooled: bool = True,
                 database_args: dict = None):

        self.logger = logging.getLogger(__name__)

        self.host = str(host) if host is not None else 'localhost'
        self.user = str(user) if user is not None else 'root'
        self.database = str(database) if database is not None else 'default'
        if password is None:
            self.logger.warning("No password provided to database. Using "
                                "default insecure password 'root'")
            password = 'root'

        self.database_args = database_args \
            if database_args is not None else dict()

        self.pooled = pooled

        try:
            self.logger.info("Connecting to database %s at %s "
                             "with username %s. Pooled: %s. Extra args: %s",
                             database, host, user, pooled, database_args)
            if self.pooled:
                self.db_conn = PostgreSQLPool.get_instance(
                    host=self.host, user=self.user,
                    password=str(password),
                    database=self.database,
                    database_args=self.database_args).getconn(key=id(self))
            else:
                self.db_conn = psycopg2.connect(host=self.host,
                                                user=self.user,
                                                password=str(password),
                                                database=self.database,
                                                **self.database_args)
            self.cursor = self.db_conn.cursor()
        except (InterfaceError, ValueError, DatabaseError,
                PoolError, ProgrammingError) as err:
            self.logger.critical("Unable to connect to database!",
                                 exc_info=True)
            raise ConnectionError("\nSomething went wrong when connecting "
                                  "to postgresql: {err}\n\n".format(err=err)) \
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
        if self.pooled:
            PostgreSQLPool.get_instance(
                host=self.host, user=self.user,
                database=self.database,
                database_args=self.database_args).putconn(self.db_conn,
                                                          key=id(self))
        else:
            self.db_conn.close()
