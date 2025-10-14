"""
AI Chat schemas
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request for AI chat"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")


class ChatResponse(BaseModel):
    """Response from AI chat"""
    response: str = Field(..., description="AI assistant response")
    tokens_used: int = Field(default=0, description="Total tokens used in this conversation")
