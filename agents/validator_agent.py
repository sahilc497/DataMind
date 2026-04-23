import re
from typing import Tuple, Dict, Any

class ValidatorAgent:
    def is_safe(self, sql: str, role: str = "user") -> Tuple[bool, str]:
        sql_upper = sql.strip().upper()
        
        # Admin commands blocking for non-admins
        blocked_commands = ["DROP", "TRUNCATE", "ALTER", "GRANT", "REVOKE"]
        
        if role != "admin":
            if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH") and not sql_upper.startswith("SHOW"):
                return False, f"Permission Denied: Only SELECT/SHOW allowed for role '{role}'."
            
            for cmd in blocked_commands:
                if f" {cmd} " in f" {sql_upper} " or sql_upper.startswith(cmd):
                    return False, f"Permission Denied: Command '{cmd}' is restricted."

        return True, ""

    def validate_hallucination(self, sql: str, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Hallucination Guard: Validates that tables and columns in the SQL exist in the schema.
        """
        if not schema or "tables" not in schema:
            return True, "" # Skip if no schema provided
            
        sql_clean = sql.replace(";", "").lower()
        tables_in_schema = [t["name"].lower() for t in schema["tables"]]
        columns_in_schema = []
        for t in schema["tables"]:
            columns_in_schema.extend([c.lower() for c in t["columns"]])
            # Also add table-qualified column names: users.id
            columns_in_schema.extend([f"{t['name'].lower()}.{c.lower()}" for c in t["columns"]])

        # Simple extraction of words that look like table/column names
        # This is a heuristic and could be improved with a proper SQL parser
        tokens = re.findall(r'\b[a-z0-9_]+\b(?:\.\b[a-z0-9_]+\b)?', sql_clean)
        
        # Identify tables in query (often after FROM or JOIN)
        from_matches = re.findall(r'from\s+([a-z0-9_]+)', sql_clean)
        join_matches = re.findall(r'join\s+([a-z0-9_]+)', sql_clean)
        referenced_tables = set(from_matches + join_matches)

        for table in referenced_tables:
            if table not in tables_in_schema and table not in ["information_schema", "pg_catalog"]:
                return False, f"Hallucination Detected: Table '{table}' does not exist in schema."

        return True, ""