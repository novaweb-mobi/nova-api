import connexion
from flask_cors import CORS
from os import environ
from nova_api import create_api_files

print("imports")

debug = environ.get('DEBUG') or '0'
if debug == '0':
    debug = False
elif debug == '1':
    debug = True

print("reading port")
port = int(environ.get('PORT')) if environ.get('PORT') else 80

print("reading Entities: ", end='')
ENTITIES = environ.get('ENTITIES') or ''
ENTITIES = [entity.strip() for entity in ENTITIES.split(',')]
print(ENTITIES)

APIS = environ.get('APIS') or ''
APIS = [api.strip() for api in APIS.split(',')]
print("reading Apis: ", APIS)

VERSION = environ.get('VERSION') or '1'

for entity in ENTITIES:
    if entity == '':
        continue
    dao_class = entity + 'DAO'
    mod = __import__(dao_class, fromlist=[dao_class])
    entity_dao = getattr(mod, dao_class)
    mod = __import__(entity, fromlist=[entity])
    entity_class = getattr(mod, entity)
    create_api_files(entity_class, entity_dao, VERSION)
    dao = entity_dao()
    dao.create_table_if_not_exists()
    print("Done creating table and api files for {ent}".format(ent=entity))

# Create the application instance
app = connexion.App(__name__, specification_dir=".")
CORS(app.app)
print("App and Cors")

for entity in ENTITIES:
    if entity == '':
        continue
    dao_class = entity + 'DAO'
    mod = __import__(dao_class, fromlist=[dao_class])
    entity_dao = getattr(mod, dao_class)
    mod = __import__(entity, fromlist=[entity])
    entity_class = getattr(mod, entity)
    create_api_files(entity_class, entity_dao, VERSION)
    dao = entity_dao()
    dao.create_table_if_not_exists()
    print("Done creating table and api files for {ent}".format(ent=entity))
    app.add_api(entity.lower() + "_api.yml")
    print("Done adding api for {ent}".format(ent=entity))

for api in APIS:
    if api == '':
        continue
    app.add_api(api)
    print("Done adding api {api}".format(api=api))
print("Full setup")

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=debug, port=port)
