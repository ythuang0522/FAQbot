from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4.1"
    openai_max_tokens: int = 6000
    openai_temperature: float = 0.1
    
    # App Configuration
    app_name: str = "FAQ Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    database_csv_path: str = "data/microbe_database.csv"
    
    # FAQ Configuration
    faq_directory_path: str = "faqs"
    faq_file_extension: str = ".txt"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = True
    
    # Security
    cors_origins: List[str] = Field(default=["http://localhost:8080", "http://127.0.0.1:8080"])
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    
    # Line Bot Configuration
    line_channel_access_token: str
    line_channel_secret: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def print_config(self):
        """Print current configuration for debugging."""
        logger.info(f"Open AI Model: {self.openai_model}")



def get_settings() -> Settings:
    return Settings()
