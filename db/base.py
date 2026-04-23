from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

class BaseDatabase(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def list_databases(self) -> List[str]:
        pass

    @abstractmethod
    async def list_tables(self, db_name: str = None) -> List[str]:
        pass

    @abstractmethod
    async def get_schema(self, db_name: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def execute_query(self, query: str) -> Union[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    async def explain_query(self, query: str) -> str:
        pass
