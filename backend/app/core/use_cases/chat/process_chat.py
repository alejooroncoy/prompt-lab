"""
Chat Processing Use Case.
Orchestrates chat workflow with LLM providers and analytics.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ...entities.conversation import Conversation, Message, MessageRole
from ...entities.analytics import LLMProvider, ConversationAnalytics
from ...ports.llm_port import LLMRepository, LLMRequest, LLMResponse
from ...ports.repository_port import ConversationRepositoryPort, AnalyticsRepositoryPort
from ...ports.analytics_port import AnalyticsPort

logger = logging.getLogger(__name__)


@dataclass
class ChatRequest:
    """Request structure for chat processing."""
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    preferred_provider: Optional[LLMProvider] = None
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Validate request invariants."""
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.message.strip():
            raise ValueError("Message cannot be empty")


@dataclass
class ChatResponse:
    """Response structure for chat processing."""
    conversation_id: str
    user_message: Message
    assistant_message: Message
    provider_used: LLMProvider
    response_time_ms: float
    tokens_used: int
    cost_usd: float
    sentiment_analysis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None


class ChatUseCase:
    """
    Chat processing use case.
    Orchestrates the complete chat workflow including LLM generation and analytics.
    """
    
    def __init__(
        self,
        llm_repository: LLMRepository,
        conversation_repo: ConversationRepositoryPort,
        analytics_repo: AnalyticsRepositoryPort,
        analytics_service: AnalyticsPort
    ):
        """
        Initialize chat use case with dependencies.
        
        Args:
            llm_repository: LLM provider repository
            conversation_repo: Conversation data repository
            analytics_repo: Analytics data repository
            analytics_service: Analytics service for sentiment analysis
        """
        self._llm_repo = llm_repository
        self._conversation_repo = conversation_repo
        self._analytics_repo = analytics_repo
        self._analytics_service = analytics_service
    
    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Execute chat processing workflow.
        
        Args:
            request: Chat request with user message and context
            
        Returns:
            Chat response with assistant message and metrics
            
        Raises:
            ValueError: For invalid request data
            Exception: For processing errors
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Load or create conversation
            conversation = await self._load_conversation(request)
            
            # Step 2: Create user message
            user_message = Message.create_user_message(
                content=request.message,
                metadata=request.metadata or {}
            )
            
            # Step 3: Add user message to conversation
            conversation.add_message(user_message)
            
            # Step 4: Build LLM request
            llm_request = await self._build_llm_request(conversation, request)
            
            # Step 5: Generate AI response
            llm_response = await self._llm_repo.generate_with_fallback(
                llm_request,
                preferred_provider=request.preferred_provider
            )
            
            # Step 6: Create assistant message
            assistant_message = Message.create_assistant_message(
                content=llm_response.content,
                metadata={
                    "provider": llm_response.provider.value,
                    "model_name": llm_response.model_name,
                    "tokens_used": llm_response.metrics.tokens_used,
                    "response_time_ms": llm_response.metrics.response_time_ms,
                    "cost_usd": llm_response.metrics.cost_usd,
                    **(llm_response.metadata or {})
                }
            )
            
            # Step 7: Add assistant message to conversation
            conversation.add_message(assistant_message)
            
            # Step 8: Perform sentiment analysis
            sentiment_analysis = await self._analyze_sentiment(assistant_message.content)
            
            # Step 9: Update analytics
            await self._update_analytics(conversation, llm_response, sentiment_analysis)
            
            # Step 10: Persist conversation
            await self._conversation_repo.save_conversation(conversation)
            
            # Step 11: Calculate response metrics
            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Step 12: Create response
            return ChatResponse(
                conversation_id=conversation.id,
                user_message=user_message,
                assistant_message=assistant_message,
                provider_used=llm_response.provider,
                response_time_ms=response_time_ms,
                tokens_used=llm_response.metrics.tokens_used,
                cost_usd=llm_response.metrics.cost_usd,
                sentiment_analysis=sentiment_analysis,
                metadata={
                    "model_name": llm_response.model_name,
                    "tokens_input": llm_response.metrics.tokens_input,
                    "tokens_output": llm_response.metrics.tokens_output,
                    "tokens_per_second": llm_response.metrics.tokens_per_second,
                }
            )
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            raise
    
    async def _load_conversation(self, request: ChatRequest) -> Conversation:
        """Load existing conversation or create new one."""
        if request.conversation_id:
            conversation = await self._conversation_repo.get_conversation_by_id(
                request.conversation_id
            )
            if not conversation:
                raise ValueError(f"Conversation {request.conversation_id} not found")
            return conversation
        else:
            # Create new conversation
            return Conversation.create_new(
                user_id=request.user_id,
                title=f"Conversación - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            )
    
    async def _build_llm_request(
        self, 
        conversation: Conversation, 
        request: ChatRequest
    ) -> LLMRequest:
        """Build LLM request with conversation context."""
        # Get recent conversation history
        recent_messages = conversation.get_recent_messages(limit=10)
        
        # Build context
        context = {
            "user_id": request.user_id,
            "conversation_id": conversation.id,
            "history": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in recent_messages
            ]
        }
        
        # Add template variables if using template
        if request.template_variables:
            context["template_variables"] = request.template_variables
        
        # Add metadata
        if request.metadata:
            context["metadata"] = request.metadata
        
        return LLMRequest(
            prompt=request.message,
            context=context,
            max_tokens=2048,
            temperature=0.7
        )
    
    async def _analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment of assistant response."""
        try:
            from app.core.ports.analytics_port import AnalyticsRequest
            
            sentiment_request = AnalyticsRequest(text=text)
            sentiment_result = await self._analytics_service.analyze_sentiment(sentiment_request)
            
            return {
                "sentiment": sentiment_result.sentiment.value,
                "polarity": sentiment_result.polarity,
                "subjectivity": sentiment_result.subjectivity,
                "confidence": sentiment_result.confidence
            }
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return None
    
    async def _update_analytics(
        self,
        conversation: Conversation,
        llm_response: LLMResponse,
        sentiment_analysis: Optional[Dict[str, Any]]
    ) -> None:
        """Update conversation analytics."""
        try:
            # Get or create analytics
            analytics = await self._analytics_repo.get_analytics_by_conversation_id(
                conversation.id
            )
            
            if not analytics:
                analytics = ConversationAnalytics.create_for_conversation(
                    conversation_id=conversation.id,
                    user_id=conversation.user_id
                )
            
            # Add response metrics
            analytics.add_response_metrics(llm_response.metrics)
            
            # Add sentiment analysis if available
            if sentiment_analysis:
                from ...entities.analytics import SentimentAnalysis, SentimentType
                
                sentiment_result = SentimentAnalysis(
                    sentiment=SentimentType(sentiment_analysis["sentiment"]),
                    polarity=sentiment_analysis["polarity"],
                    subjectivity=sentiment_analysis["subjectivity"],
                    confidence=sentiment_analysis["confidence"]
                )
                analytics.add_sentiment_analysis(sentiment_result)
            
            # Update message stats
            analytics.update_message_stats(
                message_count=conversation.message_count,
                word_count=sum(msg.word_count for msg in conversation.messages)
            )
            
            # Save analytics
            await self._analytics_repo.save_analytics(analytics)
            
        except Exception as e:
            logger.warning(f"Analytics update failed: {e}")
            # Don't fail the chat if analytics fails
