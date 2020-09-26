from abc import ABC, abstractmethod
from typing import Any, Dict, List


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
                 database: str, pooled: bool, database_args: dict ):
        pass

    @abstractmethod
    def query(self, query: str, params: List) -> (int, int):
        pass

    @abstractmethod
    def get_results(self) -> List[Any]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
