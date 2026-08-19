"""
Feedback Model

Stores user feedback from research preview limits and other feedback prompts.
"""
from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
import uuid

from app.core.database import Base


class Feedback(Base):
    """User feedback submissions"""
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # index=True already generates ix_feedback_user_id - this used to ALSO be
    # declared explicitly via __table_args__ = (Index('ix_feedback_user_id', ...),),
    # the same index name twice in one table's metadata. That made
    # Base.metadata.create_all() fail with "index ix_feedback_user_id already
    # exists" on ANY fresh database - not a test-collision issue as an earlier
    # pass at docs/MIGRATION_MAP.md incorrectly diagnosed, a real bug that
    # would hit a fresh production deploy too. Confirmed by reproducing
    # create_all() failing standalone, with no other test file involved.
    user_id = Column(String, nullable=False, index=True)  # Firebase UID
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_agent = Column(String, nullable=True)
    page_context = Column(String, nullable=True)
