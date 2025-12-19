"""
Remix Service

Handles timeline modifications ("what if" scenarios) and comparisons.

Core functionality:
1. Save timeline snapshots for comparison
2. Calculate personality and symptom differences
3. Generate comparison summaries
4. Support multiple remix scenarios per persona
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
import logging

from app.models.persona import Persona
from app.models.experience import Experience
from app.models.intervention import Intervention
from app.models.personality_snapshot import PersonalitySnapshot
from app.models.timeline_snapshot import TimelineSnapshot
from app.models.clinical_template import ClinicalTemplate

logger = logging.getLogger(__name__)


class RemixValidationError(Exception):
    """Raised when remix parameters are invalid"""
    pass


def create_timeline_snapshot(
    db: Session,
    persona_id: UUID,
    label: str,
    description: Optional[str] = None,
    template_id: Optional[str] = None,
    modifications: Optional[List[Dict]] = None
) -> TimelineSnapshot:
    """
    Create a snapshot of current persona timeline state.
    
    This captures:
    - Current personality profile
    - Current trauma markers and symptoms
    - Which experiences/interventions were applied
    - How this differs from baseline or other snapshots
    
    Args:
        db: Database session
        persona_id: Persona to snapshot
        label: Human-readable label (e.g., "Original", "With Early DBT")
        description: Optional detailed description
        template_id: Optional template this persona was created from
        modifications: Optional list of modifications made
        
    Returns:
        Created TimelineSnapshot object
    """
    # Get persona with all related data
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise ValueError(f"Persona {persona_id} not found")
    
    # Get all experiences and interventions
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()
    
    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.age_at_intervention).all()
    
    # Build modified experiences list
    modified_experiences = [
        {
            "sequence_number": exp.sequence_number,
            "age_at_event": exp.age_at_event,
            "description": exp.user_description,
            "symptoms_developed": exp.symptoms_developed,
            "symptom_severity": exp.symptom_severity
        }
        for exp in experiences
    ]
    
    # Build modified interventions list
    modified_interventions = [
        {
            "age_at_intervention": intv.age_at_intervention,
            "therapy_type": intv.therapy_type,
            "duration": intv.duration,
            "target_symptoms": intv.target_symptoms
        }
        for intv in interventions
    ]
    
    # Calculate symptom severity snapshot
    symptom_severity_snapshot = {}
    for exp in experiences:
        if exp.symptom_severity:
            for symptom, severity in exp.symptom_severity.items():
                # Keep highest severity for each symptom
                if symptom not in symptom_severity_snapshot or severity > symptom_severity_snapshot[symptom]:
                    symptom_severity_snapshot[symptom] = severity
    
    # Calculate differences from baseline
    personality_difference = {
        trait: persona.current_personality[trait] - persona.baseline_personality[trait]
        for trait in persona.current_personality.keys()
    }
    
    # Create snapshot
    snapshot = TimelineSnapshot(
        id=str(uuid4()),
        persona_id=persona_id,
        template_id=template_id,
        label=label,
        description=description,
        modified_experiences=modified_experiences,
        modified_interventions=modified_interventions if modified_interventions else None,
        personality_snapshot=dict(persona.current_personality),
        trauma_markers_snapshot=list(persona.current_trauma_markers) if persona.current_trauma_markers else None,
        symptom_severity_snapshot=symptom_severity_snapshot if symptom_severity_snapshot else None,
        personality_difference=personality_difference,
        symptom_difference=None  # Could calculate vs baseline symptoms if tracked
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return snapshot


def get_persona_snapshots(
    db: Session,
    persona_id: UUID
) -> List[TimelineSnapshot]:
    """
    Get all timeline snapshots for a persona.
    
    Args:
        db: Database session
        persona_id: Persona ID
        
    Returns:
        List of TimelineSnapshot objects ordered by creation time
    """
    snapshots = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.persona_id == persona_id
    ).order_by(TimelineSnapshot.created_at).all()
    
    return snapshots


def compare_snapshots(
    db: Session,
    snapshot_id_1: str,
    snapshot_id_2: str
) -> Dict:
    """
    Compare two timeline snapshots.
    
    Calculates:
    - Personality trait differences
    - Symptom presence differences
    - Symptom severity differences
    - Natural language summary
    
    Args:
        db: Database session
        snapshot_id_1: First snapshot ID
        snapshot_id_2: Second snapshot ID
        
    Returns:
        Comparison dictionary with differences and summary
    """
    # Get snapshots
    snapshot_1 = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.id == snapshot_id_1
    ).first()
    
    snapshot_2 = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.id == snapshot_id_2
    ).first()
    
    if not snapshot_1 or not snapshot_2:
        raise ValueError("One or both snapshots not found")
    
    # Calculate personality differences
    personality_differences = {}
    for trait in snapshot_1.personality_snapshot.keys():
        val_1 = snapshot_1.personality_snapshot[trait]
        val_2 = snapshot_2.personality_snapshot[trait]
        personality_differences[trait] = {
            "snapshot_1": val_1,
            "snapshot_2": val_2,
            "difference": val_2 - val_1,
            "change_direction": "increased" if val_2 > val_1 else "decreased" if val_2 < val_1 else "unchanged"
        }
    
    # Calculate symptom differences
    symptoms_1 = set(snapshot_1.trauma_markers_snapshot or [])
    symptoms_2 = set(snapshot_2.trauma_markers_snapshot or [])
    
    symptoms_only_in_1 = symptoms_1 - symptoms_2
    symptoms_only_in_2 = symptoms_2 - symptoms_1
    symptoms_in_both = symptoms_1 & symptoms_2
    
    # Calculate symptom severity differences
    symptom_severity_differences = {}
    severity_1 = snapshot_1.symptom_severity_snapshot or {}
    severity_2 = snapshot_2.symptom_severity_snapshot or {}
    
    all_symptoms = set(severity_1.keys()) | set(severity_2.keys())
    for symptom in all_symptoms:
        sev_1 = severity_1.get(symptom, 0)
        sev_2 = severity_2.get(symptom, 0)
        symptom_severity_differences[symptom] = {
            "snapshot_1": sev_1,
            "snapshot_2": sev_2,
            "difference": sev_2 - sev_1
        }
    
    # Generate natural language summary
    summary_parts = []
    
    # Personality summary
    significant_personality_changes = [
        trait for trait, diff in personality_differences.items()
        if abs(diff["difference"]) >= 0.1  # 10% change threshold
    ]
    
    if significant_personality_changes:
        trait_descriptions = []
        for trait in significant_personality_changes:
            diff = personality_differences[trait]
            direction = "increased" if diff["difference"] > 0 else "decreased"
            magnitude = abs(diff["difference"])
            if magnitude >= 0.3:
                intensity = "significantly"
            elif magnitude >= 0.2:
                intensity = "moderately"
            else:
                intensity = "slightly"
            
            trait_descriptions.append(f"{trait} {intensity} {direction} ({diff['difference']:+.2f})")
        
        summary_parts.append(f"Personality changes: {', '.join(trait_descriptions)}.")
    else:
        summary_parts.append("No significant personality changes observed.")
    
    # Symptom summary
    if symptoms_only_in_2:
        summary_parts.append(f"New symptoms in {snapshot_2.label}: {', '.join(symptoms_only_in_2)}.")
    
    if symptoms_only_in_1:
        summary_parts.append(f"Symptoms resolved in {snapshot_2.label}: {', '.join(symptoms_only_in_1)}.")
    
    if not symptoms_only_in_1 and not symptoms_only_in_2 and symptoms_in_both:
        summary_parts.append(f"Symptoms remain consistent: {len(symptoms_in_both)} symptoms present in both.")
    
    # Severity summary
    severity_improved = [s for s, d in symptom_severity_differences.items() if d["difference"] < -2]
    severity_worsened = [s for s, d in symptom_severity_differences.items() if d["difference"] > 2]
    
    if severity_improved:
        summary_parts.append(f"Symptom severity improved for: {', '.join(severity_improved)}.")
    
    if severity_worsened:
        summary_parts.append(f"Symptom severity worsened for: {', '.join(severity_worsened)}.")
    
    summary = " ".join(summary_parts)
    
    return {
        "snapshot_1": {
            "id": snapshot_1.id,
            "label": snapshot_1.label,
            "personality": snapshot_1.personality_snapshot,
            "symptoms": list(symptoms_1),
            "symptom_severity": severity_1
        },
        "snapshot_2": {
            "id": snapshot_2.id,
            "label": snapshot_2.label,
            "personality": snapshot_2.personality_snapshot,
            "symptoms": list(symptoms_2),
            "symptom_severity": severity_2
        },
        "personality_differences": personality_differences,
        "symptom_differences": {
            "only_in_snapshot_1": list(symptoms_only_in_1),
            "only_in_snapshot_2": list(symptoms_only_in_2),
            "in_both": list(symptoms_in_both)
        },
        "symptom_severity_differences": symptom_severity_differences,
        "summary": summary
    }


def calculate_intervention_impact(
    db: Session,
    persona_id: UUID,
    baseline_snapshot_id: str
) -> Dict:
    """
    Calculate the impact of interventions by comparing current state to baseline.
    
    Args:
        db: Database session
        persona_id: Persona ID
        baseline_snapshot_id: Snapshot ID of baseline (pre-intervention) state
        
    Returns:
        Impact analysis dictionary
    """
    # Get baseline snapshot
    baseline = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.id == baseline_snapshot_id
    ).first()
    
    if not baseline:
        raise ValueError(f"Baseline snapshot {baseline_snapshot_id} not found")
    
    # Get current persona state
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise ValueError(f"Persona {persona_id} not found")
    
    # Get all interventions
    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.age_at_intervention).all()
    
    # Calculate personality changes
    personality_changes = {
        trait: {
            "baseline": baseline.personality_snapshot[trait],
            "current": persona.current_personality[trait],
            "change": persona.current_personality[trait] - baseline.personality_snapshot[trait]
        }
        for trait in baseline.personality_snapshot.keys()
    }
    
    # Calculate symptom changes
    baseline_symptoms = set(baseline.trauma_markers_snapshot or [])
    current_symptoms = set(persona.current_trauma_markers or [])
    
    symptoms_resolved = baseline_symptoms - current_symptoms
    symptoms_persisting = baseline_symptoms & current_symptoms
    symptoms_new = current_symptoms - baseline_symptoms
    
    # Calculate symptom severity changes
    baseline_severity = baseline.symptom_severity_snapshot or {}
    
    # Get current severity from latest experience
    latest_experience = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number.desc()).first()
    
    current_severity = latest_experience.symptom_severity if latest_experience else {}
    
    severity_changes = {}
    for symptom in set(baseline_severity.keys()) | set(current_severity.keys()):
        base_sev = baseline_severity.get(symptom, 0)
        curr_sev = current_severity.get(symptom, 0)
        severity_changes[symptom] = {
            "baseline": base_sev,
            "current": curr_sev,
            "change": curr_sev - base_sev,
            "percent_change": ((curr_sev - base_sev) / base_sev * 100) if base_sev > 0 else 0
        }
    
    # Generate intervention effectiveness summary
    effectiveness_summary = []
    
    for intervention in interventions:
        targeted_symptoms = intervention.target_symptoms or []
        improvements = []
        
        for symptom in targeted_symptoms:
            if symptom in symptoms_resolved:
                improvements.append(f"{symptom} resolved")
            elif symptom in severity_changes and severity_changes[symptom]["change"] < 0:
                change = severity_changes[symptom]["percent_change"]
                improvements.append(f"{symptom} reduced by {abs(change):.0f}%")
        
        effectiveness_summary.append({
            "therapy_type": intervention.therapy_type,
            "age_administered": intervention.age_at_intervention,
            "duration": intervention.duration,
            "targeted_symptoms": targeted_symptoms,
            "improvements": improvements if improvements else ["No measurable improvement in targeted symptoms"]
        })
    
    return {
        "persona_id": str(persona_id),
        "baseline_snapshot_id": baseline_snapshot_id,
        "interventions_applied": len(interventions),
        "personality_changes": personality_changes,
        "symptom_changes": {
            "resolved": list(symptoms_resolved),
            "persisting": list(symptoms_persisting),
            "new": list(symptoms_new)
        },
        "severity_changes": severity_changes,
        "intervention_effectiveness": effectiveness_summary
    }


def get_remix_suggestions_for_persona(
    db: Session,
    persona_id: UUID,
    template_id: Optional[str] = None
) -> List[Dict]:
    """
    Get remix suggestions for a persona.
    
    If template_id provided, returns template suggestions.
    Otherwise returns generic suggestions based on persona state.
    
    Args:
        db: Database session
        persona_id: Persona ID
        template_id: Optional template ID
        
    Returns:
        List of remix suggestion dictionaries
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise ValueError(f"Persona {persona_id} not found")
    
    # If template specified, get its suggestions
    if template_id:
        template = db.query(ClinicalTemplate).filter(
            ClinicalTemplate.id == template_id
        ).first()
        
        if template and template.remix_suggestions:
            return template.remix_suggestions
    
    # Otherwise generate generic suggestions based on persona state
    suggestions = []
    
    # Suggestion 1: Add early intervention
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()
    
    if experiences:
        first_negative = next((exp for exp in experiences if exp.symptoms_developed), None)
        if first_negative:
            suggestions.append({
                "title": f"Early Intervention - What if therapy started at age {first_negative.age_at_event}?",
                "changes": [
                    f"Add therapy intervention immediately after first symptoms at age {first_negative.age_at_event}",
                    "Keep all experiences but add therapeutic support"
                ],
                "hypothesis": "Early intervention after first symptoms could prevent escalation and reduce long-term severity."
            })
    
    # Suggestion 2: Remove most severe trauma
    severe_experiences = [exp for exp in experiences if exp.symptoms_developed and len(exp.symptoms_developed) > 2]
    if severe_experiences:
        worst = max(severe_experiences, key=lambda e: len(e.symptoms_developed))
        suggestions.append({
            "title": f"Remove Severe Trauma - What if event at age {worst.age_at_event} didn't happen?",
            "changes": [
                f"Remove experience at age {worst.age_at_event}",
                "Keep all other experiences"
            ],
            "hypothesis": f"Removing this severe trauma might prevent {len(worst.symptoms_developed)} symptoms from developing."
        })
    
    # Suggestion 3: Add protective factor
    if persona.current_age > 10:
        suggestions.append({
            "title": "Add Protective Factor - Supportive Mentor",
            "changes": [
                "Add positive experience at age 10: 'Develops relationship with supportive mentor who validates experiences'",
                "Keep all negative experiences"
            ],
            "hypothesis": "One consistent supportive relationship could provide resilience buffer and reduce symptom severity."
        })
    
    return suggestions


def delete_snapshot(db: Session, snapshot_id: str) -> bool:
    """
    Delete a timeline snapshot.
    
    Args:
        db: Database session
        snapshot_id: Snapshot ID to delete
        
    Returns:
        True if deleted, False if not found
    """
    snapshot = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.id == snapshot_id
    ).first()
    
    if not snapshot:
        return False
    
    db.delete(snapshot)
    db.commit()
    return True
