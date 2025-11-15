"""
API routes for AI-powered messaging
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from backend.services.ai_message_service import AIMessageService
from backend.core.database import get_db_pool
from backend.security.auth import get_current_user
from backend.core.rate_limiter import limiter, AI_RATE_LIMIT, BATCH_RATE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-messages", tags=["ai-messages"])


# Pydantic models with input validation
from pydantic import Field, field_validator


class MessageAnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="Message to analyze (max 10,000 chars)")
    article_id: Optional[str] = Field(None, max_length=100)
    article_context: Optional[dict] = None  # Fallback if article_id not found

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class MessageGenerateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="Message to respond to (max 10,000 chars)")
    article_id: Optional[str] = Field(None, max_length=100)
    article_context: Optional[dict] = None
    tone: str = Field("friendly", pattern="^(friendly|professional|casual)$")

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class MessageSettingsUpdate(BaseModel):
    auto_reply_enabled: bool
    tone: str = Field("friendly", pattern="^(friendly|professional|casual)$")
    mode: str = Field("draft", pattern="^(auto|draft|notify)$")


class BatchMessageRequest(BaseModel):
    messages: List[dict] = Field(..., max_length=50, description="Max 50 messages per batch")
    tone: str = Field("friendly", pattern="^(friendly|professional|casual)$")

    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if not v:
            raise ValueError('Messages list cannot be empty')
        if len(v) > 50:
            raise ValueError('Cannot process more than 50 messages at once')
        return v


@router.post("/analyze")
@limiter.limit(AI_RATE_LIMIT)
async def analyze_message(
    http_request: Request,
    request: MessageAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """
    Analyze message intent using AI

    Returns intent classification, confidence score, and extracted key information
    """
    try:
        # Get article context
        article_context = request.article_context

        if request.article_id and not article_context:
            # Fetch from database
            async with db.acquire() as conn:
                article = await conn.fetchrow(
                    "SELECT id, title, price, size, condition, category, brand FROM drafts WHERE id = $1 AND user_id = $2",
                    request.article_id,
                    current_user["id"]
                )

                if not article:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Article not found"
                    )

                article_context = dict(article)

        if not article_context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either article_id or article_context must be provided"
            )

        # Analyze with AI
        service = AIMessageService()
        result = await service.analyze_message_intent(request.message, article_context)

        logger.info(f"Message analyzed for user {current_user['id']}: {result.get('intention')}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze message: {str(e)}"
        )


@router.post("/generate-response")
@limiter.limit(AI_RATE_LIMIT)
async def generate_auto_response(
    http_request: Request,
    request: MessageGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """
    Generate AI-powered automatic response

    Returns generated response text with confidence score and intent
    """
    try:
        # Get article context
        article_context = request.article_context

        if request.article_id and not article_context:
            async with db.acquire() as conn:
                article = await conn.fetchrow(
                    "SELECT id, title, price, size, condition, category, brand FROM drafts WHERE id = $1 AND user_id = $2",
                    request.article_id,
                    current_user["id"]
                )

                if not article:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Article not found"
                    )

                article_context = dict(article)

        if not article_context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either article_id or article_context must be provided"
            )

        # Generate response with AI
        service = AIMessageService()
        result = await service.analyze_and_respond(
            request.message,
            article_context,
            request.tone
        )

        logger.info(f"Response generated for user {current_user['id']}: intent={result.get('intention')}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.post("/batch-generate")
@limiter.limit(BATCH_RATE_LIMIT)
async def batch_generate_responses(
    http_request: Request,
    request: BatchMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI responses for multiple messages in batch

    Useful for processing multiple unread messages at once
    """
    try:
        service = AIMessageService()
        results = await service.batch_generate_responses(
            request.messages,
            request.tone
        )

        logger.info(f"Batch generated {len(results)} responses for user {current_user['id']}")
        return {
            "results": results,
            "total": len(results),
            "successful": len([r for r in results if not r.get("error")])
        }

    except Exception as e:
        logger.error(f"Failed to batch generate responses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch generate: {str(e)}"
        )


@router.get("/settings")
async def get_message_settings(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get user's message automation settings"""
    try:
        async with db.acquire() as conn:
            settings = await conn.fetchrow(
                "SELECT auto_reply_enabled, tone, mode, created_at FROM message_settings WHERE user_id = $1",
                current_user["id"]
            )

            if settings:
                return dict(settings)
            else:
                # Return defaults
                return {
                    "auto_reply_enabled": False,
                    "tone": "friendly",
                    "mode": "draft"
                }

    except Exception as e:
        logger.error(f"Failed to fetch message settings: {e}")
        return {
            "auto_reply_enabled": False,
            "tone": "friendly",
            "mode": "draft"
        }


@router.put("/settings")
async def update_message_settings(
    settings: MessageSettingsUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Update user's message automation settings"""
    try:
        # Validate tone
        if settings.tone not in ["friendly", "professional", "casual"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tone. Must be friendly, professional, or casual"
            )

        # Validate mode
        if settings.mode not in ["auto", "draft", "notify"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid mode. Must be auto, draft, or notify"
            )

        async with db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO message_settings (user_id, auto_reply_enabled, tone, mode)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    auto_reply_enabled = $2,
                    tone = $3,
                    mode = $4,
                    updated_at = NOW()
                """,
                current_user["id"],
                settings.auto_reply_enabled,
                settings.tone,
                settings.mode
            )

        logger.info(f"Message settings updated for user {current_user['id']}")
        return {"success": True, "settings": settings.dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update message settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.get("/stats")
async def get_message_stats(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """
    Get messaging statistics (AI-generated count, response rate, etc.)
    """
    try:
        async with db.acquire() as conn:
            # Get total AI-generated messages
            ai_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM ai_messages
                WHERE user_id = $1
                AND created_at >= NOW() - INTERVAL '30 days'
                """,
                current_user["id"]
            )

            return {
                "ai_generated_30d": ai_count or 0
            }

    except Exception as e:
        logger.error(f"Failed to fetch message stats: {e}")
        return {
            "ai_generated_30d": 0
        }
