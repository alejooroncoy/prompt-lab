"""
Analytics Router.
Handles analytics and reporting API endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.core.use_cases.analytics.track_metrics import AnalyticsTrackingUseCase, MetricsTrackingRequest, MetricsTrackingResponse
from app.core.use_cases.analytics.generate_report import ReportGenerationUseCase, ReportGenerationRequest, ReportGenerationResponse
from app.config.dependencies import (
    get_analytics_repository,
    get_conversation_repository,
    get_analytics_service
)

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response model."""
    user_metrics: Optional[dict] = None
    conversation_metrics: Optional[dict] = None
    global_metrics: Optional[dict] = None
    provider_breakdown: Optional[dict] = None
    sentiment_trends: Optional[dict] = None
    cost_analysis: Optional[dict] = None


class ReportGenerationResponseModel(BaseModel):
    """Report generation response model for API serialization."""
    report_id: str
    report_type: str
    generated_at: str  # ISO format string
    period_days: int
    summary: dict
    conversations: Optional[list] = None
    analytics: Optional[dict] = None
    recommendations: Optional[list] = None
    export_data: Optional[dict] = None


class UserAnalyticsResponse(BaseModel):
    """User analytics response model."""
    user_id: str
    period_days: int
    summary: dict


class ConversationAnalyticsResponse(BaseModel):
    """Conversation analytics response model."""
    conversation_id: str
    analytics: dict


class GlobalAnalyticsResponse(BaseModel):
    """Global analytics response model."""
    period_days: int
    global_summary: dict


class ExportDataResponse(BaseModel):
    """Export data response model."""
    user_id: str
    export_date: str
    period_days: int
    conversations: list
    analytics: dict


class ReportRequest(BaseModel):
    """Report generation request model."""
    user_id: Optional[str] = None
    report_type: str = "summary"
    days: int = 30
    include_conversations: bool = True
    include_analytics: bool = True
    include_recommendations: bool = True
    format: str = "json"


def get_metrics_tracking_use_case() -> AnalyticsTrackingUseCase:
    """Get metrics tracking use case with dependencies."""
    return AnalyticsTrackingUseCase(
        analytics_repo=get_analytics_repository(),
        conversation_repo=get_conversation_repository(),
        analytics_service=get_analytics_service()
    )


def get_report_generation_use_case() -> ReportGenerationUseCase:
    """Get report generation use case with dependencies."""
    return ReportGenerationUseCase(
        analytics_repo=get_analytics_repository(),
        conversation_repo=get_conversation_repository(),
        analytics_service=get_analytics_service()
    )


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    user_id: Optional[str] = Query(None, description="User ID for user-specific analytics"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID for conversation-specific analytics"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    include_global: bool = Query(False, description="Include global platform metrics"),
    metrics_use_case: AnalyticsTrackingUseCase = Depends(get_metrics_tracking_use_case)
):
    """
    Get analytics summary with metrics and trends.
    """
    try:
        # Create metrics tracking request
        request = MetricsTrackingRequest(
            user_id=user_id,
            conversation_id=conversation_id,
            days=days,
            include_global=include_global
        )
        
        # Get metrics
        response = await metrics_use_case.execute(request)
        
        return AnalyticsSummaryResponse(
            user_metrics=response.user_metrics,
            conversation_metrics=response.conversation_metrics,
            global_metrics=response.global_metrics,
            provider_breakdown=response.provider_breakdown,
            sentiment_trends=response.sentiment_trends,
            cost_analysis=response.cost_analysis
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")


@router.get("/analytics/user/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    analytics_repo = Depends(get_analytics_repository)
):
    """
    Get detailed user analytics.
    """
    try:
        user_summary = await analytics_repo.get_user_analytics_summary(user_id, days)
        
        return UserAnalyticsResponse(
            user_id=user_id,
            period_days=days,
            summary=user_summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get user analytics for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analytics")


@router.get("/analytics/conversation/{conversation_id}", response_model=ConversationAnalyticsResponse)
async def get_conversation_analytics(
    conversation_id: str,
    analytics_repo = Depends(get_analytics_repository)
):
    """
    Get detailed conversation analytics.
    """
    try:
        analytics = await analytics_repo.get_analytics_by_conversation_id(conversation_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Analytics not found for conversation")
        
        return ConversationAnalyticsResponse(
            conversation_id=conversation_id,
            analytics={
                "id": analytics.id,
                "user_id": analytics.user_id,
                "total_messages": analytics.total_messages,
                "total_tokens_used": analytics.total_tokens_used,
                "total_cost_usd": analytics.total_cost_usd,
                "average_response_time_ms": analytics.average_response_time_ms,
                "average_message_length": analytics.average_message_length,
                "provider_usage": {p.value: c for p, c in analytics.provider_usage.items()},
                "sentiment_trend": analytics.sentiment_trend,
                "average_sentiment": {
                    "sentiment": analytics.average_sentiment.sentiment.value if analytics.average_sentiment else None,
                    "polarity": analytics.average_sentiment.polarity if analytics.average_sentiment else 0.0,
                    "confidence": analytics.average_sentiment.confidence if analytics.average_sentiment else 0.0
                } if analytics.average_sentiment else None,
                "cost_per_message": analytics.cost_per_message
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation analytics for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation analytics")


@router.get("/analytics/global", response_model=GlobalAnalyticsResponse)
async def get_global_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    analytics_repo = Depends(get_analytics_repository)
):
    """
    Get global platform analytics.
    """
    try:
        global_summary = await analytics_repo.get_global_analytics_summary(days)
        
        return GlobalAnalyticsResponse(
            period_days=days,
            global_summary=global_summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get global analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get global analytics")


@router.post("/analytics/report", response_model=ReportGenerationResponseModel)
async def generate_report(
    request: ReportRequest,
    report_use_case: ReportGenerationUseCase = Depends(get_report_generation_use_case)
):
    """
    Generate comprehensive analytics report.
    """
    try:
        # Create report generation request
        report_request = ReportGenerationRequest(
            user_id=request.user_id,
            report_type=request.report_type,
            days=request.days,
            include_conversations=request.include_conversations,
            include_analytics=request.include_analytics,
            include_recommendations=request.include_recommendations,
            format=request.format
        )
        
        # Generate report
        response = await report_use_case.execute(report_request)
        
        # Convert to API response model
        return ReportGenerationResponseModel(
            report_id=response.report_id,
            report_type=response.report_type,
            generated_at=response.generated_at.isoformat(),
            period_days=response.period_days,
            summary=response.summary,
            conversations=response.conversations,
            analytics=response.analytics,
            recommendations=response.recommendations,
            export_data=response.export_data
        )
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/analytics/export/{user_id}", response_model=ExportDataResponse)
async def export_user_data(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    format: str = Query("json", description="Export format (json, csv)"),
    conversation_repo = Depends(get_conversation_repository),
    analytics_repo = Depends(get_analytics_repository)
):
    """
    Export user data for analysis.
    """
    try:
        # Get user conversations
        conversations = await conversation_repo.get_user_conversations(user_id, limit=1000)
        
        # Get user analytics
        user_analytics = await analytics_repo.get_user_analytics_summary(user_id, days)
        
        # Prepare export data
        export_data = {
            "user_id": user_id,
            "export_date": "2024-01-01T00:00:00Z",  # Would be current timestamp
            "period_days": days,
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": conv.message_count,
                    "total_tokens": conv.total_tokens_used,
                    "avg_response_time": conv.average_response_time,
                    "messages": [
                        {
                            "id": msg.id,
                            "role": msg.role.value,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat(),
                            "word_count": msg.word_count,
                            "character_count": msg.character_count
                        }
                        for msg in conv.messages
                    ]
                }
                for conv in conversations
            ],
            "analytics": user_analytics
        }
        
        if format.lower() == "csv":
            # Convert to CSV format (simplified)
            return ExportDataResponse(
                user_id=user_id,
                export_date="2024-01-01T00:00:00Z",  # Would be current timestamp
                period_days=days,
                conversations=[],
                analytics={"format": "csv", "data": "CSV export would be implemented here", "note": "CSV export requires additional processing"}
            )
        
        return ExportDataResponse(
            user_id=export_data["user_id"],
            export_date=export_data["export_date"],
            period_days=export_data["period_days"],
            conversations=export_data["conversations"],
            analytics=export_data["analytics"]
        )
        
    except Exception as e:
        logger.error(f"Failed to export user data for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")
