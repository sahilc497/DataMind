import asyncpg
import logging
import json
from typing import List, Dict, Any, Union
from .base import BaseDatabase

logger = logging.getLogger(__name__)

class PostgresDatabase(BaseDatabase):
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(self.dsn)
                logger.info("Connected to PostgreSQL pool")
            except Exception as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Disconnected from PostgreSQL")

    async def list_databases(self) -> List[str]:
        query = "SELECT datname FROM pg_database WHERE datistemplate = false;"
        results = await self.pool.fetch(query)
        return [r['datname'] for r in results]

    async def list_tables(self, db_name: str = None) -> List[str]:
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        results = await self.pool.fetch(query)
        return [r['table_name'] for r in results]

    async def get_schema(self, db_name: str = None) -> Dict[str, Any]:
        query = """
        SELECT 
            table_name, 
            column_name, 
            data_type 
        FROM 
            information_schema.columns 
        WHERE 
            table_schema = 'public'
        ORDER BY 
            table_name, ordinal_position;
        """
        rows = await self.pool.fetch(query)
        schema = {"tables": []}
        tables = {}
        for row in rows:
            t_name = row['table_name']
            if t_name not in tables:
                tables[t_name] = {"name": t_name, "columns": []}
                schema["tables"].append(tables[t_name])
            tables[t_name]["columns"].append(row['column_name'])
        return schema

    async def execute_query(self, query: str) -> Union[str, List[Dict[str, Any]]]:
        try:
            if query.strip().lower().startswith("select") or query.strip().lower().startswith("with") or query.strip().lower().startswith("show"):
                results = await self.pool.fetch(query)
                return [dict(r) for r in results]
            else:
                status = await self.pool.execute(query)
                return status
        except Exception as e:
            logger.error(f"PostgreSQL query error: {e}")
            return f"Error: {str(e)}"

    async def explain_query(self, query: str) -> str:
        try:
            explain_query = f"EXPLAIN (FORMAT JSON) {query}"
            results = await self.pool.fetch(explain_query)
            return json.dumps(dict(results[0]), indent=2)
        except Exception as e:
            return f"Explain Error: {str(e)}"
