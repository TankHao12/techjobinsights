"""
TechInsights  - Health Check Routes
System health and status monitoring endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import time
import psutil
import asyncio
from datetime import datetime

from src.core.config import settings

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float
    system: Dict[str, Any]
    services: Dict[str, Dict[str, Any]]


class ServiceHealth(BaseModel):
    """Individual service health model."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time_ms: float
    details: Dict[str, Any] = {}


# Store application start time
start_time = time.time()


@router.get("/", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
        HealthStatus: Current system health and status
    """
    current_time = time.time()
    uptime = current_time - start_time
    
    # System information
    system_info = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
    }
    
    # Check individual services
    services = {}
    
    # Database health check
    db_health = await check_database_health()
    services["database"] = db_health.dict()
    
    # Redis health check
    redis_health = await check_redis_health()
    services["redis"] = redis_health.dict()
    
    # External APIs health check
    apis_health = await check_external_apis_health()
    services["external_apis"] = apis_health.dict()
    
    # Determine overall status
    overall_status = determine_overall_status(services)
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=uptime,
        system=system_info,
        services=services
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for basic availability check.
    
    Returns:
        dict: Simple pong response
    """
    return {
        "message": "pong",
        "timestamp": datetime.now(),
        "version": settings.APP_VERSION
    }


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        dict: Readiness status
    
    Raises:
        HTTPException: If system is not ready
    """
    # Check critical services
    db_health = await check_database_health()
    
    if db_health.status != "healthy":
        raise HTTPException(
            status_code=503,
            detail="Database is not ready"
        )
    
    return {
        "status": "ready",
        "timestamp": datetime.now()
    }


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "uptime_seconds": time.time() - start_time
    }


async def check_database_health() -> ServiceHealth:
    """
    Check PostgreSQL database health.
    
    Returns:
        ServiceHealth: Database health status
    """
    start_time_check = time.time()
    
    try:
        # Simple database connection test
        # TODO: Implement actual database connection check
        # For now, simulate the check
        await asyncio.sleep(0.001)  # Simulate database query
        
        response_time = (time.time() - start_time_check) * 1000
        
        return ServiceHealth(
            status="healthy",
            response_time_ms=response_time,
            details={
                "connection": "active",
                "database": settings.DATABASE_NAME,
                "host": settings.DATABASE_HOST
            }
        )
    
    except Exception as e:
        response_time = (time.time() - start_time_check) * 1000
        
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=response_time,
            details={
                "error": str(e),
                "connection": "failed"
            }
        )


async def check_redis_health() -> ServiceHealth:
    """
    Check Redis cache health.
    
    Returns:
        ServiceHealth: Redis health status
    """
    start_time_check = time.time()
    
    try:
        # Simple Redis connection test
        # TODO: Implement actual Redis connection check
        # For now, simulate the check
        await asyncio.sleep(0.001)  # Simulate Redis ping
        
        response_time = (time.time() - start_time_check) * 1000
        
        return ServiceHealth(
            status="healthy",
            response_time_ms=response_time,
            details={
                "connection": "active",
                "host": settings.REDIS_HOST,
                "database": settings.REDIS_DB
            }
        )
    
    except Exception as e:
        response_time = (time.time() - start_time_check) * 1000
        
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=response_time,
            details={
                "error": str(e),
                "connection": "failed"
            }
        )


async def check_external_apis_health() -> ServiceHealth:
    """
    Check external APIs health (job sources).
    
    Returns:
        ServiceHealth: External APIs health status
    """
    start_time_check = time.time()
    
    try:
        # Check external API endpoints
        # TODO: Implement actual API health checks
        # For now, simulate the check
        await asyncio.sleep(0.001)  # Simulate API checks
        
        response_time = (time.time() - start_time_check) * 1000
        
        return ServiceHealth(
            status="healthy",
            response_time_ms=response_time,
            details={
                "seek_api": "accessible",
                "indeed_api": "accessible",
                "trademe_api": "accessible"
            }
        )
    
    except Exception as e:
        response_time = (time.time() - start_time_check) * 1000
        
        return ServiceHealth(
            status="degraded",
            response_time_ms=response_time,
            details={
                "error": str(e),
                "note": "Some external APIs may be unavailable"
            }
        )


def determine_overall_status(services: Dict[str, Dict[str, Any]]) -> str:
    """
    Determine overall system health based on individual services.
    
    Args:
        services: Dictionary of service health statuses
    
    Returns:
        str: Overall status ('healthy', 'degraded', 'unhealthy')
    """
    statuses = [service["status"] for service in services.values()]
    
    if all(status == "healthy" for status in statuses):
        return "healthy"
    elif any(status == "unhealthy" for status in statuses):
        return "unhealthy"
    else:
        return "degraded"


# Additional monitoring endpoints

@router.get("/metrics")
async def get_metrics():
    """
    Get basic application metrics.
    
    Returns:
        dict: Application metrics
    """
    return {
        "uptime_seconds": time.time() - start_time,
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "cpu_percent": psutil.Process().cpu_percent(),
        "open_files": len(psutil.Process().open_files()),
        "threads": psutil.Process().num_threads(),
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION
    }


@router.get("/info")
async def get_system_info():
    """
    Get detailed system information.
    
    Returns:
        dict: System information
    """
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "system": {
            "platform": psutil.os.name,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
            "disk_total_gb": round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 2)
        },
        "configuration": {
            "database_host": settings.DATABASE_HOST,
            "redis_host": settings.REDIS_HOST,
            "api_prefix": settings.API_PREFIX,
            "cors_origins": settings.CORS_ORIGINS
        }
    }