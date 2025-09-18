"""
Analytics domain entities.
Handles sentiment analysis, metrics tracking, and performance data.
"""
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import uuid


class SentimentType(Enum):
    """Sentiment analysis results."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class LLMProvider(Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"
    CLAUDE = "claude"  # Future expansion


@dataclass(frozen=True)
class SentimentAnalysis:
    """
    Immutable sentiment analysis result.
    Contains polarity, subjectivity, and confidence scores.
    """
    sentiment: SentimentType
    polarity: float  # -1.0 to 1.0
    subjectivity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    
    def __post_init__(self) -> None:
        """Validate sentiment analysis invariants."""
        if not -1.0 <= self.polarity <= 1.0:
            raise ValueError("Polarity must be between -1.0 and 1.0")
        
        if not 0.0 <= self.subjectivity <= 1.0:
            raise ValueError("Subjectivity must be between 0.0 and 1.0")
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    @classmethod
    def from_polarity(cls, polarity: float, subjectivity: float = 0.5) -> "SentimentAnalysis":
        """Create sentiment analysis from polarity score."""
        # Determine sentiment type based on polarity
        if polarity > 0.1:
            sentiment = SentimentType.POSITIVE
        elif polarity < -0.1:
            sentiment = SentimentType.NEGATIVE
        else:
            sentiment = SentimentType.NEUTRAL
        
        # Calculate confidence based on polarity distance from neutral
        confidence = abs(polarity)
        
        return cls(
            sentiment=sentiment,
            polarity=polarity,
            subjectivity=subjectivity,
            confidence=confidence
        )


@dataclass(frozen=True)
class ResponseMetrics:
    """
    Immutable response performance metrics.
    Tracks timing, token usage, and quality indicators.
    """
    response_time_ms: float
    tokens_used: int
    tokens_input: int
    tokens_output: int
    provider: LLMProvider
    model_name: str
    cost_usd: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate metrics invariants."""
        if self.response_time_ms < 0:
            raise ValueError("Response time cannot be negative")
        
        if self.tokens_used < 0:
            raise ValueError("Token usage cannot be negative")
        
        if self.cost_usd < 0:
            raise ValueError("Cost cannot be negative")
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second processing rate."""
        if self.response_time_ms == 0:
            return 0.0
        return (self.tokens_output * 1000) / self.response_time_ms


@dataclass
class ConversationAnalytics:
    """
    Analytics aggregate for a conversation.
    Tracks sentiment trends, performance metrics, and usage patterns.
    """
    id: str
    conversation_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    # Sentiment tracking
    sentiment_history: list[SentimentAnalysis] = field(default_factory=list)
    average_sentiment: Optional[SentimentAnalysis] = None
    
    # Performance metrics
    total_messages: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    average_response_time_ms: float = 0.0
    
    # Provider usage
    provider_usage: Dict[LLMProvider, int] = field(default_factory=dict)
    
    # Quality metrics
    average_message_length: float = 0.0
    total_word_count: int = 0
    
    def __post_init__(self) -> None:
        """Initialize provider usage tracking."""
        if not self.provider_usage:
            for provider in LLMProvider:
                self.provider_usage[provider] = 0
    
    @classmethod
    def create_for_conversation(cls, conversation_id: str, user_id: str) -> "ConversationAnalytics":
        """Factory method for new conversation analytics."""
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            created_at=now,
            updated_at=now
        )
    
    def add_sentiment_analysis(self, analysis: SentimentAnalysis) -> None:
        """Add sentiment analysis result."""
        self.sentiment_history.append(analysis)
        self._update_average_sentiment()
        self.updated_at = datetime.utcnow()
    
    def add_response_metrics(self, metrics: ResponseMetrics) -> None:
        """Add response performance metrics."""
        self.total_tokens_used += metrics.tokens_used
        self.total_cost_usd += metrics.cost_usd
        self.provider_usage[metrics.provider] += 1
        
        # Update average response time
        self._update_average_response_time(metrics.response_time_ms)
        self.updated_at = datetime.utcnow()
    
    def update_message_stats(self, message_count: int, word_count: int) -> None:
        """Update message and word count statistics."""
        self.total_messages = message_count
        self.total_word_count = word_count
        self.average_message_length = word_count / message_count if message_count > 0 else 0.0
        self.updated_at = datetime.utcnow()
    
    def _update_average_sentiment(self) -> None:
        """Calculate and update average sentiment."""
        if not self.sentiment_history:
            return
        
        avg_polarity = sum(s.polarity for s in self.sentiment_history) / len(self.sentiment_history)
        avg_subjectivity = sum(s.subjectivity for s in self.sentiment_history) / len(self.sentiment_history)
        
        self.average_sentiment = SentimentAnalysis.from_polarity(avg_polarity, avg_subjectivity)
    
    def _update_average_response_time(self, new_response_time: float) -> None:
        """Update average response time using running average."""
        if self.average_response_time_ms == 0:
            self.average_response_time_ms = new_response_time
        else:
            # Simple running average
            self.average_response_time_ms = (self.average_response_time_ms + new_response_time) / 2
    
    @property
    def sentiment_trend(self) -> str:
        """Determine sentiment trend over time."""
        if len(self.sentiment_history) < 2:
            return "insufficient_data"
        
        recent = self.sentiment_history[-3:]  # Last 3 analyses
        if len(recent) < 2:
            return "insufficient_data"
        
        first_polarity = recent[0].polarity
        last_polarity = recent[-1].polarity
        
        if last_polarity > first_polarity + 0.1:
            return "improving"
        elif last_polarity < first_polarity - 0.1:
            return "declining"
        else:
            return "stable"
    
    @property
    def most_used_provider(self) -> Optional[LLMProvider]:
        """Get the most frequently used LLM provider."""
        if not self.provider_usage:
            return None
        
        return max(self.provider_usage.items(), key=lambda x: x[1])[0]
    
    @property
    def cost_per_message(self) -> float:
        """Calculate average cost per message."""
        return self.total_cost_usd / self.total_messages if self.total_messages > 0 else 0.0
