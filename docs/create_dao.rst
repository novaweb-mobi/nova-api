Creating your DAO Class
***********************

To read the full documentation on the DAO, refer to
:doc:`dao`.

Quick Start
===========

Before creating your DAO class, you should've created an Entity,
if you haven't, please check :doc:`create_entity` before proceeding.

`What the hell is a DAO class? <https://en.wikipedia.org/wiki/Data_access_object>`_

First, create a file named after your entity with DAO in the end. For
example, if your entity is called `Contact`, your DAO should be named `ContactDAO`

Next, add the necessary imports(this example considers that the `Contact`
entity is in the same folder): ::

    from nova_api.dao.generic_sql_dao import GenericSQLDAO

    from Contact import Contact

