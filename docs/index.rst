Welcome to NovaAPI's documentation!
***********************************

Getting Started
===============

To install NovaAPI and its dependencies, you can use `pip` as follows:

``pip install NovaAPI``

First example
-------------

As our first example, we'll create a contact API which could be used to create an address book.
We need to create two files: Contact.py_ and ContactDAO.py_.

Contact.py
^^^^^^^^^^

In this file, we describe our entity, that is, our contact. We include all information
we want to add to the database. Beside our custom defined fields, as it inherits from
Entity we also have an UUID, the creation datetime and the last
modified datetime automatically generated.

In this example, we use the "type" key in the metadata to gain control over how our data
is going to be stored in the database. As our attributes are strings, they would be
`VARCHAR(100)` if no type was informed. ::

    from dataclasses import dataclass, field

    from nova_api.entity import Entity

    @dataclass
    class Contact(Entity):
        first_name: str = field(default=None, metadata={"type":"VARCHAR(45)"})
        last_name: str = ''
        telephone_number: str = field(default=None, metadata={"type":"VARCHAR(15)"})
        email: str = field(default=None, metadata={"type":"VARCHAR(255)"})

ContactDAO.py
^^^^^^^^^^^^^

In out ContactDAO, we only need to inherit from GenericSQLDAO and assign our return_class
in the init method. ::

    from nova_api.dao.generic_sql_dao import GenericSQLDAO

    from Contact import Contact


    class ContactDAO(GenericSQLDAO):
        def __init__(self, database_type=None, **kwargs):
            super(ContactDAO, self).__init__(database_type=database_type,
                                             return_class=Contact, **kwargs)


Starting a server for this example locally
------------------------------------------

If we want to run this example through a local flask server, we can use the following
server.py_ file. It will generate the api files and start the server at port 8080. You
also need a database running at localhost with a root user with password root.

server.py
^^^^^^^^^
::

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

After creating the server.py file, we can start it with the following command::

    $ python server.py
    ...
    Done adding api for Contact
     * Serving Flask app "server" (lazy loading)
     * Environment: production
       WARNING: This is a development server. Do not use it in a production deployment.
       Use a production WSGI server instead.
     * Debug mode: off
     * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)

Next, we can navigate to `<localhost:8080/v1/contact/ui>`_ to see the live swagger documentation.

And you're all set to start using your contact api!

Deploy
------

When deploying to production, you should always use a production grade server(that's not flask)
like uWSGI or NGINX. If you use Kubernetes or docker in your production environment, you can use
our docker image available at the
`NovaAPI repository <https://github.com/novaweb-mobi/nova-api/packages>`_.

You can create your Dockerfile as the following example, with sets up an API for User::

    FROM docker.pkg.github.com/novaweb-mobi/connexion-api-docker/novaapi:0.2.0-a.1
    COPY User.py .
    COPY UserDAO.py .
    ENV PORT 8080
    ENV ENTITIES User
    ENV DB_URL 172.18.0.2
    ENV DB_USER root
    ENV DB_PASSWORD root
    ENV DB_NAME default

More Information
================

.. toctree::
   :maxdepth: 2

   novaapi
   entity
   create_entity
   auth
   license