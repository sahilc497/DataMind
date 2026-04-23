import re

def validate_db_name(db_name: str) -> bool:
    """Validate db_name (regex: only letters, numbers, underscore)"""
    return bool(re.match(r'^[a-zA-Z0-9_]+$', db_name))

def format_schema(schema_data: list) -> str:
    """Convert schema data into LLM-friendly format."""
    tables = {}
    for row in schema_data:
        table_name = row['table_name']
        column_name = row['column_name']
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append(column_name)
    
    formatted = "Tables:\n"
    for table, cols in tables.items():
        formatted += f"{table}({', '.join(cols)})\n"
    return formatted

def format_relationships(rel_data: list) -> str:
    """Format relationships for LLM."""
    if not rel_data:
        return "Relationships: None detected."
    
    formatted = "Relationships:\n"
    for row in rel_data:
        formatted += f"{row['table_name']}.{row['column_name']} -> {row['foreign_table_name']}.{row['foreign_column_name']}\n"
    return formatted
