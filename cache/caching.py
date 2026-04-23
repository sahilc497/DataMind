import hashlib
from cachetools import TTLCache
from config import settings

class QueryCache:
    # NL Query -> SQL
    _sql_cache = TTLCache(maxsize=1000, ttl=settings.CACHE_TTL)
    # SQL -> Result (Serialized)
    _result_cache = TTLCache(maxsize=100, ttl=settings.CACHE_TTL)

    @classmethod
    def get_sql(cls, nl_query: str, db_type: str, schema_hash: str) -> str:
        key = f"{nl_query}:{db_type}:{schema_hash}"
        return cls._sql_cache.get(key)

    @classmethod
    def set_sql(cls, nl_query: str, db_type: str, schema_hash: str, sql: str):
        key = f"{nl_query}:{db_type}:{schema_hash}"
        cls._sql_cache[key] = sql

    @classmethod
    def get_result(cls, sql: str, db_name: str) -> any:
        key = hashlib.md5(f"{sql}:{db_name}".encode()).hexdigest()
        return cls._result_cache.get(key)

    @classmethod
    def set_result(cls, sql: str, db_name: str, result: any):
        key = hashlib.md5(f"{sql}:{db_name}".encode()).hexdigest()
        cls._result_cache[key] = result
