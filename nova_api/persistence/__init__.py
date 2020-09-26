import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from nova_api.entity import Entity


class PersistenceHelper(ABC):
    ALLOWED_COMPARATORS: List[str]
    TYPE_MAPPING: Dict[str, str]
    CREATE_QUERY: str
    COLUMN: str
    SELECT_QUERY: str
    FILTERS: str
    FILTER: str
    DELETE_QUERY: str
    INSERT_QUERY: str
    UPDATE_QUERY: str
    QUERY_TOTAL_COLUMN: str

    @abstractmethod
    def __init__(self, host: str, user: str, password: str,
                 database: str, pooled: bool, database_args: dict):
        self.cursor = None
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def query(self, query: str, params: List) -> (int, int):
        pass

    def get_results(self) -> List[Any]:
        try:
            results = self.cursor.fetchall()
            self.logger.debug("Got results from database: %s", results)
            return results if len(results) > 0 else None
        except Exception as err:
            self.logger.critical("Unable to get query results!",
                                 exc_info=True)
            raise RuntimeError("\nSomething went wrong: {}\n\n".format(err)) \
                from err

    @abstractmethod
    def close(self) -> None:
        pass

    def predict_db_type(self, cls_to_predict) -> str:
        """
        Returns the predicted db type for a class.

        :param cls_to_predict: Class to predict the db type.
        :return: The db type.
        """
        print(issubclass(cls_to_predict, Entity))
        print(cls_to_predict)
        print(cls_to_predict.__mro__)
        if issubclass(cls_to_predict, Entity):
            return "CHAR(32)"
        return self.TYPE_MAPPING.get(cls_to_predict.__name__) \
            or "CHAR(100)"
