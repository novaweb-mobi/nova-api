import os
from typing import Any, List

import mysql.connector
from mysql.connector import InterfaceError, Error


class MySQLHelper:

    def __init__(self, host=os.environ.get('DB_URL'),
                 user=os.environ.get('DB_USER'),
                 password=os.environ.get('DB_PASSWORD'),
                 database=os.environ.get('DB_NAME')):
        if host is None:
            host = 'localhost'

        if user is None:
            user = 'root'

        if password is None:
            password = 'root'

        if database is None:
            database = "default"

        try:
            self.db_conn = mysql.connector.connect(host=str(host),
                                                   user=str(user),
                                                   passwd=str(password),
                                                   database=str(database))
            self.cursor = self.db_conn.cursor()
        except (InterfaceError, ValueError) as err:
            raise ConnectionError("\nSomething went wrong when connecting "
                                  "to mysql: {err}\n\n".format(err=err))

    def query(self, query: str, params: List = None) -> (int, int):
        try:
            if params is not None:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            if (query.__contains__('INSERT')
                    or query.__contains__('UPDATE')
                    or query.__contains__('DELETE')):
                self.db_conn.commit()
            return self.cursor.rowcount, self.cursor.lastrowid
        except Error as err:
            raise RuntimeError(
                "\nSomething went wrong with the query: {}\n\n".format(err)
            )

    def get_results(self) -> List[Any]:
        try:
            results = self.cursor.fetchall()
            return results if len(results) > 0 else None
        except Error as err:
            raise RuntimeError("\nSomething went wrong: {}\n\n".format(err))

    def close(self):
        self.cursor.close()
        self.db_conn.close()
