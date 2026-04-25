import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    
    # MySQL Settings
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "mysql")

    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    MISTRAL_MODEL_FAST: str = os.getenv("MISTRAL_MODEL_FAST", "mistral-small-latest")
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600 # 1 hour
    
    # Mechanical Copilot Settings
    MECHANICAL_DB: str = os.getenv("MECHANICAL_DB", "mech_ai_demo")
    MECHANICAL_DB_TYPE: str = os.getenv("MECHANICAL_DB_TYPE", "mysql")
    PREDICTION_REFRESH_INTERVAL: int = int(os.getenv("PREDICTION_REFRESH_INTERVAL", "300"))  # 5 min
    
    model_config = ConfigDict(extra="ignore", env_file=".env")

settings = Settings()
