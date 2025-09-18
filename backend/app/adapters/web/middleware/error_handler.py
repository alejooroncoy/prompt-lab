"""
Error Handler Middleware.
Provides centralized error handling and logging.
"""
import logging
import uuid
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.ports.llm_port import LLMError, LLMTimeoutError, LLMRateLimitError, LLMQuotaExceededError
from app.core.ports.analytics_port import AnalyticsError

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """Setup error handlers for the FastAPI application."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": request_id
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.warning(f"Validation error: {exc.errors()} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "request_id": request_id
            }
        )
    
    @app.exception_handler(LLMTimeoutError)
    async def llm_timeout_handler(request: Request, exc: LLMTimeoutError):
        """Handle LLM timeout errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.error(f"LLM timeout: {exc} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=504,
            content={
                "error": "LLM Timeout",
                "message": "The AI service is taking too long to respond. Please try again.",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(LLMRateLimitError)
    async def llm_rate_limit_handler(request: Request, exc: LLMRateLimitError):
        """Handle LLM rate limit errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.warning(f"LLM rate limit: {exc} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate Limit Exceeded",
                "message": "Too many requests to the AI service. Please wait a moment and try again.",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(LLMQuotaExceededError)
    async def llm_quota_handler(request: Request, exc: LLMQuotaExceededError):
        """Handle LLM quota exceeded errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.error(f"LLM quota exceeded: {exc} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "message": "AI service quota exceeded. Please try again later.",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(LLMError)
    async def llm_error_handler(request: Request, exc: LLMError):
        """Handle general LLM errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.error(f"LLM error: {exc} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=502,
            content={
                "error": "AI Service Error",
                "message": "The AI service encountered an error. Please try again.",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(AnalyticsError)
    async def analytics_error_handler(request: Request, exc: AnalyticsError):
        """Handle analytics errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.warning(f"Analytics error: {exc} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Analytics Error",
                "message": "Analytics service encountered an error. The main functionality is still available.",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.warning(f"Starlette HTTP {exc.status_code}: {exc.detail} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": request_id
            }
        )
