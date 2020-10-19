import sys
import os
import psycopg2
from psycopg2._psycopg import Error

print(os.environ.get("DB_URL"))

db_conn = None

try:
     db_conn = psycopg2.connect(host=os.environ.get("DB_URL"),
                                user="root",
                                password="root",
                                database="default")
except Error as err:
    print('Error:', err)
    sys.exit(-1)
finally:
    if db_conn is not None:
        db_conn.close()
sys.exit(0)

