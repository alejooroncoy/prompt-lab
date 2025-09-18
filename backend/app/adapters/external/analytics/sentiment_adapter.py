"""
TextBlob Sentiment Analysis Adapter.
Provides sentiment analysis using TextBlob library.
"""
import logging
from typing import Dict, Any
from textblob import TextBlob

from app.core.ports.analytics_port import AnalyticsPort, AnalyticsRequest, AnalyticsError
from app.core.entities.analytics import SentimentAnalysis, SentimentType

logger = logging.getLogger(__name__)


class SentimentAnalysisAdapter(AnalyticsPort):
    """
    TextBlob-based sentiment analysis adapter.
    Provides sentiment analysis for Spanish and English text.
    """
    
    def __init__(self):
        """Initialize sentiment analysis adapter."""
        self.supported_languages = ["es", "en"]
    
    async def analyze_sentiment(self, request: AnalyticsRequest) -> SentimentAnalysis:
        """
        Analyze sentiment of text using TextBlob.
        
        Args:
            request: Analytics request with text to analyze
            
        Returns:
            Sentiment analysis result
            
        Raises:
            AnalyticsError: For analysis errors
        """
        try:
            # Create TextBlob object
            blob = TextBlob(request.text)
            
            # Get polarity and subjectivity
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Determine sentiment type
            if polarity > 0.1:
                sentiment = SentimentType.POSITIVE
            elif polarity < -0.1:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            # Calculate confidence based on polarity distance from neutral
            confidence = abs(polarity)
            
            # Create sentiment analysis result
            return SentimentAnalysis(
                sentiment=sentiment,
                polarity=polarity,
                subjectivity=subjectivity,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            raise AnalyticsError(f"Failed to analyze sentiment: {e}")
    
    async def track_response_metrics(
        self, 
        metrics: Any,  # ResponseMetrics from analytics entities
        context: Dict[str, Any] = None
    ) -> None:
        """
        Track response performance metrics.
        This adapter doesn't implement metrics tracking.
        
        Args:
            metrics: Response metrics to track
            context: Additional context for tracking
        """
        # TextBlob adapter doesn't track metrics
        # This would be handled by a separate metrics service
        logger.debug(f"Metrics tracking not implemented in sentiment adapter: {metrics}")
    
    async def generate_usage_report(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate usage report for user.
        This adapter doesn't implement reporting.
        
        Args:
            user_id: User ID to generate report for
            days: Number of days to include in report
            
        Returns:
            Empty report dictionary
        """
        # TextBlob adapter doesn't generate reports
        # This would be handled by a separate reporting service
        return {
            "user_id": user_id,
            "days": days,
            "sentiment_analyses": 0,
            "note": "Reporting not implemented in sentiment adapter"
        }
    
    async def get_global_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get global platform metrics.
        This adapter doesn't implement global metrics.
        
        Args:
            days: Number of days to include
            
        Returns:
            Empty metrics dictionary
        """
        # TextBlob adapter doesn't provide global metrics
        # This would be handled by a separate metrics service
        return {
            "days": days,
            "total_analyses": 0,
            "note": "Global metrics not implemented in sentiment adapter"
        }
    
    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages."""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if language is supported."""
        return language_code.lower() in self.supported_languages
