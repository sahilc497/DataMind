from typing import Dict, Any, List

class SchemaNormalizer:
    @staticmethod
    def normalize_schema(raw_schema: Dict[str, Any]) -> str:
        """
        Converts DB-specific schema metadata into a unified string format for the LLM.
        """
        unified_format = "### DATABASE SCHEMA ###\n\n"
        for table in raw_schema.get("tables", []):
            table_name = table.get("name")
            columns = ", ".join(table.get("columns", []))
            unified_format += f"Table: {table_name}\nColumns: [{columns}]\n\n"
        
        return unified_format

    @staticmethod
    def get_schema_hash(raw_schema: Dict[str, Any]) -> str:
        import hashlib
        import json
        return hashlib.md5(json.dumps(raw_schema, sort_keys=True).encode()).hexdigest()
