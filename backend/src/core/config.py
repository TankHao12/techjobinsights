"""
TechInsights  - Configuration Management
Centralized configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application configuration settings."""

    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================
    APP_NAME: str = Field(default="TechInsights ", description="Application name")
    APP_VERSION: str = Field(default="2.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # ============================================================================
    # API CONFIGURATION
    # ============================================================================
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_PREFIX: str = Field(default="/api/v2", description="API prefix")
    API_DOCS_URL: str = Field(default="/docs", description="API documentation URL")
    API_REDOC_URL: str = Field(default="/redoc", description="API ReDoc URL")

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    DATABASE_URL: str = Field(
        default="postgresql://techinsights:dev_password_123@localhost:5432/techinsights_dev",
        description="Database connection URL"
    )
    DATABASE_HOST: str = Field(default="localhost", description="Database host")
    DATABASE_PORT: int = Field(default=5432, description="Database port")
    DATABASE_NAME: str = Field(default="techinsights_dev", description="Database name")
    DATABASE_USER: str = Field(default="techinsights", description="Database user")
    DATABASE_PASSWORD: str = Field(default="dev_password_123", description="Database password")

    # Connection Pool Settings
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow")
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")

    # ============================================================================
    # REDIS CONFIGURATION
    # ============================================================================
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")

    # Cache Settings
    CACHE_TTL: int = Field(default=300, description="Default cache TTL in seconds")
    CACHE_PREFIX: str = Field(default="techinsights:v2", description="Cache key prefix")

    # ============================================================================
    # SECURITY SETTINGS
    # ============================================================================
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="JWT access token expiration in minutes"
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst")

    # ============================================================================
    # DATA SOURCE CONFIGURATIONS
    # ============================================================================
    # Seek NZ
    SEEK_BASE_URL: str = Field(default="https://www.seek.co.nz", description="Seek base URL")
    SEEK_API_URL: str = Field(
        default="https://www.seek.co.nz/api/jobsearch/v5/search",
        description="Seek API URL"
    )
    SEEK_RATE_LIMIT: int = Field(default=100, description="Seek rate limit per hour")

    # Indeed
    INDEED_BASE_URL: str = Field(default="https://nz.indeed.com", description="Indeed base URL")
    INDEED_RATE_LIMIT: int = Field(default=50, description="Indeed rate limit per hour")

    # TradeMe
    TRADEME_BASE_URL: str = Field(
        default="https://api.trademe.co.nz/v1", description="TradeMe API base URL"
    )
    TRADEME_RATE_LIMIT: int = Field(default=75, description="TradeMe rate limit per hour")

    # ============================================================================
    # SCRAPING CONFIGURATION
    # ============================================================================
    SCRAPING_ENABLED: bool = Field(default=True, description="Enable job scraping")
    SCRAPING_CONCURRENT_LIMIT: int = Field(
        default=5, description="Concurrent scraping requests limit"
    )
    SCRAPING_TIMEOUT: int = Field(default=30, description="Scraping timeout in seconds")
    SCRAPING_RETRY_ATTEMPTS: int = Field(default=3, description="Scraping retry attempts")

    # ============================================================================
    # MACHINE LEARNING CONFIGURATION
    # ============================================================================
    ML_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7, description="ML confidence threshold"
    )
    SPACY_MODEL: str = Field(default="en_core_web_sm", description="spaCy model name")

    # ============================================================================
    # AZURE SERVICES CONFIGURATION
    # ============================================================================
    # Azure Storage
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = Field(default=None, description="Azure Storage account name")
    AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = Field(default=None, description="Azure Storage account key")
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None, description="Azure Storage connection string")
    AZURE_STORAGE_CONTAINER_NAME: str = Field(default="assets", description="Azure Storage container name")

    # Azure Application Insights
    APPINSIGHTS_INSTRUMENTATIONKEY: Optional[str] = Field(default=None, description="Application Insights key")
    APPINSIGHTS_CONNECTION_STRING: Optional[str] = Field(default=None, description="Application Insights connection string")
    AZURE_MONITOR_ENABLED: bool = Field(default=False, description="Enable Azure monitoring")

    # Azure Communication Services
    AZURE_COMMUNICATION_CONNECTION_STRING: Optional[str] = Field(default=None, description="Azure Communication Services connection string")

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    COLLECT_SEEK_JOBS: bool = Field(default=True, description="Collect jobs from Seek")
    COLLECT_INDEED_JOBS: bool = Field(default=True, description="Collect jobs from Indeed")
    COLLECT_TRADEME_JOBS: bool = Field(default=True, description="Collect jobs from TradeMe")
    COLLECT_LINKEDIN_JOBS: bool = Field(default=False, description="Collect jobs from LinkedIn")

    # Feature Flags
    FEATURE_USER_ACCOUNTS: bool = Field(default=True, description="Enable user accounts")
    FEATURE_JOB_ALERTS: bool = Field(default=True, description="Enable job alerts")
    FEATURE_ML_RECOMMENDATIONS: bool = Field(default=True, description="Enable ML recommendations")

    # ============================================================================
    # MONITORING & LOGGING
    # ============================================================================
    METRICS_ENABLED: bool = Field(default=True, description="Enable metrics collection")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")

    # ============================================================================
    # VALIDATORS
    # ============================================================================
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment values."""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v

    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level values."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of: {allowed}')
        return v.upper()

    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret(cls, v, values):
        """Validate JWT secret key in production."""
        if (values.get('ENVIRONMENT') == 'production' and 
            v == 'your-super-secret-jwt-key-change-this-in-production'):
            raise ValueError('JWT secret key must be changed in production')
        return v

    # ============================================================================
    # COMPUTED PROPERTIES
    # ============================================================================
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == 'development'

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == 'production'

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')

    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL."""
        return self.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

    @property
    def is_azure_deployment(self) -> bool:
        """Check if running on Azure."""
        return (self.AZURE_STORAGE_ACCOUNT_NAME is not None or 
                self.APPINSIGHTS_INSTRUMENTATIONKEY is not None or
                'azurewebsites.net' in os.getenv('WEBSITE_HOSTNAME', ''))

    @property
    def azure_storage_enabled(self) -> bool:
        """Check if Azure Storage is configured."""
        return (self.AZURE_STORAGE_CONNECTION_STRING is not None or 
                (self.AZURE_STORAGE_ACCOUNT_NAME is not None and 
                 self.AZURE_STORAGE_ACCOUNT_KEY is not None))

    @property
    def monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return (self.AZURE_MONITOR_ENABLED and 
                self.APPINSIGHTS_INSTRUMENTATIONKEY is not None)

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Development validation
if settings.is_development:
    print(f"🔧 TechInsights  - {settings.ENVIRONMENT.upper()} MODE")
    print(f"📊 Database: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    print(f"🔄 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"🚀 API: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 Docs: http://{settings.API_HOST}:{settings.API_PORT}{settings.API_DOCS_URL}")