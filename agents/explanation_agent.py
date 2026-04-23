from crewai import Agent
from config import settings

class ExplanationAgent:
    def __init__(self):
        self.llm = f'mistral/{settings.MISTRAL_MODEL}'

    def get_agent(self):
        return Agent(
            role='SQL Logic Explainer',
            goal='Explain the reasoning behind a generated SQL query in plain English.',
            backstory='You are an expert at translating complex SQL logic into easy-to-understand explanations. '
                      'Focus on why specific tables were joined, why filters were applied, and what columns are being used.',
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
