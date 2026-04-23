import json
import logging
from typing import Dict, Any, List
from db.factory import DatabaseFactory

logger = logging.getLogger(__name__)

class ExecutionTools:
    @staticmethod
    async def execute_sql(sql: str, db_type: str, db_name: str):
        """Executes a SQL query against the specified database and returns the result."""
        try:
            db = await DatabaseFactory.get_db(db_type, db_name)
            result = await db.execute_query(sql)
            
            if isinstance(result, list):
                if not result:
                    return "Query executed successfully. No rows returned."
                return f"DATA_JSON: {json.dumps(result, default=str)}"
            
            return f"Operation completed successfully: {result}"
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return f"Error executing SQL: {str(e)}"

    @staticmethod
    async def get_explanation(sql: str, db_type: str, db_name: str):
        """Retrieves the execution plan for a SQL query."""
        try:
            db = await DatabaseFactory.get_db(db_type, db_name)
            return await db.explain_query(sql)
        except Exception as e:
            return f"Error explaining SQL: {str(e)}"

from crewai import Agent
from config import settings

class ExecutorAgent:
    def __init__(self):
        self.llm = f"mistral/{settings.MISTRAL_MODEL}"

    def get_agent(self):
        return Agent(
            role='SQL Executor',
            goal='Execute SQL queries and retrieve results.',
            backstory='You are a precise database administrator.',
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
