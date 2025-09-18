"""
Analytics Tracking Use Case.
Tracks and aggregates metrics for conversations and users.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ...entities.analytics import ConversationAnalytics, LLMProvider
from ...ports.repository_port import AnalyticsRepositoryPort, ConversationRepositoryPort
from ...ports.analytics_port import AnalyticsPort

logger = logging.getLogger(__name__)


@dataclass
class MetricsTrackingRequest:
    """Request structure for metrics tracking."""
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    days: int = 30
    include_global: bool = False


@dataclass
class MetricsTrackingResponse:
    """Response structure for metrics tracking."""
    user_metrics: Optional[Dict[str, Any]] = None
    conversation_metrics: Optional[Dict[str, Any]] = None
    global_metrics: Optional[Dict[str, Any]] = None
    provider_breakdown: Dict[str, Any] = None
    sentiment_trends: Dict[str, Any] = None
    cost_analysis: Dict[str, Any] = None


class AnalyticsTrackingUseCase:
    """
    Analytics tracking use case.
    Aggregates and analyzes conversation metrics and trends.
    """
    
    def __init__(
        self,
        analytics_repo: AnalyticsRepositoryPort,
        conversation_repo: ConversationRepositoryPort,
        analytics_service: AnalyticsPort
    ):
        """
        Initialize analytics tracking use case.
        
        Args:
            analytics_repo: Analytics data repository
            conversation_repo: Conversation data repository
            analytics_service: Analytics service
        """
        self._analytics_repo = analytics_repo
        self._conversation_repo = conversation_repo
        self._analytics_service = analytics_service
    
    async def execute(self, request: MetricsTrackingRequest) -> MetricsTrackingResponse:
        """
        Execute metrics tracking workflow.
        
        Args:
            request: Metrics tracking request
            
        Returns:
            Metrics tracking response with aggregated data
            
        Raises:
            Exception: For processing errors
        """
        try:
            # Initialize response
            response = MetricsTrackingResponse()
            
            # Step 1: Get user metrics if user_id provided
            if request.user_id:
                response.user_metrics = await self._get_user_metrics(
                    request.user_id, 
                    request.days
                )
            
            # Step 2: Get conversation metrics if conversation_id provided
            if request.conversation_id:
                response.conversation_metrics = await self._get_conversation_metrics(
                    request.conversation_id
                )
            
            # Step 3: Get global metrics if requested
            if request.include_global:
                response.global_metrics = await self._get_global_metrics(request.days)
            
            # Step 4: Get provider breakdown
            response.provider_breakdown = await self._get_provider_breakdown(
                request.user_id, 
                request.days
            )
            
            # Step 5: Get sentiment trends
            response.sentiment_trends = await self._get_sentiment_trends(
                request.user_id, 
                request.days
            )
            
            # Step 6: Get cost analysis
            response.cost_analysis = await self._get_cost_analysis(
                request.user_id, 
                request.days
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Metrics tracking failed: {e}")
            raise
    
    async def _get_user_metrics(self, user_id: str, days: int) -> Dict[str, Any]:
        """Get user-specific metrics."""
        try:
            # Get user analytics summary
            user_summary = await self._analytics_repo.get_user_analytics_summary(
                user_id, 
                days
            )
            
            # Get user conversations
            conversations = await self._conversation_repo.get_user_conversations(
                user_id, 
                limit=100
            )
            
            # Calculate additional metrics
            total_conversations = len(conversations)
            total_messages = sum(conv.message_count for conv in conversations)
            avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_messages_per_conversation": round(avg_messages_per_conversation, 2),
                "total_tokens_used": user_summary.get("total_tokens", 0),
                "total_cost_usd": user_summary.get("total_cost", 0.0),
                "avg_response_time_ms": user_summary.get("avg_response_time", 0.0),
                "most_used_provider": user_summary.get("most_used_provider"),
                "sentiment_distribution": user_summary.get("sentiment_distribution", {}),
                "activity_trend": user_summary.get("activity_trend", "stable")
            }
            
        except Exception as e:
            logger.warning(f"Failed to get user metrics: {e}")
            return {"error": str(e)}
    
    async def _get_conversation_metrics(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation-specific metrics."""
        try:
            # Get conversation analytics
            analytics = await self._analytics_repo.get_analytics_by_conversation_id(
                conversation_id
            )
            
            if not analytics:
                return {"error": "No analytics found for conversation"}
            
            # Get conversation details
            conversation = await self._conversation_repo.get_conversation_by_id(
                conversation_id
            )
            
            if not conversation:
                return {"error": "Conversation not found"}
            
            return {
                "conversation_id": conversation_id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "total_messages": analytics.total_messages,
                "total_tokens_used": analytics.total_tokens_used,
                "total_cost_usd": analytics.total_cost_usd,
                "avg_response_time_ms": analytics.average_response_time_ms,
                "avg_message_length": analytics.average_message_length,
                "provider_usage": analytics.provider_usage,
                "most_used_provider": analytics.most_used_provider.value if analytics.most_used_provider else None,
                "sentiment_trend": analytics.sentiment_trend,
                "avg_sentiment": {
                    "sentiment": analytics.average_sentiment.sentiment.value if analytics.average_sentiment else None,
                    "polarity": analytics.average_sentiment.polarity if analytics.average_sentiment else 0.0,
                    "confidence": analytics.average_sentiment.confidence if analytics.average_sentiment else 0.0
                } if analytics.average_sentiment else None,
                "cost_per_message": analytics.cost_per_message
            }
            
        except Exception as e:
            logger.warning(f"Failed to get conversation metrics: {e}")
            return {"error": str(e)}
    
    async def _get_global_metrics(self, days: int) -> Dict[str, Any]:
        """Get global platform metrics."""
        try:
            global_summary = await self._analytics_repo.get_global_analytics_summary(days)
            
            return {
                "period_days": days,
                "total_users": global_summary.get("total_users", 0),
                "total_conversations": global_summary.get("total_conversations", 0),
                "total_messages": global_summary.get("total_messages", 0),
                "total_tokens_used": global_summary.get("total_tokens", 0),
                "total_cost_usd": global_summary.get("total_cost", 0.0),
                "avg_response_time_ms": global_summary.get("avg_response_time", 0.0),
                "provider_distribution": global_summary.get("provider_distribution", {}),
                "sentiment_distribution": global_summary.get("sentiment_distribution", {}),
                "daily_activity": global_summary.get("daily_activity", [])
            }
            
        except Exception as e:
            logger.warning(f"Failed to get global metrics: {e}")
            return {"error": str(e)}
    
    async def _get_provider_breakdown(
        self, 
        user_id: Optional[str], 
        days: int
    ) -> Dict[str, Any]:
        """Get provider usage breakdown."""
        try:
            if user_id:
                summary = await self._analytics_repo.get_user_analytics_summary(user_id, days)
            else:
                summary = await self._analytics_repo.get_global_analytics_summary(days)
            
            provider_distribution = summary.get("provider_distribution", {})
            
            # Calculate percentages
            total_usage = sum(provider_distribution.values())
            provider_percentages = {
                provider: round((count / total_usage) * 100, 2) if total_usage > 0 else 0
                for provider, count in provider_distribution.items()
            }
            
            return {
                "provider_distribution": provider_distribution,
                "provider_percentages": provider_percentages,
                "total_requests": total_usage,
                "most_used_provider": max(provider_distribution.items(), key=lambda x: x[1])[0] if provider_distribution else None
            }
            
        except Exception as e:
            logger.warning(f"Failed to get provider breakdown: {e}")
            return {"error": str(e)}
    
    async def _get_sentiment_trends(
        self, 
        user_id: Optional[str], 
        days: int
    ) -> Dict[str, Any]:
        """Get sentiment analysis trends."""
        try:
            if user_id:
                summary = await self._analytics_repo.get_user_analytics_summary(user_id, days)
            else:
                summary = await self._analytics_repo.get_global_analytics_summary(days)
            
            sentiment_distribution = summary.get("sentiment_distribution", {})
            
            # Calculate sentiment percentages
            total_sentiments = sum(sentiment_distribution.values())
            sentiment_percentages = {
                sentiment: round((count / total_sentiments) * 100, 2) if total_sentiments > 0 else 0
                for sentiment, count in sentiment_distribution.items()
            }
            
            return {
                "sentiment_distribution": sentiment_distribution,
                "sentiment_percentages": sentiment_percentages,
                "total_analyses": total_sentiments,
                "dominant_sentiment": max(sentiment_distribution.items(), key=lambda x: x[1])[0] if sentiment_distribution else None,
                "sentiment_trend": summary.get("sentiment_trend", "stable")
            }
            
        except Exception as e:
            logger.warning(f"Failed to get sentiment trends: {e}")
            return {"error": str(e)}
    
    async def _get_cost_analysis(
        self, 
        user_id: Optional[str], 
        days: int
    ) -> Dict[str, Any]:
        """Get cost analysis and breakdown."""
        try:
            if user_id:
                summary = await self._analytics_repo.get_user_analytics_summary(user_id, days)
            else:
                summary = await self._analytics_repo.get_global_analytics_summary(days)
            
            total_cost = summary.get("total_cost", 0.0)
            total_messages = summary.get("total_messages", 0)
            total_tokens = summary.get("total_tokens", 0)
            
            return {
                "total_cost_usd": total_cost,
                "avg_cost_per_message": round(total_cost / total_messages, 4) if total_messages > 0 else 0.0,
                "avg_cost_per_token": round(total_cost / total_tokens, 6) if total_tokens > 0 else 0.0,
                "total_messages": total_messages,
                "total_tokens": total_tokens,
                "cost_by_provider": summary.get("cost_by_provider", {}),
                "daily_cost_trend": summary.get("daily_cost_trend", [])
            }
            
        except Exception as e:
            logger.warning(f"Failed to get cost analysis: {e}")
            return {"error": str(e)}
