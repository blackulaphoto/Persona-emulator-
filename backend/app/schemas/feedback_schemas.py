"""
Feedback Schemas

Pydantic schemas for feedback submission and response.
"""
from pydantic import BaseModel, Field
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    message: str = Field(..., min_length=1, max_length=10000)


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: str
    user_id: str
    message: str
    created_at: datetime
    page_context: str | None = None

    class Config:
        from_attributes = True
