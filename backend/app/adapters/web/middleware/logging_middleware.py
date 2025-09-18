"""
Logging Middleware.
Provides request/response logging with correlation IDs.
"""
import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logging middleware for request/response tracking.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log successful response
            process_time = time.time() - start_time
            self._log_response(request, response, request_id, process_time)
            
            return response
            
        except Exception as e:
            # Log error response
            process_time = time.time() - start_time
            self._log_error(request, e, request_id, process_time)
            raise
    
    def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request."""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Get user agent
            user_agent = request.headers.get("User-Agent", "Unknown")
            
            # Log request
            logger.info(
                f"Request started - "
                f"ID: {request_id}, "
                f"Method: {request.method}, "
                f"Path: {request.url.path}, "
                f"Client: {client_ip}, "
                f"User-Agent: {user_agent[:100]}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to log request: {e}")
    
    def _log_response(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        process_time: float
    ) -> None:
        """Log successful response."""
        try:
            # Get response size
            response_size = response.headers.get("Content-Length", "Unknown")
            
            # Log response
            logger.info(
                f"Request completed - "
                f"ID: {request_id}, "
                f"Status: {response.status_code}, "
                f"Time: {process_time:.3f}s, "
                f"Size: {response_size}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to log response: {e}")
    
    def _log_error(
        self, 
        request: Request, 
        error: Exception, 
        request_id: str, 
        process_time: float
    ) -> None:
        """Log error response."""
        try:
            # Get error details
            error_type = type(error).__name__
            error_message = str(error)
            
            # Log error
            logger.error(
                f"Request failed - "
                f"ID: {request_id}, "
                f"Error: {error_type}, "
                f"Message: {error_message}, "
                f"Time: {process_time:.3f}s"
            )
            
        except Exception as e:
            logger.warning(f"Failed to log error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Use direct client IP
        if request.client:
            return request.client.host
        
        return "Unknown"
