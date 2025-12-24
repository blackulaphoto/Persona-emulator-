"""
Feedback Model

Stores user feedback from research preview limits and other feedback prompts.
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from datetime import datetime
import uuid

from app.core.database import Base


class Feedback(Base):
    """User feedback submissions"""
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)  # Firebase UID
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_agent = Column(String, nullable=True)
    page_context = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_feedback_user_id', 'user_id'),
    )
