from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 6000
    openai_temperature: float = 0.1
    
    # App Configuration
    app_name: str = "FAQ Chatbot"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    database_csv_path: str = "data/microbe_database.csv"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = False
    
    # Security
    cors_origins: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    
    # Line Bot Configuration
    line_channel_access_token: str = "8wpqYRDhj2lqYHXrJj3fXk+oAv1EqmcaGvhSgFmN8IeVfBX+ujakcHogcS/opI9M8St5A5L0fR5r//nvg39q1p1LLDx5qSCGVSfs2rGJ5EvqLwRwUJzfAN4giEibcVwPeFuD9aYBjqnC+bFFsIBO5QdB04t89/1O/w1cDnyilFU="
    line_channel_secret: str = "29cc83f1dfc20dec73718eb97727d286"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings() 