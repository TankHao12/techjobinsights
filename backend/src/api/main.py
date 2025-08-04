"""
TechInsights  - Main FastAPI Application
Multi-source job market intelligence platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import logging

from src.core.config import settings
from src.core.logging import setup_logging
from src.api.routes import health, jobs, analytics, tech_stacks, companies

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TechInsights API",
    description="Job Market Intelligence Platform for New Zealand Tech Industry",
    version="2.0.0",
    docs_url=settings.API_DOCS_URL,
    redoc_url=settings.API_REDOC_URL,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": time.time(),
                "path": str(request.url)
            }
        }
    )

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# Health check routes
app.include_router(
    health.router, 
    prefix=f"{settings.API_PREFIX}/health", 
    tags=["health"]
)

# Core API routes
app.include_router(
    jobs.router, 
    prefix=f"{settings.API_PREFIX}/jobs", 
    tags=["jobs"]
)

app.include_router(
    analytics.router, 
    prefix=f"{settings.API_PREFIX}/analytics", 
    tags=["analytics"]
)

app.include_router(
    tech_stacks.router, 
    prefix=f"{settings.API_PREFIX}/tech-stacks", 
    tags=["tech-stacks"]
)

app.include_router(
    companies.router, 
    prefix=f"{settings.API_PREFIX}/companies", 
    tags=["companies"]
)

# ============================================================================
# APPLICATION EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 TechInsights API  starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    logger.info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("🛑 TechInsights API shutting down...")

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "name": "TechInsights API",
        "version": "2.0.0",
        "description": "Job Market Intelligence Platform for New Zealand Tech Industry",
        "docs": f"{settings.API_PREFIX}/docs",
        "health": f"{settings.API_PREFIX}/health",
        "environment": settings.ENVIRONMENT
    }

@app.get(f"{settings.API_PREFIX}")
async def api_info():
    """API information endpoint."""
    return {
        "api_version": "2.0.0",
        "endpoints": {
            "jobs": f"{settings.API_PREFIX}/jobs",
            "analytics": f"{settings.API_PREFIX}/analytics", 
            "tech_stacks": f"{settings.API_PREFIX}/tech-stacks",
            "companies": f"{settings.API_PREFIX}/companies",
            "health": f"{settings.API_PREFIX}/health"
        },
        "documentation": {
            "swagger": f"{settings.API_PREFIX}/docs",
            "redoc": f"{settings.API_PREFIX}/redoc"
        }
    }

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_config=None  # Use our custom logging
    )