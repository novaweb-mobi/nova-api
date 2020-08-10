import sys
import os
import mysql.connector


print(os.environ.get("DB_URL"))

try:
     db_conn = mysql.connector.connect(host=os.environ.get("DB_URL"),
                                       user="root",
                                       passwd="root",
                                       database="default")
except mysql.connector.Error as err:
    print('Error:', err)
    sys.exit(-1)
sys.exit(0)

