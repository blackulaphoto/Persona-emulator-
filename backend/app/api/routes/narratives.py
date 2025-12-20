"""
Narrative API Routes

Endpoints for generating and retrieving persona narratives.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services import narrative_service
from app.schemas.narrative_schemas import (
    NarrativeResponse,
    GenerateNarrativeRequest,
    NarrativeListResponse
)

router = APIRouter(prefix="/api/v1/narratives", tags=["narratives"])


@router.post("/personas/{persona_id}/generate", response_model=NarrativeResponse)
async def generate_narrative(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive AI narrative for a persona.

    Analyzes the persona's complete timeline and generates:
    - Executive summary
    - Developmental timeline narrative
    - Current behavioral presentation
    - Treatment response analysis
    - Prognosis and recommendations

    This can take 15-30 seconds as it uses GPT-4.
    """
    try:
        narrative = await narrative_service.generate_persona_narrative(
            db=db,
            persona_id=persona_id,
            user_id=user_id
        )
        
        return NarrativeResponse.from_orm(narrative)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate narrative: {str(e)}"
        )


@router.get("/personas/{persona_id}", response_model=List[NarrativeListResponse])
async def get_persona_narratives(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get all narratives for a persona, ordered by most recent first.

    Use this to show narrative history and track how the narrative
    evolves as the persona develops.
    """
    try:
        narratives = await narrative_service.get_persona_narratives(
            db=db,
            persona_id=persona_id,
            user_id=user_id,
            limit=limit
        )
        
        return [NarrativeListResponse.from_orm(n) for n in narratives]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve narratives: {str(e)}"
        )


@router.get("/{narrative_id}", response_model=NarrativeResponse)
async def get_narrative(
    narrative_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific narrative by ID.
    """
    try:
        narrative = await narrative_service.get_narrative_by_id(
            db=db,
            narrative_id=narrative_id,
            user_id=user_id
        )
        
        return NarrativeResponse.from_orm(narrative)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve narrative: {str(e)}"
        )


@router.delete("/{narrative_id}")
async def delete_narrative(
    narrative_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a narrative.
    """
    try:
        success = await narrative_service.delete_narrative(
            db=db,
            narrative_id=narrative_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Narrative not found")
        
        return {"message": "Narrative deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete narrative: {str(e)}"
        )
