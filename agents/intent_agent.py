from crewai import Agent
from config import settings

class IntentAgent:
    def __init__(self):
        self.llm = f'mistral/{settings.MISTRAL_MODEL_FAST}'

    def get_agent(self):
        return Agent(
            role='Intent Classifier',
            goal='Classify the user query into categories: LIST_DB, CREATE_DB, USE_DB, LIST_TABLES, or SQL_QUERY.',
            backstory='You are an expert at understanding intentions. Always ensure replies are beautifully formatted using Markdown (lists, tables). If a user asks for tables in a specific database, classify it as LIST_TABLES.',
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )