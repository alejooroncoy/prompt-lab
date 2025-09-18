"""
Chat Router.
Handles chat-related API endpoints.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.use_cases.chat.process_chat import ChatUseCase, ChatRequest, ChatResponse
from app.core.use_cases.chat.validate_prompt import PromptValidationUseCase, PromptValidationRequest, PromptValidationResponse
from app.core.entities.analytics import LLMProvider
from app.config.dependencies import (
    get_llm_repository,
    get_conversation_repository,
    get_analytics_repository,
    get_analytics_service,
    get_prompt_template_repository
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessageRequest(BaseModel):
    """Chat message request model."""
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    preferred_provider: Optional[str] = Field(None, description="Preferred LLM provider")
    template_id: Optional[str] = Field(None, description="Prompt template ID to use")
    template_variables: Optional[dict] = Field(None, description="Variables for template")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class ChatMessageResponse(BaseModel):
    """Chat message response model."""
    conversation_id: str
    user_message: dict
    assistant_message: dict
    provider_used: str
    response_time_ms: float
    tokens_used: int
    cost_usd: float
    sentiment_analysis: Optional[dict] = None
    metadata: Optional[dict] = None


class ConversationListResponse(BaseModel):
    """Conversation list response model."""
    conversations: List[dict]
    total: int
    limit: int
    offset: int


class PromptValidationResponseModel(BaseModel):
    """Prompt validation response model for API serialization."""
    is_valid: bool
    rendered_prompt: Optional[str] = None
    required_variables: Optional[List[str]] = None
    missing_variables: Optional[List[str]] = None
    estimated_tokens: int = 0
    validation_errors: Optional[List[str]] = None
    template_info: Optional[dict] = None


class ConversationDetailResponse(BaseModel):
    """Conversation detail response model."""
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[dict]
    metadata: dict


def get_chat_use_case() -> ChatUseCase:
    """Get chat use case with dependencies."""
    return ChatUseCase(
        llm_repository=get_llm_repository(),
        conversation_repo=get_conversation_repository(),
        analytics_repo=get_analytics_repository(),
        analytics_service=get_analytics_service()
    )


def get_prompt_validation_use_case() -> PromptValidationUseCase:
    """Get prompt validation use case with dependencies."""
    return PromptValidationUseCase(
        template_repo=get_prompt_template_repository()
    )


@router.post("/chat/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    """
    Send a chat message and get AI response.
    """
    try:
        # Validate preferred provider
        preferred_provider = None
        if request.preferred_provider:
            try:
                preferred_provider = LLMProvider(request.preferred_provider)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {request.preferred_provider}. Available: {[p.value for p in LLMProvider]}"
                )
        
        # Create chat request
        chat_request = ChatRequest(
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            preferred_provider=preferred_provider,
            template_id=request.template_id,
            template_variables=request.template_variables,
            metadata=request.metadata
        )
        
        # Process chat
        response = await chat_use_case.execute(chat_request)
        
        # Convert to response model
        return ChatMessageResponse(
            conversation_id=response.conversation_id,
            user_message={
                "id": response.user_message.id,
                "role": response.user_message.role.value,
                "content": response.user_message.content,
                "timestamp": response.user_message.timestamp.isoformat(),
                "metadata": response.user_message.metadata
            },
            assistant_message={
                "id": response.assistant_message.id,
                "role": response.assistant_message.role.value,
                "content": response.assistant_message.content,
                "timestamp": response.assistant_message.timestamp.isoformat(),
                "metadata": response.assistant_message.metadata
            },
            provider_used=response.provider_used.value,
            response_time_ms=response.response_time_ms,
            tokens_used=response.tokens_used,
            cost_usd=response.cost_usd,
            sentiment_analysis=response.sentiment_analysis,
            metadata=response.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.get("/chat/conversations/{user_id}", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    conversation_repo = Depends(get_conversation_repository)
):
    """
    Get user's conversations with pagination.
    """
    try:
        conversations = await conversation_repo.get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        conversation_data = []
        for conv in conversations:
            conversation_data.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": conv.message_count,
                "total_tokens": conv.total_tokens_used,
                "avg_response_time": conv.average_response_time
            })
        
        return ConversationListResponse(
            conversations=conversation_data,
            total=len(conversation_data),  # This would be total count in real implementation
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")


@router.get("/chat/conversations/{conversation_id}/detail", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: str,
    conversation_repo = Depends(get_conversation_repository)
):
    """
    Get detailed conversation information.
    """
    try:
        conversation = await conversation_repo.get_conversation_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Convert messages to response format
        messages_data = []
        for msg in conversation.messages:
            messages_data.append({
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            })
        
        return ConversationDetailResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            messages=messages_data,
            metadata=conversation.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.delete("/chat/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_repo = Depends(get_conversation_repository)
):
    """
    Delete a conversation.
    """
    try:
        success = await conversation_repo.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.post("/chat/validate-prompt", response_model=PromptValidationResponseModel)
async def validate_prompt(
    request: PromptValidationRequest,
    validation_use_case: PromptValidationUseCase = Depends(get_prompt_validation_use_case)
):
    """
    Validate and render a prompt template.
    """
    try:
        response = await validation_use_case.execute(request)
        
        # Convert to API response model
        return PromptValidationResponseModel(
            is_valid=response.is_valid,
            rendered_prompt=response.rendered_prompt,
            required_variables=response.required_variables,
            missing_variables=response.missing_variables,
            estimated_tokens=response.estimated_tokens,
            validation_errors=response.validation_errors,
            template_info=response.template_info
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prompt validation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate prompt")


@router.get("/chat/providers")
async def get_available_providers(
    llm_repo = Depends(get_llm_repository)
):
    """
    Get available LLM providers.
    """
    try:
        available_providers = await llm_repo.get_available_providers()
        
        provider_info = []
        for provider in available_providers:
            info = llm_repo.get_provider_info(provider)
            provider_info.append({
                "provider": provider.value,
                "info": info
            })
        
        return {"providers": provider_info}
        
    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get providers")
