"""User model - legacy, unused.

Predates Firebase auth (see app/core/auth.py): email/hashed_password local
accounts. Nothing in this app writes to this table anymore - every real
user is a verified Firebase UID, stored directly as a plain string on
Persona.user_id/Experience.user_id/Intervention.user_id, not a row here.
Kept only because dropping the table itself is a bigger, separate change
than the Postgres-compatibility fix that removed Persona.user_id's now-
incorrect ForeignKey("users.id") (see that migration/model change) - this
class is intentionally not related to any live code path.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
