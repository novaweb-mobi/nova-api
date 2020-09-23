from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import ClassVar, Dict

from mysql.connector import pooling


@dataclass
class MySQLPool:
    instances: ClassVar[Dict[MySQLPool]] = field(default={})

    @classmethod
    def get_instance(cls, host: str = os.environ.get('DB_URL'),
                     user: str = os.environ.get('DB_USER'),
                     password: str = os.environ.get('DB_PASSWORD'),
                     database: str = os.environ.get('DB_NAME'),
                     size: int = os.environ.get('MYSQL_POOL_SIZE', 5)) \
            -> pooling.MySQLConnectionPool:
        """
        Get an instance of a database connection pool.

        This checks the existence of a connection pool with the specified \
        server and database and return the existent connection or a new one \
        if it doesn't exists

        :param host: The database URL to connect
        :param user: The database user to use
        :param password: The user password if necessary
        :param database: The database name to use
        :param size: Number of connections to keep in the pool. \
        Defaults to 5.
        :return: The connection pool instance
        """
        instance = cls.instances.get(user + "@" + host + ":" + database, None)

        if instance:
            return instance

        instance = pooling.MySQLConnectionPool(
            pool_name=user + "@" + host + ":" + database,
            pool_size=size,
            pool_reset_session=True,
            host=host,
            database=database,
            user=user,
            password=password)
        cls.instances[user + "@" + host + ":" + database] = instance

        return instance
