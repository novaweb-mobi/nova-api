import os
import sys

import pymongo

print(os.environ.get("DB_URL"))

db_conn = None

try:
    db_conn = pymongo.MongoClient(os.environ.get("DB_URL"),
                                  serverSelectionTimeoutMS=5000)
    db_conn.server_info()
except Exception as err:
    print('Error:', err)
    sys.exit(-1)
finally:
    if db_conn is not None:
        db_conn.close()
sys.exit(0)
