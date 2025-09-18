"""
Health Check Router.
Provides health and status endpoints.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config.dependencies import (
    get_dependency_status, 
    get_llm_repository,
    get_cache_repository
)

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    dependencies: dict


class StatusResponse(BaseModel):
    """Status response model."""
    status: str
    timestamp: datetime
    llm_providers: list
    cache_status: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    Returns application status and dependency information.
    """
    try:
        # Get dependency status
        dependencies = get_dependency_status()
        
        # Determine overall status
        critical_deps = ["llm_repository", "conversation_repository", "analytics_repository"]
        all_critical_healthy = all(dependencies.get(dep, False) for dep in critical_deps)
        
        status = "healthy" if all_critical_healthy else "degraded"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies=dependencies
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/status", response_model=StatusResponse)
async def detailed_status():
    """
    Detailed status endpoint.
    Returns comprehensive system status including LLM providers.
    """
    try:
        # Get LLM repository status
        llm_repo = get_llm_repository()
        available_providers = await llm_repo.get_available_providers()
        
        # Get cache status
        cache_repo = get_cache_repository()
        cache_status = "connected" if hasattr(cache_repo, '_connected') and cache_repo._connected else "disconnected"
        
        return StatusResponse(
            status="operational",
            timestamp=datetime.utcnow(),
            llm_providers=[provider.value for provider in available_providers],
            cache_status=cache_status
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=503, detail="Status check failed")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Used by load balancers to determine if the service is ready to receive traffic.
    """
    try:
        # Check critical dependencies
        llm_repo = get_llm_repository()
        available_providers = await llm_repo.get_available_providers()
        
        if not available_providers:
            raise HTTPException(status_code=503, detail="No LLM providers available")
        
        return {"status": "ready", "timestamp": datetime.utcnow()}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    Used by orchestrators to determine if the service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}
