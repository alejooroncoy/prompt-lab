"""
Analytics Port - Interface for analytics services.
Handles sentiment analysis and metrics tracking.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..entities.analytics import SentimentAnalysis, ResponseMetrics


@dataclass(frozen=True)
class AnalyticsRequest:
    """Request structure for analytics operations."""
    text: str
    context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Validate request invariants."""
        if not self.text.strip():
            raise ValueError("Text cannot be empty")


class AnalyticsError(Exception):
    """Base exception for analytics-related errors."""
    pass


class AnalyticsPort(ABC):
    """
    Abstract port for analytics services.
    Handles sentiment analysis, metrics tracking, and reporting.
    """
    
    @abstractmethod
    async def analyze_sentiment(self, request: AnalyticsRequest) -> SentimentAnalysis:
        """
        Analyze sentiment of text.
        
        Args:
            request: Analytics request with text to analyze
            
        Returns:
            Sentiment analysis result
            
        Raises:
            AnalyticsError: For analysis errors
        """
        pass
    
    @abstractmethod
    async def track_response_metrics(
        self, 
        metrics: ResponseMetrics,
        context: Dict[str, Any] = None
    ) -> None:
        """
        Track response performance metrics.
        
        Args:
            metrics: Response metrics to track
            context: Additional context for tracking
        """
        pass
    
    @abstractmethod
    async def generate_usage_report(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate usage report for user.
        
        Args:
            user_id: User ID to generate report for
            days: Number of days to include in report
            
        Returns:
            Usage report dictionary
        """
        pass
    
    @abstractmethod
    async def get_global_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get global platform metrics.
        
        Args:
            days: Number of days to include
            
        Returns:
            Global metrics dictionary
        """
        pass
