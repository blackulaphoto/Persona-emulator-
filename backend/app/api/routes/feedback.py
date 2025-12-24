"""
Feedback API Routes

Endpoints for submitting and managing user feedback.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.feedback import Feedback
from app.schemas.feedback_schemas import FeedbackCreate, FeedbackResponse

router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit user feedback.

    Stores feedback with user context for research preview.
    """
    # Extract user agent from request headers
    user_agent = request.headers.get("user-agent")

    # Create feedback record
    feedback = Feedback(
        user_id=user_id,
        message=feedback_data.message,
        created_at=datetime.utcnow(),
        user_agent=user_agent,
        page_context="persona_limit_modal"
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback
