import connexion
from flask_cors import CORS

import nova_api

nova_api.logger.info("Test")

debug = True
port = 8080
version = "1"

# Import entity and dao
mod = __import__("ContactDAO", fromlist=["ContactDAO"])
contact_dao = getattr(mod, "ContactDAO")
mod = __import__("PhoneDAO", fromlist=["PhoneDAO"])
phone_dao = getattr(mod, "PhoneDAO")

# Create the table in the database
dao = contact_dao()
dao.create_table_if_not_exists()
dao.close()
dao = phone_dao()
dao.create_table_if_not_exists()
dao.close()

# Create the application instance
app = connexion.App(__name__, specification_dir=".")
CORS(app.app)

# Add the api to the flask server
app.add_api("contact_api.yml")
print("Done adding api for {ent}".format(ent="Contact"))

if __name__ == '__main__':
    app.run(debug=debug, port=port)
