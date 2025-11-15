from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Service Info
    service_name: str = "analytics-service"
    version: str = "1.0.0"
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    redis_url: str = "redis://localhost:6379"
    
    # API Configuration
    api_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

