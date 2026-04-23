from crewai import Agent
from config import settings

class SQLAgent:
    def __init__(self):
        self.llm = f'mistral/{settings.MISTRAL_MODEL}'

    def get_agent(self, db_type: str = "postgres"):
        db_flavor = "PostgreSQL" if db_type == "postgres" else "MySQL"
        
        few_shot_examples = ""
        if db_type == "postgres":
            few_shot_examples = """
            Example 1: "Top 5 users by spend"
            SQL: SELECT user_id, SUM(amount) FROM transactions GROUP BY user_id ORDER BY SUM(amount) DESC LIMIT 5;
            """
        else:
            few_shot_examples = """
            Example 1: "Show all tables"
            SQL: SHOW TABLES;
            Example 2: "First 10 records of users"
            SQL: SELECT * FROM users LIMIT 10;
            """

        return Agent(
            role=f'{db_flavor} Expert',
            goal=f'Convert natural language requests into accurate {db_flavor} queries. Use ONLY the tables and columns provided in the schema.',
            backstory=f"""You are a senior {db_flavor} specialist. 
            Rules:
            1. Use ONLY provided schema.
            2. For joins, ensure column names match exactly.
            3. If context from previous query is provided, use it to refine the new query.
            4. If a requested table/column does not exist, return "-- ERROR: [Reason]".
            5. Return ONLY clean SQL without markdown blocks.
            
            {few_shot_examples}
            """,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )