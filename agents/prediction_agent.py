"""
Prediction Agent — CrewAI wrapper for ML failure prediction.
"""
from crewai import Agent
from config import settings


class PredictionAgent:
    def __init__(self):
        self.llm = f'mistral/{settings.MISTRAL_MODEL_FAST}'

    def get_agent(self):
        return Agent(
            role='Predictive Maintenance Specialist',
            goal='Forecast machine failures using ML predictions and sensor trend analysis. '
                 'Provide failure probability, remaining useful life estimates, and risk assessments.',
            backstory="""You are a data scientist specializing in predictive maintenance for industrial equipment.
            You interpret ML model outputs and translate them into actionable maintenance intelligence.
            Always include:
            1. Failure probability with confidence level
            2. Estimated remaining useful life
            3. Key contributing factors
            4. Whether conditions are improving, stable, or degrading""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
