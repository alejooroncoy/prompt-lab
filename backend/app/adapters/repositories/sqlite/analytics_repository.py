"""
SQLite Analytics Repository Implementation.
Handles analytics data persistence using SQLite.
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiosqlite

from app.core.ports.repository_port import AnalyticsRepositoryPort
from app.core.entities.analytics import ConversationAnalytics, SentimentAnalysis, SentimentType, LLMProvider

logger = logging.getLogger(__name__)


class SQLiteAnalyticsRepository(AnalyticsRepositoryPort):
    """
    SQLite implementation of analytics repository.
    Handles conversation analytics persistence and aggregation.
    """
    
    def __init__(self, db_path: str = "prompt_lab.db"):
        """
        Initialize SQLite analytics repository.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
    
    async def _ensure_initialized(self) -> None:
        """Ensure database tables are created."""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Create conversation_analytics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversation_analytics (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_messages INTEGER DEFAULT 0,
                    total_tokens_used INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    average_response_time_ms REAL DEFAULT 0.0,
                    average_message_length REAL DEFAULT 0.0,
                    total_word_count INTEGER DEFAULT 0,
                    provider_usage TEXT DEFAULT '{}',
                    sentiment_history TEXT DEFAULT '[]',
                    average_sentiment TEXT DEFAULT NULL
                )
            """)
            
            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analytics_conversation_id ON conversation_analytics (conversation_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON conversation_analytics (user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON conversation_analytics (created_at)")
            
            await db.commit()
        
        self._initialized = True
    
    async def save_analytics(self, analytics: ConversationAnalytics) -> None:
        """Save or update conversation analytics."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Serialize complex data
                provider_usage_json = json.dumps({
                    provider.value: count 
                    for provider, count in analytics.provider_usage.items()
                })
                
                sentiment_history_json = json.dumps([
                    {
                        "sentiment": s.sentiment.value,
                        "polarity": s.polarity,
                        "subjectivity": s.subjectivity,
                        "confidence": s.confidence
                    }
                    for s in analytics.sentiment_history
                ])
                
                average_sentiment_json = None
                if analytics.average_sentiment:
                    average_sentiment_json = json.dumps({
                        "sentiment": analytics.average_sentiment.sentiment.value,
                        "polarity": analytics.average_sentiment.polarity,
                        "subjectivity": analytics.average_sentiment.subjectivity,
                        "confidence": analytics.average_sentiment.confidence
                    })
                
                # Insert or update analytics
                await db.execute("""
                    INSERT OR REPLACE INTO conversation_analytics 
                    (id, conversation_id, user_id, created_at, updated_at,
                     total_messages, total_tokens_used, total_cost_usd,
                     average_response_time_ms, average_message_length, total_word_count,
                     provider_usage, sentiment_history, average_sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analytics.id,
                    analytics.conversation_id,
                    analytics.user_id,
                    analytics.created_at.isoformat(),
                    analytics.updated_at.isoformat(),
                    analytics.total_messages,
                    analytics.total_tokens_used,
                    analytics.total_cost_usd,
                    analytics.average_response_time_ms,
                    analytics.average_message_length,
                    analytics.total_word_count,
                    provider_usage_json,
                    sentiment_history_json,
                    average_sentiment_json
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save analytics {analytics.id}: {e}")
            raise
    
    async def get_analytics_by_conversation_id(
        self, 
        conversation_id: str
    ) -> Optional[ConversationAnalytics]:
        """Get analytics for specific conversation."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT id, conversation_id, user_id, created_at, updated_at,
                           total_messages, total_tokens_used, total_cost_usd,
                           average_response_time_ms, average_message_length, total_word_count,
                           provider_usage, sentiment_history, average_sentiment
                    FROM conversation_analytics WHERE conversation_id = ?
                """, (conversation_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    return self._row_to_analytics(row)
                    
        except Exception as e:
            logger.error(f"Failed to get analytics for conversation {conversation_id}: {e}")
            raise
    
    async def get_user_analytics_summary(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user analytics summary for specified days."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Get aggregated data
                async with db.execute("""
                    SELECT 
                        COUNT(*) as total_conversations,
                        SUM(total_messages) as total_messages,
                        SUM(total_tokens_used) as total_tokens,
                        SUM(total_cost_usd) as total_cost,
                        AVG(average_response_time_ms) as avg_response_time,
                        provider_usage,
                        sentiment_history
                    FROM conversation_analytics 
                    WHERE user_id = ? AND created_at >= ?
                """, (user_id, start_date.isoformat())) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row or row[0] == 0:
                        return self._empty_summary()
                    
                    # Parse provider usage
                    provider_usage = {}
                    if row[5]:
                        provider_data = json.loads(row[5])
                        for provider_str, count in provider_data.items():
                            try:
                                provider = LLMProvider(provider_str)
                                provider_usage[provider] = count
                            except ValueError:
                                continue
                    
                    # Parse sentiment history
                    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
                    if row[6]:
                        sentiment_history = json.loads(row[6])
                        for sentiment_data in sentiment_history:
                            sentiment = sentiment_data.get("sentiment", "neutral")
                            sentiment_distribution[sentiment] += 1
                    
                    # Find most used provider
                    most_used_provider = None
                    if provider_usage:
                        most_used_provider = max(provider_usage.items(), key=lambda x: x[1])[0].value
                    
                    return {
                        "total_conversations": row[0] or 0,
                        "total_messages": row[1] or 0,
                        "total_tokens": row[2] or 0,
                        "total_cost": row[3] or 0.0,
                        "avg_response_time": row[4] or 0.0,
                        "provider_distribution": {p.value: c for p, c in provider_usage.items()},
                        "most_used_provider": most_used_provider,
                        "sentiment_distribution": sentiment_distribution,
                        "activity_trend": await self._calculate_activity_trend(user_id, days, db)
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get user analytics summary for {user_id}: {e}")
            return self._empty_summary()
    
    async def get_global_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get global analytics summary for specified days."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Get aggregated data
                async with db.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as total_users,
                        COUNT(*) as total_conversations,
                        SUM(total_messages) as total_messages,
                        SUM(total_tokens_used) as total_tokens,
                        SUM(total_cost_usd) as total_cost,
                        AVG(average_response_time_ms) as avg_response_time
                    FROM conversation_analytics 
                    WHERE created_at >= ?
                """, (start_date.isoformat(),)) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row or row[0] == 0:
                        return self._empty_global_summary()
                    
                    # Get provider distribution
                    provider_distribution = await self._get_global_provider_distribution(db, start_date)
                    
                    # Get sentiment distribution
                    sentiment_distribution = await self._get_global_sentiment_distribution(db, start_date)
                    
                    # Get daily activity
                    daily_activity = await self._get_daily_activity(db, start_date, end_date)
                    
                    return {
                        "total_users": row[0] or 0,
                        "total_conversations": row[1] or 0,
                        "total_messages": row[2] or 0,
                        "total_tokens": row[3] or 0,
                        "total_cost": row[4] or 0.0,
                        "avg_response_time": row[5] or 0.0,
                        "provider_distribution": provider_distribution,
                        "sentiment_distribution": sentiment_distribution,
                        "daily_activity": daily_activity,
                        "avg_messages_per_user": (row[2] or 0) / (row[0] or 1)
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get global analytics summary: {e}")
            return self._empty_global_summary()
    
    def _row_to_analytics(self, row) -> ConversationAnalytics:
        """Convert database row to ConversationAnalytics object."""
        # Parse provider usage
        provider_usage = {}
        if row[11]:  # provider_usage
            provider_data = json.loads(row[11])
            for provider_str, count in provider_data.items():
                try:
                    provider = LLMProvider(provider_str)
                    provider_usage[provider] = count
                except ValueError:
                    continue
        
        # Parse sentiment history
        sentiment_history = []
        if row[12]:  # sentiment_history
            sentiment_data = json.loads(row[12])
            for s_data in sentiment_data:
                sentiment = SentimentAnalysis(
                    sentiment=SentimentType(s_data["sentiment"]),
                    polarity=s_data["polarity"],
                    subjectivity=s_data["subjectivity"],
                    confidence=s_data["confidence"]
                )
                sentiment_history.append(sentiment)
        
        # Parse average sentiment
        average_sentiment = None
        if row[13]:  # average_sentiment
            avg_data = json.loads(row[13])
            average_sentiment = SentimentAnalysis(
                sentiment=SentimentType(avg_data["sentiment"]),
                polarity=avg_data["polarity"],
                subjectivity=avg_data["subjectivity"],
                confidence=avg_data["confidence"]
            )
        
        return ConversationAnalytics(
            id=row[0],
            conversation_id=row[1],
            user_id=row[2],
            created_at=datetime.fromisoformat(row[3]),
            updated_at=datetime.fromisoformat(row[4]),
            total_messages=row[5],
            total_tokens_used=row[6],
            total_cost_usd=row[7],
            average_response_time_ms=row[8],
            average_message_length=row[9],
            total_word_count=row[10],
            provider_usage=provider_usage,
            sentiment_history=sentiment_history,
            average_sentiment=average_sentiment
        )
    
    async def _get_global_provider_distribution(
        self, 
        db: aiosqlite.Connection, 
        start_date: datetime
    ) -> Dict[str, int]:
        """Get global provider usage distribution."""
        try:
            async with db.execute("""
                SELECT provider_usage FROM conversation_analytics 
                WHERE created_at >= ?
            """, (start_date.isoformat(),)) as cursor:
                rows = await cursor.fetchall()
                
                provider_distribution = {}
                for row in rows:
                    if row[0]:
                        provider_data = json.loads(row[0])
                        for provider_str, count in provider_data.items():
                            provider_distribution[provider_str] = provider_distribution.get(provider_str, 0) + count
                
                return provider_distribution
                
        except Exception as e:
            logger.warning(f"Failed to get provider distribution: {e}")
            return {}
    
    async def _get_global_sentiment_distribution(
        self, 
        db: aiosqlite.Connection, 
        start_date: datetime
    ) -> Dict[str, int]:
        """Get global sentiment distribution."""
        try:
            async with db.execute("""
                SELECT sentiment_history FROM conversation_analytics 
                WHERE created_at >= ?
            """, (start_date.isoformat(),)) as cursor:
                rows = await cursor.fetchall()
                
                sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
                for row in rows:
                    if row[0]:
                        sentiment_data = json.loads(row[0])
                        for s_data in sentiment_data:
                            sentiment = s_data.get("sentiment", "neutral")
                            sentiment_distribution[sentiment] += 1
                
                return sentiment_distribution
                
        except Exception as e:
            logger.warning(f"Failed to get sentiment distribution: {e}")
            return {"positive": 0, "negative": 0, "neutral": 0}
    
    async def _get_daily_activity(
        self, 
        db: aiosqlite.Connection, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily activity data."""
        try:
            async with db.execute("""
                SELECT DATE(created_at) as date, 
                       COUNT(*) as conversations,
                       SUM(total_messages) as messages,
                       SUM(total_tokens_used) as tokens
                FROM conversation_analytics 
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat())) as cursor:
                rows = await cursor.fetchall()
                
                daily_activity = []
                for row in rows:
                    daily_activity.append({
                        "date": row[0],
                        "conversations": row[1],
                        "messages": row[2] or 0,
                        "tokens": row[3] or 0
                    })
                
                return daily_activity
                
        except Exception as e:
            logger.warning(f"Failed to get daily activity: {e}")
            return []
    
    async def _calculate_activity_trend(
        self, 
        user_id: str, 
        days: int, 
        db: aiosqlite.Connection
    ) -> str:
        """Calculate user activity trend."""
        try:
            # Get activity for first and second half of period
            mid_date = datetime.utcnow() - timedelta(days=days//2)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # First half
            async with db.execute("""
                SELECT COUNT(*) FROM conversation_analytics 
                WHERE user_id = ? AND created_at >= ? AND created_at < ?
            """, (user_id, start_date.isoformat(), mid_date.isoformat())) as cursor:
                first_half = (await cursor.fetchone())[0] or 0
            
            # Second half
            async with db.execute("""
                SELECT COUNT(*) FROM conversation_analytics 
                WHERE user_id = ? AND created_at >= ?
            """, (user_id, mid_date.isoformat())) as cursor:
                second_half = (await cursor.fetchone())[0] or 0
            
            if second_half > first_half * 1.2:
                return "increasing"
            elif second_half < first_half * 0.8:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.warning(f"Failed to calculate activity trend: {e}")
            return "unknown"
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary for user with no data."""
        return {
            "total_conversations": 0,
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0,
            "provider_distribution": {},
            "most_used_provider": None,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "activity_trend": "stable"
        }
    
    def _empty_global_summary(self) -> Dict[str, Any]:
        """Return empty summary for platform with no data."""
        return {
            "total_users": 0,
            "total_conversations": 0,
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0,
            "provider_distribution": {},
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "daily_activity": [],
            "avg_messages_per_user": 0.0
        }
