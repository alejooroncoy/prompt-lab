"""
Google Gemini LLM Adapter.
Primary LLM provider with advanced capabilities.
"""
import asyncio
import time
from typing import Dict, Any, Optional
import logging

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.ports.llm_port import (
    LLMPort, LLMRequest, LLMResponse, 
    LLMError, LLMTimeoutError, LLMRateLimitError, LLMQuotaExceededError
)
from app.core.entities.analytics import LLMProvider, ResponseMetrics

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMPort):
    """
    Google Gemini LLM adapter implementation.
    Primary provider with advanced reasoning capabilities.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini adapter.
        
        Args:
            api_key: Google AI API key
            model_name: Gemini model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider = LLMProvider.GEMINI
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        # Token pricing (per 1M tokens)
        self.pricing = {
            "input": 0.075,   # $0.075 per 1M input tokens
            "output": 0.30,   # $0.30 per 1M output tokens
        }
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response using Gemini.
        
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
            # Build generation config
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens or 2048,
                candidate_count=1,
            )
            
            # Prepare context if provided
            full_prompt = self._build_prompt_with_context(request)
            
            # Generate response
            response = await self._generate_with_retry(
                full_prompt, 
                generation_config
            )
            
            # Calculate metrics
            response_time_ms = (time.time() - start_time) * 1000
            
            # Estimate token usage (Gemini doesn't provide exact counts in free tier)
            input_tokens = self._estimate_tokens(full_prompt)
            output_tokens = self._estimate_tokens(response.text)
            total_tokens = input_tokens + output_tokens
            
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
                content=response.text,
                provider=self.provider,
                model_name=self.model_name,
                metrics=metrics,
                metadata={
                    "finish_reason": getattr(response, 'finish_reason', 'stop'),
                    "safety_ratings": getattr(response, 'safety_ratings', []),
                    "candidates": len(getattr(response, 'candidates', [])),
                }
            )
            
        except Exception as e:
            # Handle specific Gemini errors
            if "quota" in str(e).lower() or "billing" in str(e).lower():
                raise LLMQuotaExceededError(f"Gemini quota exceeded: {e}")
            elif "rate" in str(e).lower() or "limit" in str(e).lower():
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {e}")
            elif "timeout" in str(e).lower():
                raise LLMTimeoutError(f"Gemini request timeout: {e}")
            else:
                raise LLMError(f"Gemini generation failed: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if Gemini service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Simple health check with minimal request
            test_request = LLMRequest(
                prompt="Hello",
                context={},
                max_tokens=5,
                temperature=0.1
            )
            
            # Use asyncio.wait_for for timeout with shorter timeout
            await asyncio.wait_for(
                self.generate_response(test_request),
                timeout=5.0  # Reduced from 10.0 to 5.0 seconds
            )
            
            return True
            
        except asyncio.TimeoutError:
            logger.warning("Gemini health check timeout")
            return False
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get Gemini provider information.
        
        Returns:
            Dictionary with provider metadata
        """
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "capabilities": [
                "text_generation",
                "reasoning",
                "code_generation",
                "multimodal",  # Future capability
                "long_context"
            ],
            "max_tokens": 1048576,  # Gemini 1.5 Flash context window
            "supported_languages": ["es", "en", "fr", "de", "it", "pt", "ja", "ko", "zh"],
            "pricing": self.pricing,
            "rate_limits": {
                "requests_per_minute": 60,
                "tokens_per_minute": 32000
            }
        }
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """
        Estimate cost for Gemini request.
        
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
    
    def _build_prompt_with_context(self, request: LLMRequest) -> str:
        """Build full prompt with context information."""
        prompt_parts = [request.prompt]
        
        # Add context if provided
        if request.context:
            context_str = self._format_context(request.context)
            if context_str:
                prompt_parts.insert(0, f"Contexto:\n{context_str}\n\n")
        
        return "\n".join(prompt_parts)
    
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
    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        generation_config: genai.types.GenerationConfig,
        max_retries: int = 3
    ) -> Any:
        """Generate response with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )
                )
                
                if response.text:
                    return response
                else:
                    raise LLMError("Empty response from Gemini")
                    
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise e
        
        raise last_exception
    
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
