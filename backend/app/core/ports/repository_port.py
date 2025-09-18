"""
Repository Ports - Interfaces for data persistence.
Implements Repository pattern for clean separation of concerns.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.conversation import Conversation, Message
from ..entities.analytics import ConversationAnalytics
from ..entities.prompt_template import PromptTemplate
from ..entities.user import User


class ConversationRepositoryPort(ABC):
    """Abstract port for conversation data persistence."""
    
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> None:
        """Save or update conversation."""
        pass
    
    @abstractmethod
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        pass
    
    @abstractmethod
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Conversation]:
        """Get user's conversations with pagination."""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation by ID."""
        pass
    
    @abstractmethod
    async def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by content."""
        pass


class AnalyticsRepositoryPort(ABC):
    """Abstract port for analytics data persistence."""
    
    @abstractmethod
    async def save_analytics(self, analytics: ConversationAnalytics) -> None:
        """Save or update conversation analytics."""
        pass
    
    @abstractmethod
    async def get_analytics_by_conversation_id(
        self, 
        conversation_id: str
    ) -> Optional[ConversationAnalytics]:
        """Get analytics for specific conversation."""
        pass
    
    @abstractmethod
    async def get_user_analytics_summary(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user analytics summary for specified days."""
        pass
    
    @abstractmethod
    async def get_global_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get global analytics summary for specified days."""
        pass


class PromptTemplateRepositoryPort(ABC):
    """Abstract port for prompt template data persistence."""
    
    @abstractmethod
    async def save_template(self, template: PromptTemplate) -> None:
        """Save or update prompt template."""
        pass
    
    @abstractmethod
    async def get_template_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID."""
        pass
    
    @abstractmethod
    async def get_templates_by_category(
        self, 
        category: str, 
        limit: int = 50
    ) -> List[PromptTemplate]:
        """Get templates by category."""
        pass
    
    @abstractmethod
    async def get_all_templates(self, limit: int = 100) -> List[PromptTemplate]:
        """Get all available templates."""
        pass
    
    @abstractmethod
    async def search_templates(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[PromptTemplate]:
        """Search templates by name or description."""
        pass


class UserRepositoryPort(ABC):
    """Abstract port for user data persistence."""
    
    @abstractmethod
    async def save_user(self, user: User) -> None:
        """Save or update user."""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID."""
        pass


class CacheRepositoryPort(ABC):
    """Abstract port for cache operations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl_seconds: int = 3600
    ) -> None:
        """Set value in cache with TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        pass
