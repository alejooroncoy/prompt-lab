"""
LLM Port - Interface for LLM providers.
Implements Repository pattern for multiple LLM providers with fallback strategy.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..entities.analytics import LLMProvider, ResponseMetrics


@dataclass(frozen=True)
class LLMRequest:
    """Request structure for LLM calls."""
    prompt: str
    context: Dict[str, Any]
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    model_name: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Validate request invariants."""
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")


@dataclass(frozen=True)
class LLMResponse:
    """Response structure from LLM calls."""
    content: str
    provider: LLMProvider
    model_name: str
    metrics: ResponseMetrics
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Validate response invariants."""
        if not self.content.strip():
            raise ValueError("Response content cannot be empty")


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMTimeoutError(LLMError):
    """LLM request timeout error."""
    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded error."""
    pass


class LLMQuotaExceededError(LLMError):
    """LLM quota exceeded error."""
    pass


class LLMPort(ABC):
    """
    Abstract port for LLM providers.
    Defines the contract for all LLM implementations.
    """
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from LLM provider.
        
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
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if LLM provider is healthy and available.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information and capabilities.
        
        Returns:
            Dictionary with provider metadata
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> float:
        """
        Estimate cost for the request.
        
        Args:
            request: LLM request to estimate
            
        Returns:
            Estimated cost in USD
        """
        pass


class LLMRepository:
    """
    Repository for managing multiple LLM providers.
    Implements fallback strategy and provider selection.
    """
    
    def __init__(self, providers: Dict[LLMProvider, LLMPort]):
        """
        Initialize LLM repository with providers.
        
        Args:
            providers: Dictionary mapping provider types to implementations
        """
        self._providers = providers
        # Only include providers that are actually available
        self._fallback_order = [
            provider for provider in [
                LLMProvider.GEMINI,  # Primary provider
                LLMProvider.GROQ,    # High-performance provider
                LLMProvider.OPENAI,  # Fallback provider
                LLMProvider.CLAUDE   # Future fallback
            ] if provider in providers
        ]
    
    async def generate_with_fallback(
        self, 
        request: LLMRequest,
        preferred_provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        """
        Generate response with automatic fallback strategy.
        
        Args:
            request: LLM request
            preferred_provider: Preferred provider (optional)
            
        Returns:
            LLM response from first available provider
            
        Raises:
            LLMError: If all providers fail
        """
        # Determine provider order
        provider_order = self._get_provider_order(preferred_provider)
        
        last_error = None
        
        for provider_type in provider_order:
            if provider_type not in self._providers:
                continue
            
            provider = self._providers[provider_type]
            
            try:
                # Check provider health first
                if not await provider.health_check():
                    continue
                
                # Attempt to generate response
                response = await provider.generate_response(request)
                return response
                
            except (LLMTimeoutError, LLMRateLimitError, LLMQuotaExceededError) as e:
                # These errors should trigger fallback
                last_error = e
                continue
                
            except LLMError as e:
                # Other LLM errors should also trigger fallback
                last_error = e
                continue
        
        # If all providers failed, raise the last error or a generic error
        if last_error:
            raise last_error
        else:
            raise LLMError("All LLM providers are unavailable")
    
    async def generate_with_specific_provider(
        self, 
        request: LLMRequest, 
        provider_type: LLMProvider
    ) -> LLMResponse:
        """
        Generate response using specific provider.
        
        Args:
            request: LLM request
            provider_type: Specific provider to use
            
        Returns:
            LLM response from specified provider
            
        Raises:
            LLMError: If provider fails or is unavailable
        """
        if provider_type not in self._providers:
            raise LLMError(f"Provider {provider_type.value} not available")
        
        provider = self._providers[provider_type]
        
        if not await provider.health_check():
            raise LLMError(f"Provider {provider_type.value} is not healthy")
        
        return await provider.generate_response(request)
    
    async def get_available_providers(self) -> List[LLMProvider]:
        """
        Get list of currently available providers.
        
        Returns:
            List of available provider types
        """
        available = []
        
        for provider_type, provider in self._providers.items():
            try:
                if await provider.health_check():
                    available.append(provider_type)
            except Exception:
                # Provider is not available
                continue
        
        return available
    
    def get_provider_info(self, provider_type: LLMProvider) -> Dict[str, Any]:
        """
        Get information about specific provider.
        
        Args:
            provider_type: Provider type to get info for
            
        Returns:
            Provider information dictionary
        """
        if provider_type not in self._providers:
            raise ValueError(f"Provider {provider_type.value} not available")
        
        return self._providers[provider_type].get_provider_info()
    
    def estimate_cost(self, request: LLMRequest, provider_type: LLMProvider) -> float:
        """
        Estimate cost for request using specific provider.
        
        Args:
            request: LLM request
            provider_type: Provider to estimate cost for
            
        Returns:
            Estimated cost in USD
        """
        if provider_type not in self._providers:
            raise ValueError(f"Provider {provider_type.value} not available")
        
        return self._providers[provider_type].estimate_cost(request)
    
    def _get_provider_order(self, preferred_provider: Optional[LLMProvider]) -> List[LLMProvider]:
        """
        Get ordered list of providers to try.
        
        Args:
            preferred_provider: Preferred provider (optional)
            
        Returns:
            Ordered list of provider types
        """
        if preferred_provider and preferred_provider in self._providers:
            # Put preferred provider first
            order = [preferred_provider]
            # Add other providers in fallback order
            for provider in self._fallback_order:
                if provider != preferred_provider and provider in self._providers:
                    order.append(provider)
            return order
        
        # Use default fallback order
        return [p for p in self._fallback_order if p in self._providers]
