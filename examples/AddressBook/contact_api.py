from Contact import Contact
from ContactDAO import ContactDAO

from nova_api import error_response, success_response, use_dao
from nova_api.dao.generic_sql_dao import GenericSQLDAO


@use_dao(ContactDAO, "API Unavailable")
def probe(dao: GenericSQLDAO = None):
    total, results = dao.get_all(length=1, offset=0, filters=None)
    return success_response(message="API Ready",
                            data={"available": total})


@use_dao(ContactDAO, "Unable to list contact")
def read(length: int = 20, offset: int = 0,
         dao: GenericSQLDAO = None, **kwargs):
    for key, value in kwargs.items():
        kwargs[key] = value.split(',') \
            if len(value.split(',')) > 1 \
            else value
    total, results = dao.get_all(length=length, offset=offset,
                                 filters=kwargs if len(kwargs) > 0 else None)
    return success_response(message="List of contact",
                            data={"total": total, "results": [dict(result)
                                                              for result
                                                              in results]})


@use_dao(ContactDAO, "Unable to retrieve contact")
def read_one(id_: str, dao: GenericSQLDAO = None):
    result = dao.get(id_=id_)

    if not result:
        return success_response(status_code=404,
                                message="Contact not found in database",
                                data={"id_": id_})

    return success_response(message="Contact retrieved",
                            data={"Contact": dict(result)})


@use_dao(ContactDAO, "Unable to create contact")
def create(entity: dict, dao: GenericSQLDAO = None):
    entity_to_create = Contact(**entity)

    dao.create(entity=entity_to_create)

    return success_response(message="Contact created",
                            data={"Contact": dict(entity_to_create)})


@use_dao(ContactDAO, "Unable to update contact")
def update(id_: str, entity: dict, dao: GenericSQLDAO = None):
    entity_to_update = dao.get(id_)

    if not entity_to_update:
        return error_response(status_code=404,
                              message="Contact not found",
                              data={"id_": id_})

    entity_fields = dao.fields.keys()

    for key, value in entity.items():
        if key not in entity_fields:
            raise KeyError("{key} not in {entity}"
                           .format(key=key,
                                   entity=dao.return_class))

        entity_to_update.__dict__[key] = value

    dao.update(entity_to_update)

    return success_response(message="Contact updated",
                            data={"Contact": dict(entity_to_update)})


@use_dao(ContactDAO, "Unable to delete contact")
def delete(id_: str, dao: GenericSQLDAO):
    entity = dao.get(id_=id_)

    if not entity:
        return error_response(status_code=404,
                              message="Contact not found",
                              data={"id_": id_})

    dao.remove(entity)

    return success_response(message="Contact deleted",
                            data={"Contact": dict(entity)})
