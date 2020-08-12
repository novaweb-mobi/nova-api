import connexion
from flask_cors import CORS
from os import environ
from nova_api import create_api_files


debug = False
port = 8080
entity = "Contact"
dao_class = entity + 'DAO'
version = "1"

# Import entity and dao
mod = __import__(dao_class, fromlist=[dao_class])
entity_dao = getattr(mod, dao_class)
mod = __import__(entity, fromlist=[entity])
entity_class = getattr(mod, entity)

# Generate api documentation and implementation
create_api_files(entity_class, entity_dao, version)

# Create the table in the database
dao = entity_dao()
dao.create_table_if_not_exists()

# Create the application instance
app = connexion.App(__name__, specification_dir=".")
CORS(app.app)

# Add the api to the flask server
app.add_api(entity.lower() + "_api.yml")
print("Done adding api for {ent}".format(ent=entity))

if __name__ == '__main__':
    app.run(debug=debug, port=port)
