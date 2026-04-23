import re

class RBACManager:
    # Role definitions
    ROLES = {
        'admin': {
            'allowed_tables': '*',
            'allowed_columns': '*',
            'can_execute_write': True
        },
        'analyst': {
            'allowed_tables': ['users', 'orders', 'products', 'categories'],
            'allowed_columns': '*',
            'can_execute_write': False
        },
        'viewer': {
            'allowed_tables': ['products', 'categories'],
            'allowed_columns': ['name', 'description', 'price', 'category_id'],
            'can_execute_write': False
        }
    }

    @staticmethod
    def validate_access(role, sql):
        """
        Validates if the role has access to the tables/columns in the SQL.
        """
        role_config = RBACManager.ROLES.get(role, RBACManager.ROLES['viewer'])
        sql_lower = sql.lower()

        # Check for write operations if not allowed
        if not role_config['can_execute_write']:
            if any(cmd in sql_lower for cmd in ['insert', 'update', 'delete', 'drop', 'truncate', 'alter']):
                return False, f"Role '{role}' is not authorized to perform write operations."

        # Simple table extraction (very basic, for demo)
        # In production, use a SQL parser like sqlglot or sqlparse
        tables = re.findall(r'from\s+([a-zA-Z0-9_]+)', sql_lower)
        tables += re.findall(r'join\s+([a-zA-Z0-9_]+)', sql_lower)
        
        if role_config['allowed_tables'] != '*':
            for table in tables:
                if table not in role_config['allowed_tables']:
                    return False, f"Role '{role}' is not authorized to access table '{table}'."

        return True, ""

    @staticmethod
    def mask_data(role, result):
        """
        Masks sensitive data based on role.
        """
        if role == 'admin':
            return result
        
        if not isinstance(result, list):
            return result

        masked_result = []
        for row in result:
            new_row = dict(row)
            for key in new_row:
                # Mask emails
                if 'email' in key.lower() and isinstance(new_row[key], str):
                    email = new_row[key]
                    if '@' in email:
                        name, domain = email.split('@')
                        new_row[key] = f"{name[0]}***@{domain}"
                
                # Mask phones
                if 'phone' in key.lower() and isinstance(new_row[key], str):
                    phone = new_row[key]
                    new_row[key] = f"****{phone[-4:]}" if len(phone) >= 4 else "****"
            
            masked_result.append(new_row)
        
        return masked_result
