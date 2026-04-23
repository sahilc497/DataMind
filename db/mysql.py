import mysql.connector
import logging
import asyncio
import json
from typing import List, Dict, Any, Union
from .base import BaseDatabase

logger = logging.getLogger(__name__)

class MySQLDatabase(BaseDatabase):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None

    async def connect(self):
        def _connect():
            return mysql.connector.connect(**self.config)
        
        if not self.connection:
            try:
                self.connection = await asyncio.to_thread(_connect)
                logger.info("Connected to MySQL (XAMPP)")
            except Exception as e:
                logger.error(f"MySQL connection failed: {e}")
                raise

    async def disconnect(self):
        if self.connection:
            await asyncio.to_thread(self.connection.close)
            self.connection = None
            logger.info("Disconnected from MySQL")

    async def list_databases(self) -> List[str]:
        def _list():
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES")
            dbs = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return dbs
        return await asyncio.to_thread(_list)

    async def list_tables(self, db_name: str = None) -> List[str]:
        def _list():
            cursor = self.connection.cursor()
            if db_name: cursor.execute(f"USE {db_name}")
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        return await asyncio.to_thread(_list)

    async def get_schema(self, db_name: str = None) -> Dict[str, Any]:
        def _get():
            cursor = self.connection.cursor(dictionary=True)
            if db_name: cursor.execute(f"USE {db_name}")
            query = """
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s
            """
            db = db_name or self.config.get('database')
            cursor.execute(query, (db,))
            rows = cursor.fetchall()
            schema = {"tables": []}
            tables = {}
            for row in rows:
                t_name = row['TABLE_NAME']
                if t_name not in tables:
                    tables[t_name] = {"name": t_name, "columns": []}
                    schema["tables"].append(tables[t_name])
                tables[t_name]["columns"].append(row['COLUMN_NAME'])
            cursor.close()
            return schema
        return await asyncio.to_thread(_get)

    async def execute_query(self, query: str) -> Union[str, List[Dict[str, Any]]]:
        def _execute():
            cursor = self.connection.cursor(dictionary=True)
            try:
                cursor.execute(query)
                if query.strip().lower().startswith("select") or query.strip().lower().startswith("show") or query.strip().lower().startswith("describe"):
                    results = cursor.fetchall()
                    return results
                else:
                    self.connection.commit()
                    return f"Rows affected: {cursor.rowcount}"
            except Exception as e:
                return f"Error: {str(e)}"
            finally:
                cursor.close()
        return await asyncio.to_thread(_execute)

    async def explain_query(self, query: str) -> str:
        def _explain():
            cursor = self.connection.cursor(dictionary=True)
            try:
                cursor.execute(f"EXPLAIN {query}")
                results = cursor.fetchall()
                return json.dumps(results, indent=2)
            except Exception as e:
                return f"Explain Error: {str(e)}"
            finally:
                cursor.close()
        return await asyncio.to_thread(_explain)
