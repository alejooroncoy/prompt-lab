"""
Conversation and Message domain entities.
Implements business rules for chat conversations.
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid


class MessageRole(Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class Message:
    """
    Immutable message entity with business invariants.
    Represents a single message in a conversation.
    """
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate message invariants."""
        if not self.content.strip():
            raise ValueError("Message content cannot be empty")
        
        if len(self.content) > 10000:
            raise ValueError("Message content too long (max 10000 characters)")
    
    @classmethod
    def create_user_message(cls, content: str, metadata: dict = None) -> "Message":
        """Factory method for user messages."""
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=content.strip(),
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
    
    @classmethod
    def create_assistant_message(cls, content: str, metadata: dict = None) -> "Message":
        """Factory method for assistant messages."""
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content.strip(),
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
    
    @property
    def word_count(self) -> int:
        """Calculate word count for analytics."""
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """Calculate character count for analytics."""
        return len(self.content)


@dataclass
class Conversation:
    """
    Conversation aggregate root.
    Manages a collection of messages with business rules.
    """
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate conversation invariants."""
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.title.strip():
            raise ValueError("Conversation title cannot be empty")
    
    @classmethod
    def create_new(cls, user_id: str, title: str = "Nueva Conversación") -> "Conversation":
        """Factory method for new conversations."""
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now
        )
    
    def add_message(self, message: Message) -> None:
        """Add message to conversation with business rules."""
        if not isinstance(message, Message):
            raise ValueError("Message must be a Message entity")
        
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if len(self.messages) == 1 and message.role == MessageRole.USER:
            self.title = self._generate_title_from_message(message.content)
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages for context building."""
        return self.messages[-limit:] if self.messages else []
    
    def get_messages_by_role(self, role: MessageRole) -> List[Message]:
        """Get messages filtered by role."""
        return [msg for msg in self.messages if msg.role == role]
    
    @property
    def message_count(self) -> int:
        """Total number of messages."""
        return len(self.messages)
    
    @property
    def total_tokens_used(self) -> int:
        """Calculate total tokens used across all messages."""
        return sum(
            msg.metadata.get('tokens_used', 0) 
            for msg in self.messages 
            if msg.role == MessageRole.ASSISTANT
        )
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time in milliseconds."""
        response_times = [
            msg.metadata.get('response_time_ms', 0)
            for msg in self.messages
            if msg.role == MessageRole.ASSISTANT and 'response_time_ms' in msg.metadata
        ]
        return sum(response_times) / len(response_times) if response_times else 0.0
    
    def _generate_title_from_message(self, content: str) -> str:
        """Generate conversation title from first message."""
        # Simple title generation - first 50 characters
        title = content.strip()[:50]
        return title + "..." if len(content) > 50 else title
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update conversation metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
