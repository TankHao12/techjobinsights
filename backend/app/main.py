"""
Tech Jobs Insights NZ - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager
import os

# Import our modules
from app.database import get_db, test_connection
from sqlalchemy import text
import app.schemas as schemas

# Import routers
from app.routers import jobs, companies, analytics, categories, skills, operations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events - startup and shutdown
    """
    # Startup
    logger.info("Starting Tech Jobs Insights NZ API...")
    
    # Test database connection
    if test_connection():
        logger.info("Database connection verified")
    else:
        logger.error("Database connection failed")
        # Don't crash the app, but log the error
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Tech Jobs Insights NZ API...")

# Create FastAPI instance with lifespan events
app = FastAPI(
    title="Tech Jobs Insights NZ API",
    description="""
    ## Tech Jobs Insights NZ API
    
    A comprehensive API for analyzing the New Zealand technology job market.
    
    ### Features
    - **Job Search**: Search and filter tech job postings
    - **Skills Analysis**: Trending skills and demand analytics  
    - **Company Intelligence**: Company hiring patterns and statistics
    - **Market Analytics**: Salary trends and market insights
    - **Real-time Data**: Fresh job market data updated daily
    
    ### Data Sources
    - Seek NZ job postings
    - Manual curation and validation
    - Community contributions
    
    ### Usage
    All endpoints are publicly accessible. Rate limiting may apply.
    
    For questions or support, please visit our [GitHub repository](https://github.com/yourusername/tech-jobs-insights).
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend access
# Allow configuring allowed origins via environment variable ALLOWED_ORIGINS
# Format: comma-separated list of origins. Use "*" to allow all (for testing only).
default_origins = [
    "http://localhost:3000",  # React development server
    "http://localhost:5173",  # Vite development server
    "https://www.techjobinsights.me",  # Production frontend (custom domain)
    "https://techjobinsights.me",      # Production frontend (without www)
]

env_allowed = os.getenv("ALLOWED_ORIGINS", "").strip()
if env_allowed:
    if env_allowed == "*":
        allow_origins = ["*"]
    else:
        # split on comma and strip whitespace
        additional_origins = [o.strip() for o in env_allowed.split(",") if o.strip()]
        allow_origins = default_origins + additional_origins
else:
    allow_origins = default_origins

logger.info(f"CORS allowed origins: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API prefix
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(operations.router, prefix="/api/v1")

# Root endpoints
@app.get("/", response_model=schemas.APIResponse)
async def root():
    """
    Root endpoint - API information and status
    """
    return schemas.APIResponse(
        success=True,
        message="Tech Jobs Insights NZ API",
        data={
            "version": "1.0.0",
            "status": "running",
            "description": "API for New Zealand tech job market insights",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc"
            },
            "endpoints": {
                "jobs": "/api/v1/jobs",
                "skills": "/api/v1/skills", 
                "companies": "/api/v1/companies",
                "analytics": "/api/v1/analytics",
                "categories": "/api/v1/categories",
                "operations": "/api/v1/operations"
            }
        }
    )

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
        
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0",
        "timestamp": "2025-01-19T00:00:00Z"  # This would be dynamic in real implementation
    }

@app.get("/api/v1/info")
async def api_info():
    """
    API information and available endpoints
    """
    return {
        "api_name": "Tech Jobs Insights NZ",
        "version": "1.0.0",
        "description": "Comprehensive API for NZ tech job market analytics",
        "endpoints": {
            "jobs": {
                "description": "Job postings and search",
                "path": "/api/v1/jobs",
                "methods": ["GET", "POST", "PUT"]
            },
            "skills": {
                "description": "Skills analysis and trending",
                "path": "/api/v1/skills", 
                "methods": ["GET", "POST", "PUT"]
            },
            "companies": {
                "description": "Company information and statistics",
                "path": "/api/v1/companies",
                "methods": ["GET", "POST", "PUT"]
            },
            "analytics": {
                "description": "Market analytics and insights",
                "path": "/api/v1/analytics",
                "methods": ["GET"]
            }
        },
        "features": [
            "Full-text job search",
            "Skills trending analysis", 
            "Salary trend tracking",
            "Company hiring patterns",
            "Real-time market statistics",
            "Advanced filtering and pagination"
        ]
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=schemas.ErrorResponse(
            success=False,
            message="An internal server error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            details={"error": str(exc) if app.debug else "Please try again later"}
        ).dict()
    )

# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    Custom 404 handler
    """
    return JSONResponse(
        status_code=404,
        content=schemas.ErrorResponse(
            success=False,
            message="Endpoint not found",
            error_code="NOT_FOUND",
            details={
                "path": str(request.url.path),
                "suggestion": "Check the API documentation at /docs"
            }
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )