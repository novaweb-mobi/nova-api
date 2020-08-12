from Contact import Contact, Phone
from PhoneDAO import PhoneDAO

from nova_api import error_response, success_response, use_dao
from nova_api.generic_dao import GenericSQLDAO


@use_dao(PhoneDAO, "API Unavailable")
def probe(id_: str = None, dao: GenericSQLDAO = None):
    total, results = dao.get_all(length=1, offset=0, filters={"contact": id_})
    return success_response(message="API Ready",
                            data={"available": total})


@use_dao(PhoneDAO, "Unable to list phone")
def read(id_: str = None, length: int = 20, offset: int = 0,
         dao: GenericSQLDAO = None, **kwargs):
    for key, value in kwargs.items():
        kwargs[key] = value.split(',') \
            if len(value.split(',')) > 1 \
            else value
    kwargs['contact'] = id_
    total, results = dao.get_all(length=length, offset=offset,
                                 filters=kwargs if len(kwargs) > 0 else None)
    return success_response(message="List of phone",
                            data={"total": total, "results": [dict(result)
                                                              for result
                                                              in results]})


@use_dao(PhoneDAO, "Unable to retrieve phone")
def read_one(id_: str, phone_id: str, dao: GenericSQLDAO = None):
    result = dao.get(id_=phone_id)

    if result.contact.id_ != id_:
        result = None

    if not result:
        return success_response(status_code=404,
                                message="Phone not found in database",
                                data={"id_": id_})

    return success_response(message="Phone retrieved",
                            data={"Phone": dict(result)})


@use_dao(PhoneDAO, "Unable to create phone")
def create(id_: str, entity: dict, dao: GenericSQLDAO = None):
    entity_to_create = Phone(**entity)
    entity_to_create.contact = Contact(id_=id_)

    dao.create(entity=entity_to_create)

    return success_response(message="Phone created",
                            data={"Phone": dict(entity_to_create)})


@use_dao(PhoneDAO, "Unable to update phone")
def update(id_: str, phone_id: str, entity: dict, dao: GenericSQLDAO = None):
    entity_to_update = dao.get(phone_id)

    if entity_to_update.contact.id_ != id_:
        entity_to_update = None

    if not entity_to_update:
        return error_response(status_code=404,
                              message="Phone not found",
                              data={"id_": id_})

    entity_fields = dao.fields.keys()

    for key, value in entity.items():
        if key not in entity_fields:
            raise KeyError("{key} not in {entity}"
                           .format(key=key,
                                   entity=dao.return_class))

        entity_to_update.__dict__[key] = value

    dao.update(entity_to_update)

    return success_response(message="Phone updated",
                            data={"Phone": dict(entity_to_update)})


@use_dao(PhoneDAO, "Unable to delete phone")
def delete(id_: str, phone_id: str, dao: GenericSQLDAO):
    entity = dao.get(id_=phone_id)

    if entity.contact.id_ != id_:
        entity = None

    if not entity:
        return error_response(status_code=404,
                              message="Phone not found",
                              data={"id_": id_})

    dao.remove(entity)

    return success_response(message="Phone deleted",
                            data={"Phone": dict(entity)})
