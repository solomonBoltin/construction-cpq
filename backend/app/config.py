from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # Explicitly define POSTGRES variables first
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT")
    BACKEND_PORT: str = os.getenv("BACKEND_PORT")  
    

    # DATABASE_URL can be provided directly or constructed
    DATABASE_URL: Optional[str] = None
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    def __init__(self, **values):
        super().__init__(**values)
        assert self.POSTGRES_USER, "POSTGRES_USER must be set"
        assert self.POSTGRES_HOST, "POSTGRES_HOST must be set"
        assert self.POSTGRES_PASSWORD, "POSTGRES_PASSWORD must be set"
        assert self.POSTGRES_DB, "POSTGRES_DB must be set"
        assert self.POSTGRES_PORT, "POSTGRES_PORT must be set"
        assert self.BACKEND_PORT, "BACKEND_PORT must be set"

        self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
