"""
Report Generation Use Case.
Generates comprehensive analytics reports for users and administrators.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ...ports.repository_port import AnalyticsRepositoryPort, ConversationRepositoryPort
from ...ports.analytics_port import AnalyticsPort

logger = logging.getLogger(__name__)


@dataclass
class ReportGenerationRequest:
    """Request structure for report generation."""
    user_id: Optional[str] = None
    report_type: str = "summary"  # summary, detailed, export
    days: int = 30
    include_conversations: bool = True
    include_analytics: bool = True
    include_recommendations: bool = True
    format: str = "json"  # json, csv, pdf


@dataclass
class ReportGenerationResponse:
    """Response structure for report generation."""
    report_id: str
    report_type: str
    generated_at: datetime
    period_days: int
    summary: Dict[str, Any]
    conversations: List[Dict[str, Any]] = None
    analytics: Dict[str, Any] = None
    recommendations: List[str] = None
    export_data: Dict[str, Any] = None


class ReportGenerationUseCase:
    """
    Report generation use case.
    Creates comprehensive reports with analytics, insights, and recommendations.
    """
    
    def __init__(
        self,
        analytics_repo: AnalyticsRepositoryPort,
        conversation_repo: ConversationRepositoryPort,
        analytics_service: AnalyticsPort
    ):
        """
        Initialize report generation use case.
        
        Args:
            analytics_repo: Analytics data repository
            conversation_repo: Conversation data repository
            analytics_service: Analytics service
        """
        self._analytics_repo = analytics_repo
        self._conversation_repo = conversation_repo
        self._analytics_service = analytics_service
    
    async def execute(self, request: ReportGenerationRequest) -> ReportGenerationResponse:
        """
        Execute report generation workflow.
        
        Args:
            request: Report generation request
            
        Returns:
            Generated report with comprehensive data
            
        Raises:
            Exception: For processing errors
        """
        try:
            report_id = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Step 1: Generate summary
            summary = await self._generate_summary(request)
            
            # Step 2: Get conversations if requested
            conversations = None
            if request.include_conversations:
                conversations = await self._get_conversations_data(request)
            
            # Step 3: Get analytics if requested
            analytics = None
            if request.include_analytics:
                analytics = await self._get_analytics_data(request)
            
            # Step 4: Generate recommendations if requested
            recommendations = None
            if request.include_recommendations:
                recommendations = await self._generate_recommendations(
                    summary, analytics, request
                )
            
            # Step 5: Prepare export data if needed
            export_data = None
            if request.format != "json":
                export_data = await self._prepare_export_data(
                    summary, conversations, analytics, request
                )
            
            return ReportGenerationResponse(
                report_id=report_id,
                report_type=request.report_type,
                generated_at=datetime.utcnow(),
                period_days=request.days,
                summary=summary,
                conversations=conversations,
                analytics=analytics,
                recommendations=recommendations,
                export_data=export_data
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise
    
    async def _generate_summary(self, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate report summary."""
        try:
            if request.user_id:
                # User-specific summary
                user_summary = await self._analytics_repo.get_user_analytics_summary(
                    request.user_id, 
                    request.days
                )
                
                conversations = await self._conversation_repo.get_user_conversations(
                    request.user_id, 
                    limit=100
                )
                
                return {
                    "type": "user_summary",
                    "user_id": request.user_id,
                    "period_days": request.days,
                    "total_conversations": len(conversations),
                    "total_messages": user_summary.get("total_messages", 0),
                    "total_tokens_used": user_summary.get("total_tokens", 0),
                    "total_cost_usd": user_summary.get("total_cost", 0.0),
                    "avg_response_time_ms": user_summary.get("avg_response_time", 0.0),
                    "most_used_provider": user_summary.get("most_used_provider"),
                    "activity_level": self._calculate_activity_level(
                        user_summary.get("total_messages", 0), 
                        request.days
                    )
                }
            else:
                # Global summary
                global_summary = await self._analytics_repo.get_global_analytics_summary(
                    request.days
                )
                
                return {
                    "type": "global_summary",
                    "period_days": request.days,
                    "total_users": global_summary.get("total_users", 0),
                    "total_conversations": global_summary.get("total_conversations", 0),
                    "total_messages": global_summary.get("total_messages", 0),
                    "total_tokens_used": global_summary.get("total_tokens", 0),
                    "total_cost_usd": global_summary.get("total_cost", 0.0),
                    "avg_response_time_ms": global_summary.get("avg_response_time", 0.0),
                    "provider_distribution": global_summary.get("provider_distribution", {}),
                    "platform_health": self._calculate_platform_health(global_summary)
                }
                
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            return {"error": str(e)}
    
    async def _get_conversations_data(self, request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Get conversations data for report."""
        try:
            if request.user_id:
                conversations = await self._conversation_repo.get_user_conversations(
                    request.user_id, 
                    limit=50
                )
            else:
                # For global reports, we'd need a different method
                # This is a simplified version
                conversations = []
            
            conversations_data = []
            for conv in conversations:
                # Get analytics for each conversation
                analytics = await self._analytics_repo.get_analytics_by_conversation_id(
                    conv.id
                )
                
                conv_data = {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": conv.message_count,
                    "total_tokens": conv.total_tokens_used,
                    "avg_response_time": conv.average_response_time,
                    "analytics": {
                        "total_cost": analytics.total_cost_usd if analytics else 0.0,
                        "sentiment_trend": analytics.sentiment_trend if analytics else "unknown",
                        "provider_usage": analytics.provider_usage if analytics else {}
                    } if analytics else None
                }
                conversations_data.append(conv_data)
            
            return conversations_data
            
        except Exception as e:
            logger.warning(f"Failed to get conversations data: {e}")
            return []
    
    async def _get_analytics_data(self, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Get detailed analytics data for report."""
        try:
            if request.user_id:
                user_summary = await self._analytics_repo.get_user_analytics_summary(
                    request.user_id, 
                    request.days
                )
                
                return {
                    "user_analytics": user_summary,
                    "provider_breakdown": user_summary.get("provider_distribution", {}),
                    "sentiment_analysis": user_summary.get("sentiment_distribution", {}),
                    "cost_analysis": {
                        "total_cost": user_summary.get("total_cost", 0.0),
                        "avg_cost_per_message": user_summary.get("avg_cost_per_message", 0.0),
                        "cost_trend": user_summary.get("cost_trend", "stable")
                    },
                    "performance_metrics": {
                        "avg_response_time": user_summary.get("avg_response_time", 0.0),
                        "total_tokens": user_summary.get("total_tokens", 0),
                        "efficiency_score": self._calculate_efficiency_score(user_summary)
                    }
                }
            else:
                global_summary = await self._analytics_repo.get_global_analytics_summary(
                    request.days
                )
                
                return {
                    "global_analytics": global_summary,
                    "platform_metrics": {
                        "total_users": global_summary.get("total_users", 0),
                        "total_conversations": global_summary.get("total_conversations", 0),
                        "avg_messages_per_user": global_summary.get("avg_messages_per_user", 0.0),
                        "platform_utilization": self._calculate_platform_utilization(global_summary)
                    }
                }
                
        except Exception as e:
            logger.warning(f"Failed to get analytics data: {e}")
            return {"error": str(e)}
    
    async def _generate_recommendations(
        self, 
        summary: Dict[str, Any], 
        analytics: Dict[str, Any], 
        request: ReportGenerationRequest
    ) -> List[str]:
        """Generate actionable recommendations based on data."""
        recommendations = []
        
        try:
            # Cost optimization recommendations
            if summary.get("total_cost_usd", 0) > 10.0:
                recommendations.append(
                    "Consider using more cost-effective providers for simple queries to reduce costs"
                )
            
            # Performance recommendations
            avg_response_time = summary.get("avg_response_time_ms", 0)
            if avg_response_time > 5000:  # 5 seconds
                recommendations.append(
                    "Response times are high. Consider optimizing prompts or switching to faster providers"
                )
            
            # Usage pattern recommendations
            if request.user_id:
                total_messages = summary.get("total_messages", 0)
                if total_messages > 100:
                    recommendations.append(
                        "High usage detected. Consider using conversation templates for common queries"
                    )
                elif total_messages < 5:
                    recommendations.append(
                        "Low usage detected. Try exploring different prompt templates to increase engagement"
                    )
            
            # Provider diversity recommendations
            if analytics and "provider_breakdown" in analytics:
                provider_dist = analytics["provider_breakdown"]
                if len(provider_dist) == 1:
                    recommendations.append(
                        "Using only one provider. Consider diversifying to improve reliability"
                    )
            
            # Sentiment recommendations
            if analytics and "sentiment_analysis" in analytics:
                sentiment_dist = analytics["sentiment_analysis"]
                negative_count = sentiment_dist.get("negative", 0)
                total_sentiments = sum(sentiment_dist.values())
                
                if total_sentiments > 0 and (negative_count / total_sentiments) > 0.3:
                    recommendations.append(
                        "High negative sentiment detected. Review prompt templates and responses"
                    )
            
            # Default recommendation if no specific issues found
            if not recommendations:
                recommendations.append(
                    "Your usage patterns look healthy. Continue exploring different prompt templates"
                )
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations at this time"]
    
    async def _prepare_export_data(
        self, 
        summary: Dict[str, Any], 
        conversations: List[Dict[str, Any]], 
        analytics: Dict[str, Any], 
        request: ReportGenerationRequest
    ) -> Dict[str, Any]:
        """Prepare data for export in different formats."""
        try:
            if request.format == "csv":
                return {
                    "format": "csv",
                    "summary_csv": self._summary_to_csv(summary),
                    "conversations_csv": self._conversations_to_csv(conversations) if conversations else None,
                    "analytics_csv": self._analytics_to_csv(analytics) if analytics else None
                }
            elif request.format == "pdf":
                return {
                    "format": "pdf",
                    "content": "PDF generation would be implemented here",
                    "note": "PDF export requires additional libraries like reportlab"
                }
            else:
                return {
                    "format": request.format,
                    "note": f"Export format {request.format} not yet implemented"
                }
                
        except Exception as e:
            logger.warning(f"Failed to prepare export data: {e}")
            return {"error": str(e)}
    
    def _calculate_activity_level(self, total_messages: int, days: int) -> str:
        """Calculate user activity level."""
        messages_per_day = total_messages / days if days > 0 else 0
        
        if messages_per_day >= 10:
            return "high"
        elif messages_per_day >= 3:
            return "medium"
        else:
            return "low"
    
    def _calculate_platform_health(self, global_summary: Dict[str, Any]) -> str:
        """Calculate overall platform health."""
        # Simple health calculation based on various metrics
        total_users = global_summary.get("total_users", 0)
        total_conversations = global_summary.get("total_conversations", 0)
        
        if total_users > 0:
            conv_per_user = total_conversations / total_users
            if conv_per_user >= 5:
                return "excellent"
            elif conv_per_user >= 2:
                return "good"
            else:
                return "needs_improvement"
        
        return "insufficient_data"
    
    def _calculate_efficiency_score(self, user_summary: Dict[str, Any]) -> float:
        """Calculate user efficiency score (0-100)."""
        try:
            total_cost = user_summary.get("total_cost", 0.0)
            total_messages = user_summary.get("total_messages", 0)
            avg_response_time = user_summary.get("avg_response_time", 0.0)
            
            if total_messages == 0:
                return 0.0
            
            # Simple efficiency calculation
            cost_efficiency = max(0, 100 - (total_cost * 10))  # Lower cost = higher score
            speed_efficiency = max(0, 100 - (avg_response_time / 100))  # Faster = higher score
            
            return round((cost_efficiency + speed_efficiency) / 2, 1)
            
        except Exception:
            return 0.0
    
    def _calculate_platform_utilization(self, global_summary: Dict[str, Any]) -> float:
        """Calculate platform utilization percentage."""
        try:
            total_users = global_summary.get("total_users", 0)
            total_conversations = global_summary.get("total_conversations", 0)
            
            if total_users == 0:
                return 0.0
            
            # Utilization based on conversations per user
            utilization = min(100.0, (total_conversations / total_users) * 20)
            return round(utilization, 1)
            
        except Exception:
            return 0.0
    
    def _summary_to_csv(self, summary: Dict[str, Any]) -> str:
        """Convert summary to CSV format."""
        csv_lines = ["Metric,Value"]
        for key, value in summary.items():
            if key != "type":
                csv_lines.append(f"{key},{value}")
        return "\n".join(csv_lines)
    
    def _conversations_to_csv(self, conversations: List[Dict[str, Any]]) -> str:
        """Convert conversations to CSV format."""
        if not conversations:
            return "No conversations data"
        
        csv_lines = ["ID,Title,Created At,Message Count,Total Tokens,Avg Response Time"]
        for conv in conversations:
            csv_lines.append(
                f"{conv['id']},{conv['title']},{conv['created_at']},"
                f"{conv['message_count']},{conv['total_tokens']},{conv['avg_response_time']}"
            )
        return "\n".join(csv_lines)
    
    def _analytics_to_csv(self, analytics: Dict[str, Any]) -> str:
        """Convert analytics to CSV format."""
        csv_lines = ["Category,Metric,Value"]
        
        for category, data in analytics.items():
            if isinstance(data, dict):
                for metric, value in data.items():
                    csv_lines.append(f"{category},{metric},{value}")
            else:
                csv_lines.append(f"{category},value,{data}")
        
        return "\n".join(csv_lines)
