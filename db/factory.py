from typing import Dict, Any
from .base import BaseDatabase
from .postgres import PostgresDatabase
from .mysql import MySQLDatabase
from config import settings

class DatabaseFactory:
    _instances: Dict[str, BaseDatabase] = {}

    @classmethod
    async def get_db(cls, db_type: str, db_name: str = None) -> BaseDatabase:
        key = f"{db_type}:{db_name}"
        if key not in cls._instances:
            if db_type == "postgres":
                dsn = settings.DATABASE_URL
                if db_name:
                    base = dsn.rsplit('/', 1)[0]
                    dsn = f"{base}/{db_name}"
                db = PostgresDatabase(dsn)
            elif db_type == "mysql":
                config = {
                    "host": settings.MYSQL_HOST,
                    "port": settings.MYSQL_PORT,
                    "user": settings.MYSQL_USER,
                    "password": settings.MYSQL_PASSWORD,
                    "database": db_name or settings.MYSQL_DATABASE
                }
                db = MySQLDatabase(config)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            await db.connect()
            cls._instances[key] = db
        
        return cls._instances[key]

    @classmethod
    async def close_all(cls):
        for db in cls._instances.values():
            await db.disconnect()
        cls._instances = {}
