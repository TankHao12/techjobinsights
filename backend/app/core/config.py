"""
Configuration management for tech-jobs-insights
"""
import os
from typing import Optional

class Settings:
    """Application settings"""

    # Database
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "database")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "techjobs")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "password")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # Scraping
    SCRAPING_DELAY_MIN: float = float(os.getenv("SCRAPING_DELAY_MIN", "1.0"))
    SCRAPING_DELAY_MAX: float = float(os.getenv("SCRAPING_DELAY_MAX", "2.0"))
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "30"))
    SCRAPING_RETRIES: int = int(os.getenv("SCRAPING_RETRIES", "3"))

    # Processing
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

settings = Settings()