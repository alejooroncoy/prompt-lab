"""
User domain entity.
Manages user information and preferences.
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid


@dataclass
class User:
    """
    User entity with preferences and usage tracking.
    Manages user-specific settings and analytics.
    """
    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
    
    # User preferences
    preferred_llm_provider: Optional[str] = None
    default_template_category: Optional[str] = None
    language_preference: str = "es"
    
    # Usage tracking
    total_conversations: int = 0
    total_messages: int = 0
    total_tokens_used: int = 0
    
    # Settings
    analytics_enabled: bool = True
    auto_save_conversations: bool = True
    max_conversation_history: int = 100
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate user invariants."""
        if not self.email.strip():
            raise ValueError("Email cannot be empty")
        
        if not self.name.strip():
            raise ValueError("Name cannot be empty")
        
        if self.max_conversation_history < 1:
            raise ValueError("Max conversation history must be at least 1")
    
    @classmethod
    def create_new(
        cls,
        email: str,
        name: str,
        preferred_llm_provider: Optional[str] = None
    ) -> "User":
        """Factory method for new users."""
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            email=email.strip().lower(),
            name=name.strip(),
            created_at=now,
            updated_at=now,
            preferred_llm_provider=preferred_llm_provider
        )
    
    def update_preferences(
        self,
        preferred_llm_provider: Optional[str] = None,
        default_template_category: Optional[str] = None,
        language_preference: Optional[str] = None
    ) -> None:
        """Update user preferences."""
        if preferred_llm_provider is not None:
            self.preferred_llm_provider = preferred_llm_provider
        
        if default_template_category is not None:
            self.default_template_category = default_template_category
        
        if language_preference is not None:
            self.language_preference = language_preference
        
        self.updated_at = datetime.utcnow()
    
    def update_settings(
        self,
        analytics_enabled: Optional[bool] = None,
        auto_save_conversations: Optional[bool] = None,
        max_conversation_history: Optional[int] = None
    ) -> None:
        """Update user settings."""
        if analytics_enabled is not None:
            self.analytics_enabled = analytics_enabled
        
        if auto_save_conversations is not None:
            self.auto_save_conversations = auto_save_conversations
        
        if max_conversation_history is not None:
            if max_conversation_history < 1:
                raise ValueError("Max conversation history must be at least 1")
            self.max_conversation_history = max_conversation_history
        
        self.updated_at = datetime.utcnow()
    
    def increment_usage_stats(
        self,
        conversations: int = 0,
        messages: int = 0,
        tokens: int = 0
    ) -> None:
        """Increment usage statistics."""
        self.total_conversations += conversations
        self.total_messages += messages
        self.total_tokens_used += tokens
        self.updated_at = datetime.utcnow()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update user metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    @property
    def average_messages_per_conversation(self) -> float:
        """Calculate average messages per conversation."""
        return self.total_messages / self.total_conversations if self.total_conversations > 0 else 0.0
    
    @property
    def is_active_user(self) -> bool:
        """Check if user is considered active (has recent activity)."""
        # Consider active if has conversations or recent activity
        return self.total_conversations > 0 or self.total_messages > 0
