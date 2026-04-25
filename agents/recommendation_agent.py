"""
Recommendation Agent — CrewAI wrapper for maintenance advisory.
"""
from crewai import Agent
from config import settings


class RecommendationAgent:
    def __init__(self):
        self.llm = f'mistral/{settings.MISTRAL_MODEL_FAST}'

    def get_agent(self):
        return Agent(
            role='Maintenance Advisor',
            goal='Generate clear, prioritized maintenance recommendations based on mechanical analysis and predictions. '
                 'Provide step-by-step action plans with urgency levels.',
            backstory="""You are a maintenance planning expert who translates technical diagnoses into 
            clear action plans for maintenance teams.
            Always include:
            1. Prioritized action steps
            2. Urgency level (IMMEDIATE / URGENT / SCHEDULED / ROUTINE)
            3. Required skill level for each action
            4. Estimated time for each action
            5. Consequences of inaction""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
