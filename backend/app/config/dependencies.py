"""
Dependency injection container.
Manages application dependencies and their lifecycle.
"""
import logging
from typing import Dict, Any

from .settings import settings
from ..core.ports.llm_port import LLMRepository, LLMProvider
from ..core.ports.repository_port import (
    ConversationRepositoryPort, AnalyticsRepositoryPort, 
    PromptTemplateRepositoryPort, CacheRepositoryPort
)
from ..core.ports.analytics_port import AnalyticsPort
from ..adapters.external.llm.gemini_adapter import GeminiAdapter
from ..adapters.external.llm.groq_adapter import GroqAdapter
from ..adapters.external.analytics.sentiment_adapter import SentimentAnalysisAdapter
from ..adapters.repositories.sqlite.conversation_repository import SQLiteConversationRepository
from ..adapters.repositories.sqlite.analytics_repository import SQLiteAnalyticsRepository
from ..adapters.repositories.redis.cache_repository import RedisCacheRepository

logger = logging.getLogger(__name__)

# Global dependency instances
_dependencies: Dict[str, Any] = {}


def get_llm_repository() -> LLMRepository:
    """Get LLM repository with configured providers."""
    if "llm_repository" not in _dependencies:
        providers = {}
        
        # Add Gemini provider if API key is available
        if settings.gemini_api_key:
            try:
                gemini_adapter = GeminiAdapter(
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model
                )
                providers[LLMProvider.GEMINI] = gemini_adapter
                logger.info("Gemini provider configured")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini provider: {e}")
        
        # Add Groq provider if API key is available
        if settings.groq_api_key:
            try:
                groq_adapter = GroqAdapter(
                    api_key=settings.groq_api_key,
                    model_name=settings.groq_model
                )
                providers[LLMProvider.GROQ] = groq_adapter
                logger.info("Groq provider configured")
            except Exception as e:
                logger.warning(f"Failed to configure Groq provider: {e}")
        
        if not providers:
            logger.error("No LLM providers configured! Please set API keys.")
            raise RuntimeError("No LLM providers available")
        
        _dependencies["llm_repository"] = LLMRepository(providers)
        logger.info(f"LLM repository configured with {len(providers)} providers")
    
    return _dependencies["llm_repository"]


def get_conversation_repository() -> ConversationRepositoryPort:
    """Get conversation repository."""
    if "conversation_repository" not in _dependencies:
        _dependencies["conversation_repository"] = SQLiteConversationRepository()
        logger.info("Conversation repository configured")
    
    return _dependencies["conversation_repository"]


def get_analytics_repository() -> AnalyticsRepositoryPort:
    """Get analytics repository."""
    if "analytics_repository" not in _dependencies:
        _dependencies["analytics_repository"] = SQLiteAnalyticsRepository()
        logger.info("Analytics repository configured")
    
    return _dependencies["analytics_repository"]


def get_cache_repository() -> CacheRepositoryPort:
    """Get cache repository."""
    if "cache_repository" not in _dependencies:
        _dependencies["cache_repository"] = RedisCacheRepository(
            redis_url=settings.redis_url
        )
        logger.info("Cache repository configured")
    
    return _dependencies["cache_repository"]


def get_analytics_service() -> AnalyticsPort:
    """Get analytics service."""
    if "analytics_service" not in _dependencies:
        _dependencies["analytics_service"] = SentimentAnalysisAdapter()
        logger.info("Analytics service configured")
    
    return _dependencies["analytics_service"]


def get_prompt_template_repository() -> PromptTemplateRepositoryPort:
    """Get prompt template repository."""
    if "prompt_template_repository" not in _dependencies:
        # For now, we'll use a simple in-memory implementation
        # In a real application, this would be a database repository
        from ..adapters.repositories.memory.prompt_template_repository import MemoryPromptTemplateRepository
        _dependencies["prompt_template_repository"] = MemoryPromptTemplateRepository()
        logger.info("Prompt template repository configured")
    
    return _dependencies["prompt_template_repository"]


async def initialize_dependencies() -> None:
    """Initialize all dependencies."""
    try:
        # Initialize repositories
        conversation_repo = get_conversation_repository()
        analytics_repo = get_analytics_repository()
        cache_repo = get_cache_repository()
        analytics_service = get_analytics_service()
        template_repo = get_prompt_template_repository()
        
        # Initialize LLM repository
        llm_repo = get_llm_repository()
        
        # Test connections
        logger.info("Testing dependency connections...")
        
        # Test cache connection
        try:
            await cache_repo.get("test")
            logger.info("Cache connection: OK")
        except Exception as e:
            logger.warning(f"Cache connection failed: {e}")
        
        # Test LLM providers
        available_providers = await llm_repo.get_available_providers()
        logger.info(f"Available LLM providers: {[p.value for p in available_providers]}")
        
        logger.info("All dependencies initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise


async def cleanup_dependencies() -> None:
    """Cleanup all dependencies."""
    try:
        # Close cache connection
        if "cache_repository" in _dependencies:
            cache_repo = _dependencies["cache_repository"]
            if hasattr(cache_repo, 'close'):
                await cache_repo.close()
        
        # Clear dependencies
        _dependencies.clear()
        logger.info("Dependencies cleaned up")
        
    except Exception as e:
        logger.error(f"Failed to cleanup dependencies: {e}")


def get_dependency_status() -> Dict[str, Any]:
    """Get status of all dependencies."""
    status = {
        "llm_repository": "llm_repository" in _dependencies,
        "conversation_repository": "conversation_repository" in _dependencies,
        "analytics_repository": "analytics_repository" in _dependencies,
        "cache_repository": "cache_repository" in _dependencies,
        "analytics_service": "analytics_service" in _dependencies,
        "prompt_template_repository": "prompt_template_repository" in _dependencies,
    }
    
    return status
