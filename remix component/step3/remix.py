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
from typing import List
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.feature_flags import FeatureFlags
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
    try:
        persona_uuid = UUID(request.persona_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona ID format"
        )
    
    try:
        snapshot = create_timeline_snapshot(
            db=db,
            persona_id=persona_uuid,
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
    db: Session = Depends(get_db)
):
    """
    Get all timeline snapshots for a persona.
    
    Returns snapshots in chronological order (oldest first).
    """
    try:
        persona_uuid = UUID(persona_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona ID format"
        )
    
    snapshots = get_persona_snapshots(db, persona_uuid)
    return snapshots


# Endpoint 3: Get single snapshot
@router.get("/snapshots/{snapshot_id}", response_model=TimelineSnapshotResponse, dependencies=[Depends(require_remix_feature)])
async def get_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific timeline snapshot.
    """
    from app.models.timeline_snapshot import TimelineSnapshot
    
    snapshot = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.id == snapshot_id
    ).first()
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found"
        )
    
    return snapshot


# Endpoint 4: Compare snapshots
@router.post("/snapshots/compare", dependencies=[Depends(require_remix_feature)])
async def compare_timeline_snapshots(
    request: CompareSnapshotsRequest,
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
    try:
        persona_uuid = UUID(persona_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona ID format"
        )
    
    try:
        impact = calculate_intervention_impact(
            db=db,
            persona_id=persona_uuid,
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
    template_id: str = None,
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
    try:
        persona_uuid = UUID(persona_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona ID format"
        )
    
    try:
        suggestions = get_remix_suggestions_for_persona(
            db=db,
            persona_id=persona_uuid,
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
    db: Session = Depends(get_db)
):
    """
    Delete a timeline snapshot.
    
    Use when cleaning up comparison scenarios.
    """
    deleted = delete_snapshot(db, snapshot_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found"
        )
    
    return {"message": f"Snapshot {snapshot_id} deleted successfully"}
