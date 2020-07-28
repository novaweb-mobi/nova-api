from GenericSQLDAO import GenericSQLDAO
from nova_api import error_response, success_response, use_dao


@use_dao({DAO_CLASS}, "API Unavailable")
def probe(dao: GenericSQLDAO = None):
    total, results = dao.get_all(length=1, offset=0, filters=None)
    return success_response(message="API Ready",
                            data={"available": total})


@use_dao({DAO_CLASS}, "Unable to list {entity_lower}")
def read(length: int = 20, offset: int = 0,
         filters: dict = None, dao: GenericSQLDAO = None):
    total, results = dao.get_all(length=length, offset=offset,
                                 filters=filters)
    return success_response(message="List of {entity_lower}",
                            data={"total": total, "results": [dict(result)
                                                              for result
                                                              in results]})


@use_dao({DAO_CLASS}, "Unable to retrieve {entity_lower}")
def read_one(id_: str, dao: GenericSQLDAO = None):
    result = dao.get(id_=id_)

    if not result:
        return success_response(status_code=404,
                                message="{entity} not found in db",
                                data={"id_": id_})

    return success_response(message="{entity} retrieved",
                            data={"{entity}": dict(result)})


@use_dao({DAO_CLASS}, "Unable to create {entity_lower}")
def create(entity: dict, dao: GenericSQLDAO = None):
    entity_to_create = {CLASS}(**entity)

    dao.create(entity=entity_to_create)

    return success_response(message="{entity} created",
                            data={"{entity}": dict(entity_to_create)})


@use_dao({DAO_CLASS}, "Unable to update {entity_lower}")
def update(id_: str, entity: dict, dao: GenericSQLDAO = None):
    entity_to_update = dao.get(id_)]

    if not entity:
        return error_response(status_code=404,
                              message="{entity} not found",
                              data={"id_": id_})

    entity_fields = dao.FIELDS.keys()

    for key, value in entity.items():
        if key not in entity_fields:
            raise KeyError("{key} not in {entity_}"
                           .format(key=key,
                                   entity_=dao.RETURN_CLASS))

        entity_to_update.__dict__[key] = value

    dao.update(entity_to_update)

    return success_response(message="{entity} updated",
                            data={"{entity}": dict(entity_to_update)})


@use_dao({DAO_CLASS}, "Unable to delete {entity_lower}")
def delete(id_: str, dao: GenericSQLDAO):
    entity = dao.get(id_=id_)

    if not entity:
        return error_response(status_code=404,
                              message="{entity} not found",
                              data={"id_": id_})

    dao.remove(entity)

    return success_response(message="{entity} deleted",
                            data={"{entity}": dict(entity)})
