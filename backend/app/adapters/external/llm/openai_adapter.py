"""
OpenAI LLM Adapter.
Fallback provider with reliable performance.
"""
import asyncio
import time
from typing import Dict, Any, Optional
import logging

import openai
from openai import AsyncOpenAI

from app.core.ports.llm_port import (
    LLMPort, LLMRequest, LLMResponse, 
    LLMError, LLMTimeoutError, LLMRateLimitError, LLMQuotaExceededError
)
from app.core.entities.analytics import LLMProvider, ResponseMetrics

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMPort):
    """
    OpenAI LLM adapter implementation.
    Fallback provider with reliable performance and good Spanish support.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI adapter.
        
        Args:
            api_key: OpenAI API key
            model_name: OpenAI model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider = LLMProvider.OPENAI
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Token pricing (per 1M tokens) - GPT-3.5-turbo
        self.pricing = {
            "input": 0.50,   # $0.50 per 1M input tokens
            "output": 1.50,  # $1.50 per 1M output tokens
        }
        
        # Update pricing for GPT-4 if used
        if "gpt-4" in model_name.lower():
            self.pricing = {
                "input": 30.0,   # $30.0 per 1M input tokens
                "output": 60.0,  # $60.0 per 1M output tokens
            }
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response using OpenAI.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with content and metrics
            
        Raises:
            LLMError: For provider-specific errors
            LLMTimeoutError: For timeout errors
            LLMRateLimitError: For rate limit errors
            LLMQuotaExceededError: For quota exceeded errors
        """
        start_time = time.time()
        
        try:
            # Build messages array
            messages = self._build_messages(request)
            
            # Build completion parameters
            completion_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or 1000,
                "timeout": 30.0,  # 30 second timeout
            }
            
            # Generate response
            response = await self.client.chat.completions.create(**completion_params)
            
            # Calculate metrics
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract token usage
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            # Create response metrics
            metrics = ResponseMetrics(
                response_time_ms=response_time_ms,
                tokens_used=total_tokens,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                provider=self.provider,
                model_name=self.model_name,
                cost_usd=cost
            )
            
            # Create LLM response
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=self.provider,
                model_name=self.model_name,
                metrics=metrics,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model,
                    "id": response.id,
                    "created": response.created,
                }
            )
            
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}")
        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI request timeout: {e}")
        except openai.APIConnectionError as e:
            raise LLMError(f"OpenAI connection error: {e}")
        except openai.AuthenticationError as e:
            raise LLMError(f"OpenAI authentication error: {e}")
        except openai.PermissionDeniedError as e:
            raise LLMError(f"OpenAI permission denied: {e}")
        except openai.NotFoundError as e:
            raise LLMError(f"OpenAI model not found: {e}")
        except openai.BadRequestError as e:
            if "quota" in str(e).lower() or "billing" in str(e).lower():
                raise LLMQuotaExceededError(f"OpenAI quota exceeded: {e}")
            else:
                raise LLMError(f"OpenAI bad request: {e}")
        except Exception as e:
            raise LLMError(f"OpenAI generation failed: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if OpenAI service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Simple health check with minimal request
            test_request = LLMRequest(
                prompt="Hello",
                context={},
                max_tokens=10
            )
            
            # Use asyncio.wait_for for timeout
            await asyncio.wait_for(
                self.generate_response(test_request),
                timeout=15.0
            )
            
            return True
            
        except asyncio.TimeoutError:
            logger.warning("OpenAI health check timeout")
            return False
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get OpenAI provider information.
        
        Returns:
            Dictionary with provider metadata
        """
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "capabilities": [
                "text_generation",
                "conversation",
                "code_generation",
                "translation",
                "summarization"
            ],
            "max_tokens": 4096 if "gpt-3.5" in self.model_name else 8192,
            "supported_languages": ["es", "en", "fr", "de", "it", "pt", "ja", "ko", "zh"],
            "pricing": self.pricing,
            "rate_limits": {
                "requests_per_minute": 60,
                "tokens_per_minute": 90000
            }
        }
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """
        Estimate cost for OpenAI request.
        
        Args:
            request: LLM request to estimate
            
        Returns:
            Estimated cost in USD
        """
        # Estimate input tokens
        input_tokens = self._estimate_tokens(request.prompt)
        
        # Estimate output tokens (assume 50% of max_tokens or 200 default)
        output_tokens = request.max_tokens or 200
        
        return self._calculate_cost(input_tokens, output_tokens)
    
    def _build_messages(self, request: LLMRequest) -> list[Dict[str, str]]:
        """Build messages array for OpenAI API."""
        messages = []
        
        # Add system message if context provided
        if request.context:
            system_content = self._format_context(request.context)
            if system_content:
                messages.append({
                    "role": "system",
                    "content": system_content
                })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable text."""
        if not context:
            return ""
        
        context_parts = []
        for key, value in context.items():
            if isinstance(value, list):
                # Handle conversation history
                if key == "history":
                    history_text = "\n".join([
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                        for msg in value[-5:]  # Last 5 messages
                    ])
                    context_parts.append(f"Historial de conversación:\n{history_text}")
                else:
                    context_parts.append(f"{key}: {', '.join(map(str, value))}")
            else:
                context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Simple approximation: ~4 characters per token.
        """
        return len(text) // 4
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        input_cost = (input_tokens / 1_000_000) * self.pricing["input"]
        output_cost = (output_tokens / 1_000_000) * self.pricing["output"]
        return input_cost + output_cost
