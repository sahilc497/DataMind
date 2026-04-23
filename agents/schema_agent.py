import logging
from typing import Dict, Any
from db.factory import DatabaseFactory
from services.normalization import SchemaNormalizer

logger = logging.getLogger(__name__)

class SchemaTools:
    @staticmethod
    async def get_normalized_schema(db_type: str, db_name: str) -> Dict[str, Any]:
        """Extracts and normalizes the schema for the specified database."""
        try:
            db = await DatabaseFactory.get_db(db_type, db_name)
            raw_schema = await db.get_schema()
            return raw_schema
        except Exception as e:
            logger.error(f"Schema Extraction Error: {e}")
            return {"tables": []}

    @staticmethod
    def format_for_llm(raw_schema: Dict[str, Any]) -> str:
        return SchemaNormalizer.normalize_schema(raw_schema)

from crewai import Agent
from config import settings

class SchemaAgent:
    def __init__(self):
        self.llm = f"mistral/{settings.MISTRAL_MODEL}"

    def get_agent(self):
        return Agent(
            role='Schema Architect',
            goal='Extract and understand the database schema and relationships.',
            backstory='You are an expert in database structures.',
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
