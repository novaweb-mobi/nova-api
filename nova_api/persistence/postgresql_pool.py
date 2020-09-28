from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import ClassVar, Dict

from psycopg2 import pool


@dataclass
class PostgreSQLPool:
    instances: ClassVar[Dict[PostgreSQLPool]] = field(default={})
    logger: ClassVar[logging.Logger] = field(
        default=logging.getLogger(__name__))

    @classmethod
    def get_instance(cls, host: str = os.environ.get('DB_URL'),
                     user: str = os.environ.get('DB_USER'),
                     password: str = os.environ.get('DB_PASSWORD'),
                     database: str = os.environ.get('DB_NAME'),
                     size: int = os.environ.get('MYSQL_POOL_SIZE', 5),
                     database_args: dict = None) \
            -> pool.SimpleConnectionPool:
        """
        Get an instance of a database connection pool.

        This checks the existence of a connection pool with the specified \
        server and database and return the existent connection or a new one \
        if it doesn't exists. Any database args that should be used have to \
        be passed at the first call to create a pool. `database_args` are \
        not verified at every call and are not used to compare the required \
        and available pools.

        :param host: The database URL to connect
        :param user: The database user to use
        :param password: The user password if necessary
        :param database: The database name to use
        :param size: Number of connections to keep in the pool. \
        Defaults to 5.
        :param database_args: Extra options to pass to database connection.
        :return: The connection pool instance
        """
        if database_args is None:
            database_args = dict()

        if database_args.get("minconn", None) is None:
            database_args.update({"minconn": size})

        pool_name = user + "_" + host + "-" + database
        # This guarantees
        pool_name = re.sub("[^a-zA-Z0-9._*$#-]", "_", pool_name)
        if len(pool_name) > 64:
            pool_name = pool_name[:64]
        instance = cls.instances.get(pool_name, None)

        cls.logger.info("Requested connection from pool: %s", pool_name)

        if instance:
            cls.logger.info("Pool already connected: %s. ", pool_name)
            return instance

        cls.logger.info("Pool not connected, instantiating: %s", pool_name)
        instance = pool.SimpleConnectionPool(
            maxconn=size,
            host=host,
            database=database,
            user=user,
            password=password,
            **database_args)
        cls.instances[pool_name] = instance

        cls.logger.info("Pool instantiated: %s", pool_name)
        return instance
