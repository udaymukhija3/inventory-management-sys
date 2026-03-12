from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Service Info
    service_name: str = "analytics-service"
    version: str = "1.0.0"
    
    # Data stores
    redis_url: str = "redis://localhost:6379"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "inventory"
    postgres_user: str = "inventory_user"
    postgres_password: str = "inventory_pass"
    
    # API Configuration
    api_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
