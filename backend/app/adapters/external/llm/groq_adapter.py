"""
Groq LLM Adapter.
High-performance provider with ultra-fast inference.
"""
import asyncio
import time
from typing import Dict, Any, Optional
import logging

from groq import AsyncGroq

from app.core.ports.llm_port import (
    LLMPort, LLMRequest, LLMResponse, 
    LLMError, LLMTimeoutError, LLMRateLimitError, LLMQuotaExceededError
)
from app.core.entities.analytics import LLMProvider, ResponseMetrics

logger = logging.getLogger(__name__)


class GroqAdapter(LLMPort):
    """
    Groq LLM adapter implementation.
    High-performance provider with ultra-fast inference and excellent Spanish support.
    """
    
    def __init__(self, api_key: str, model_name: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq adapter.
        
        Args:
            api_key: Groq API key
            model_name: Groq model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider = LLMProvider.GROQ
        
        # Initialize Groq client
        self.client = AsyncGroq(api_key=api_key)
        
        # Token pricing (per 1M tokens) - Groq pricing
        self.pricing = {
            "input": 0.27,   # $0.27 per 1M input tokens
            "output": 0.27,  # $0.27 per 1M output tokens
        }
        
        # Update pricing for different models
        if "llama3-70b" in model_name.lower():
            self.pricing = {
                "input": 0.59,   # $0.59 per 1M input tokens
                "output": 0.79,  # $0.79 per 1M output tokens
            }
        elif "mixtral" in model_name.lower():
            self.pricing = {
                "input": 0.27,   # $0.27 per 1M input tokens
                "output": 0.27,  # $0.27 per 1M output tokens
            }
    
    async def generate_response(
        self, 
        request: LLMRequest, 
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using Groq API.
        
        Args:
            request: LLM request with prompt and context
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated content and metrics
            
        Raises:
            LLMError: For various API errors
        """
        start_time = time.time()
        
        try:
            # Build messages from context
            messages = self._build_messages(request)
            
            # Prepare request parameters
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or 2048,
                "temperature": request.temperature or 0.7,
                "stream": False,
            }
            
            # Add any additional parameters
            request_params.update(kwargs)
            
            logger.debug(f"Groq request: {request_params}")
            
            # Make API call
            response = await self.client.chat.completions.create(**request_params)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Calculate token usage
            usage = response.usage
            tokens_input = usage.prompt_tokens
            tokens_output = usage.completion_tokens
            tokens_total = usage.total_tokens
            
            # Calculate costs
            input_cost = (tokens_input / 1_000_000) * self.pricing["input"]
            output_cost = (tokens_output / 1_000_000) * self.pricing["output"]
            total_cost = input_cost + output_cost
            
            # Calculate tokens per second
            tokens_per_second = tokens_output / (response_time_ms / 1000) if response_time_ms > 0 else 0
            
            # Create metrics
            metrics = ResponseMetrics(
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_used=tokens_total,
                response_time_ms=response_time_ms,
                cost_usd=total_cost,
                provider=self.provider,
                model_name=self.model_name
            )
            
            # Create response
            return LLMResponse(
                content=content,
                provider=self.provider,
                model_name=self.model_name,
                metrics=metrics,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model_version": self.model_name,
                    "request_id": getattr(response, 'id', None),
                }
            )
            
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Groq request timeout after {time.time() - start_time:.2f}s")
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq API error: {error_msg}")
            
            # Handle specific error types
            if "rate limit" in error_msg.lower():
                raise LLMRateLimitError(f"Groq rate limit exceeded: {error_msg}")
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                raise LLMQuotaExceededError(f"Groq quota exceeded: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise LLMTimeoutError(f"Groq request timeout: {error_msg}")
            else:
                raise LLMError(f"Groq API error: {error_msg}")
    
    def _build_messages(self, request: LLMRequest) -> list:
        """
        Build messages array from LLM request.
        
        Args:
            request: LLM request with prompt and context
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system message if context has instructions
        if request.context and "system_instruction" in request.context:
            messages.append({
                "role": "system",
                "content": request.context["system_instruction"]
            })
        
        # Add conversation history if available
        if request.context and "history" in request.context:
            for msg in request.context["history"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
    
    async def health_check(self) -> bool:
        """
        Check if Groq API is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check with minimal request
            test_request = LLMRequest(
                prompt="Hello",
                context={},
                max_tokens=10,
                temperature=0.1
            )
            
            response = await self.generate_response(test_request)
            return response is not None and len(response.content) > 0
            
        except Exception as e:
            logger.warning(f"Groq health check failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information and capabilities.
        
        Returns:
            Dictionary with provider information
        """
        return {
            "name": "Groq",
            "provider": self.provider.value,
            "model": self.model_name,
            "pricing": self.pricing,
            "capabilities": [
                "ultra_fast_inference",
                "spanish_support",
                "code_generation",
                "reasoning",
                "creative_writing"
            ],
            "max_tokens": 8192,
            "supported_models": [
                "llama-3.1-8b-instant",
                "llama-3.1-70b-versatile", 
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]
        }
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """
        Estimate cost for the request based on token usage.
        
        Args:
            request: LLM request to estimate cost for
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimation based on prompt length
        # This is a simplified estimation - actual cost depends on tokenization
        estimated_input_tokens = len(request.prompt.split()) * 1.3  # Rough token estimation
        estimated_output_tokens = request.max_tokens or 2048
        
        # Calculate estimated costs
        input_cost = (estimated_input_tokens / 1_000_000) * self.pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * self.pricing["output"]
        
        return input_cost + output_cost