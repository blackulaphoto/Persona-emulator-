"""
Remix API Routes

Endpoints for timeline snapshots and comparisons.
Protected by FEATURE_REMIX_TIMELINE flag.

Allows users to:
1. Save timeline snapshots for comparison
2. Compare different scenarios
3. Analyze intervention impact
4. Get remix suggestions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.feature_flags import FeatureFlags
from app.models.persona import Persona
from app.models.timeline_snapshot import TimelineSnapshot
from app.schemas.template_schemas import (
    CreateTimelineSnapshotRequest,
    TimelineSnapshotResponse,
    CompareSnapshotsRequest,
    CompareSnapshotsResponse,
)
from app.services.remix_service import (
    create_timeline_snapshot,
    get_persona_snapshots,
    compare_snapshots,
    calculate_intervention_impact,
    get_remix_suggestions_for_persona,
    delete_snapshot,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/remix", tags=["remix"])


def _require_owned_persona(db: Session, persona_id: str, user_id: str) -> Persona:
    """
    Resolve persona_id to a Persona this user actually owns, or raise 404.

    Same ownership contract as experiences.py / interventions.py / personas.py:
    identity always comes from the verified get_current_user dependency, never
    from a caller-supplied field, and a persona that exists but belongs to
    someone else 404s exactly like one that doesn't exist at all - existence
    of other users' personas is never disclosed.
    """
    persona = db.query(Persona).filter(
        Persona.id == persona_id, Persona.user_id == user_id
    ).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    return persona


def _require_owned_snapshot(db: Session, snapshot_id: str, user_id: str) -> TimelineSnapshot:
    """
    Resolve snapshot_id to a TimelineSnapshot whose parent persona this user
    owns, or raise 404. Ownership is always resolved server-side by joining
    back through TimelineSnapshot.persona_id -> Persona.user_id - the
    snapshot_id alone is never trusted as sufficient to authorize access.
    """
    snapshot = db.query(TimelineSnapshot).filter(TimelineSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    owned = db.query(Persona).filter(
        Persona.id == snapshot.persona_id, Persona.user_id == user_id
    ).first()
    if not owned:
        # Snapshot exists but belongs to a persona this user doesn't own -
        # same 404 as "doesn't exist" so existence isn't disclosed.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return snapshot


def require_remix_feature():
    """Dependency to check if remix feature is enabled"""
    if not FeatureFlags.is_enabled(FeatureFlags.REMIX_TIMELINE):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remix timeline feature is not enabled. Contact administrator."
        )


# Endpoint 1: Create timeline snapshot
@router.post("/snapshots", response_model=TimelineSnapshotResponse, dependencies=[Depends(require_remix_feature)])
async def create_snapshot(
    request: CreateTimelineSnapshotRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a snapshot of current persona timeline state.
    
    This saves the current personality, symptoms, experiences, and interventions
    so you can later compare different scenarios.
    
    Typical workflow:
    1. Create baseline snapshot ("Original")
    2. Modify timeline (add/remove experiences)
    3. Create new snapshot ("With Early Therapy")
    4. Compare snapshots
    
    Request:
    - persona_id: Persona to snapshot
    - label: Human-readable label (e.g., "Original", "With DBT at 16")
    - description: Optional detailed description
    - template_id: Optional template this was based on
    - modifications: Optional list of changes made
    """
    _require_owned_persona(db, str(request.persona_id), user_id)
    try:
        snapshot = create_timeline_snapshot(
            db=db,
            persona_id=str(request.persona_id),
            label=request.label,
            description=request.description,
            template_id=request.template_id,
            modifications=request.modifications if hasattr(request, 'modifications') else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )
    
    return snapshot


# Endpoint 2: List snapshots for persona
@router.get("/personas/{persona_id}/snapshots", response_model=List[TimelineSnapshotResponse], dependencies=[Depends(require_remix_feature)])
async def list_persona_snapshots(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all timeline snapshots for a persona.

    Returns snapshots in chronological order (oldest first).
    """
    _require_owned_persona(db, str(persona_id), user_id)
    snapshots = get_persona_snapshots(db, str(persona_id))
    return snapshots


# Endpoint 3: Get single snapshot
@router.get("/snapshots/{snapshot_id}", response_model=TimelineSnapshotResponse, dependencies=[Depends(require_remix_feature)])
async def get_snapshot(
    snapshot_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific timeline snapshot.
    """
    snapshot = _require_owned_snapshot(db, snapshot_id, user_id)
    return snapshot


# Endpoint 4: Compare snapshots
@router.post("/snapshots/compare", dependencies=[Depends(require_remix_feature)])
async def compare_timeline_snapshots(
    request: CompareSnapshotsRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare two timeline snapshots side-by-side.
    
    Calculates:
    - Personality trait differences
    - Symptom presence differences  
    - Symptom severity changes
    - Natural language summary
    
    Request:
    - snapshot_id_1: First snapshot ID
    - snapshot_id_2: Second snapshot ID
    
    Returns detailed comparison with before/after analysis.
    """
    # Ownership verified independently for each snapshot - comparing across
    # two of this same user's personas is allowed (no cross-persona
    # restriction here, only ownership), but neither snapshot may belong to
    # someone else.
    _require_owned_snapshot(db, request.snapshot_id_1, user_id)
    _require_owned_snapshot(db, request.snapshot_id_2, user_id)
    try:
        comparison = compare_snapshots(
            db=db,
            snapshot_id_1=request.snapshot_id_1,
            snapshot_id_2=request.snapshot_id_2
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error comparing snapshots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare snapshots: {str(e)}"
        )
    
    return comparison


# Endpoint 5: Calculate intervention impact
@router.get("/personas/{persona_id}/intervention-impact", dependencies=[Depends(require_remix_feature)])
async def get_intervention_impact(
    persona_id: str,
    baseline_snapshot_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate the impact of interventions by comparing current state to baseline.
    
    This analyzes:
    - Which symptoms resolved
    - Which symptoms persisted
    - Personality changes
    - Effectiveness of each intervention
    
    Query params:
    - baseline_snapshot_id: Snapshot taken before interventions
    
    Use case: After applying interventions, compare current state to
    pre-intervention baseline to measure therapeutic impact.
    """
    _require_owned_persona(db, str(persona_id), user_id)
    baseline_snapshot = _require_owned_snapshot(db, baseline_snapshot_id, user_id)
    if baseline_snapshot.persona_id != str(persona_id):
        # Both resources can be independently owned by this same user and
        # still not belong together - a snapshot from one of the caller's
        # OTHER personas is not a valid baseline for this one. Ownership
        # alone isn't the full contract for a nested resource; it has to
        # belong to the specific parent it's being used against.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    try:
        impact = calculate_intervention_impact(
            db=db,
            persona_id=str(persona_id),
            baseline_snapshot_id=baseline_snapshot_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating intervention impact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate intervention impact: {str(e)}"
        )
    
    return impact


# Endpoint 6: Get remix suggestions
@router.get("/personas/{persona_id}/suggestions", dependencies=[Depends(require_remix_feature)])
async def get_remix_suggestions(
    persona_id: str,
    template_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get "what if" remix suggestions for a persona.
    
    If template_id provided, returns template-specific suggestions.
    Otherwise generates suggestions based on persona's current state.
    
    Query params:
    - template_id: Optional template ID for template-specific suggestions
    
    Returns list of suggested timeline modifications to explore.
    """
    _require_owned_persona(db, str(persona_id), user_id)
    try:
        suggestions = get_remix_suggestions_for_persona(
            db=db,
            persona_id=str(persona_id),
            template_id=template_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {"suggestions": suggestions}


# Endpoint 7: Delete snapshot
@router.delete("/snapshots/{snapshot_id}", dependencies=[Depends(require_remix_feature)])
async def delete_timeline_snapshot(
    snapshot_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a timeline snapshot.

    Use when cleaning up comparison scenarios.
    """
    _require_owned_snapshot(db, snapshot_id, user_id)
    deleted = delete_snapshot(db, snapshot_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found"
        )

    return {"message": f"Snapshot {snapshot_id} deleted successfully"}

