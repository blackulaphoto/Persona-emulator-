"""Server-authoritative policy for the research-preview persona cap."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import is_dev_auth_bypass_active
from app.core.config import settings
from app.models import Persona

PREVIEW_PERSONA_LIMIT = 3


def is_preview_limit_exempt(user_id: str) -> bool:
    """
    Exempt only a verified Firebase UID configured by the server, or the
    fixed local identity produced by the separately gated dev auth bypass.
    No client-provided role, email, header, or request-body flag is read.
    """
    if is_dev_auth_bypass_active() and user_id == "dev-local-user":
        return True
    return user_id in settings.preview_limit_exempt_user_ids


def enforce_preview_persona_limit(db: Session, user_id: str) -> None:
    if is_preview_limit_exempt(user_id):
        return
    persona_count = db.query(Persona).filter(Persona.user_id == user_id).count()
    if persona_count >= PREVIEW_PERSONA_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"Persona limit reached. Maximum {PREVIEW_PERSONA_LIMIT} personas allowed in research preview.",
        )
