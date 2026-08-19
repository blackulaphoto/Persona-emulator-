"""
Remix Service

Handles timeline modifications ("what if" scenarios) and comparisons.

Core functionality:
1. Save timeline snapshots for comparison
2. Calculate personality and symptom differences
3. Generate comparison summaries
4. Support multiple remix scenarios per persona
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import uuid
import logging

from app.models.persona import Persona
from app.models.experience import Experience
from app.models.intervention import Intervention
from app.models.timeline_snapshot import TimelineSnapshot
from app.models.clinical_template import ClinicalTemplate
from app.models.adaptation_pattern import AdaptationPattern
from app.models.clinical_pattern_hypothesis import ClinicalPatternHypothesis
from app.services.evidence_accumulator import evidence_strength_label

logger = logging.getLogger(__name__)


class RemixValidationError(Exception):
    """Raised when remix parameters are invalid"""
    pass


def create_timeline_snapshot(
    db: Session,
    persona_id: str,
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
        persona_id: Persona ID (String)
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
            "target_symptoms": intv.target_symptoms or intv.actual_symptoms_targeted or []
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

    # Step 9: frozen copies of pattern/hypothesis state at this moment - see
    # app/models/timeline_snapshot.py's docstring for why these are point-in-
    # time copies rather than live references. Always live queries (this
    # function runs against a real DB); they return empty lists in
    # production today only because nothing populates AdaptationPattern/
    # ClinicalPatternHypothesis yet (steps 2-5 aren't wired into a creation
    # route) - see docs/MIGRATION_MAP.md.
    adaptation_patterns = db.query(AdaptationPattern).filter(
        AdaptationPattern.persona_id == persona_id
    ).all()
    adaptation_patterns_snapshot = [
        {
            "pattern_name": p.pattern_name,
            "adaptation_strategy": p.adaptation_strategy,
            "status": p.status,
            "evidence_strength": p.evidence_strength,
        }
        for p in adaptation_patterns
    ]

    clinical_pattern_hypotheses = db.query(ClinicalPatternHypothesis).filter(
        ClinicalPatternHypothesis.persona_id == persona_id
    ).all()
    clinical_pattern_hypotheses_snapshot = [
        {
            "pattern_key": h.pattern_key,
            "tier": h.tier,
            "evidence_strength": h.evidence_strength,
        }
        for h in clinical_pattern_hypotheses
    ]

    # Note: Persona model doesn't store baseline_personality separately
    # The baseline is the initial current_personality when persona was created
    # For comparison purposes, we'll store None and compare snapshots to each other instead
    personality_difference = None

    # Create snapshot
    snapshot = TimelineSnapshot(
        id=str(uuid.uuid4()),
        persona_id=persona_id,
        template_id=template_id,
        label=label,
        description=description,
        modified_experiences=modified_experiences,
        modified_interventions=modified_interventions if modified_interventions else None,
        personality_snapshot=dict(persona.current_personality),
        trauma_markers_snapshot=list(persona.current_trauma_markers) if persona.current_trauma_markers else None,
        symptom_severity_snapshot=symptom_severity_snapshot if symptom_severity_snapshot else None,
        adaptation_patterns_snapshot=adaptation_patterns_snapshot if adaptation_patterns_snapshot else None,
        clinical_pattern_hypotheses_snapshot=clinical_pattern_hypotheses_snapshot if clinical_pattern_hypotheses_snapshot else None,
        state_profile_snapshot=dict(persona.current_state) if persona.current_state else None,
        personality_difference=personality_difference,
        symptom_difference=None
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return snapshot


def get_persona_snapshots(
    db: Session,
    persona_id: str
) -> List[TimelineSnapshot]:
    """
    Get all timeline snapshots for a persona.
    
    Args:
        db: Database session
        persona_id: Persona ID (String)
        
    Returns:
        List of TimelineSnapshot objects ordered by creation time
    """
    snapshots = db.query(TimelineSnapshot).filter(
        TimelineSnapshot.persona_id == persona_id
    ).order_by(TimelineSnapshot.created_at).all()
    
    return snapshots


def _diff_pattern_lists(list_1: List[Dict], list_2: List[Dict], key_field: str) -> Dict:
    """
    Pure diff between two frozen pattern-snapshot lists (adaptation_patterns_
    snapshot or clinical_pattern_hypotheses_snapshot), keyed on key_field
    ("adaptation_strategy" or "pattern_key" - the controlled-vocabulary
    fields, not the evocative pattern_name, so the diff is exact rather than
    fuzzy-matched on a name an AI might phrase slightly differently across
    two generations).
    """
    list_1 = list_1 or []
    list_2 = list_2 or []
    by_key_1 = {p[key_field]: p for p in list_1 if p.get(key_field)}
    by_key_2 = {p[key_field]: p for p in list_2 if p.get(key_field)}

    new_keys = set(by_key_2) - set(by_key_1)
    resolved_keys = set(by_key_1) - set(by_key_2)
    shared_keys = set(by_key_1) & set(by_key_2)

    changed = []
    unchanged = []
    for key in shared_keys:
        p1, p2 = by_key_1[key], by_key_2[key]
        strength_1, strength_2 = p1.get("evidence_strength"), p2.get("evidence_strength")
        status_1, status_2 = p1.get("status"), p2.get("status")
        if strength_1 != strength_2 or status_1 != status_2:
            changed.append({
                key_field: key,
                "snapshot_1": p1,
                "snapshot_2": p2,
                "evidence_strength_change": (
                    (strength_2 - strength_1) if (strength_1 is not None and strength_2 is not None) else None
                ),
            })
        else:
            unchanged.append(key)

    return {
        "new": [by_key_2[k] for k in new_keys],
        "resolved": [by_key_1[k] for k in resolved_keys],
        "changed": changed,
        "unchanged": unchanged,
    }


def _diff_state_profile(state_1: Optional[Dict[str, float]], state_2: Optional[Dict[str, float]]) -> Dict:
    """
    Step 11f: diffs the State tier (Persona.current_state, frozen as
    TimelineSnapshot.state_profile_snapshot) between two snapshots, the same
    way personality_differences below diffs the Trait tier. Unlike
    current_personality (which always carries all five Big Five keys),
    current_state doesn't always carry every STATE_VARIABLES key - a
    variable only appears once something has actually moved it - so this is
    keyed on the UNION of keys present in either snapshot: a variable
    present in only one snapshot is reported as newly/no-longer tracked
    rather than silently skipped or treated as an unearned 0.0.
    """
    state_1 = state_1 or {}
    state_2 = state_2 or {}
    differences = {}
    for key in set(state_1) | set(state_2):
        val_1, val_2 = state_1.get(key), state_2.get(key)
        if val_1 is None or val_2 is None:
            differences[key] = {
                "snapshot_1": val_1,
                "snapshot_2": val_2,
                "difference": None,
                "change_direction": "newly_tracked" if val_1 is None else "no_longer_tracked",
            }
            continue
        differences[key] = {
            "snapshot_1": val_1,
            "snapshot_2": val_2,
            "difference": val_2 - val_1,
            "change_direction": "increased" if val_2 > val_1 else "decreased" if val_2 < val_1 else "unchanged",
        }
    return differences


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

    # Step 9: diff patterns and adaptations, not just Big Five deltas.
    adaptation_pattern_differences = _diff_pattern_lists(
        snapshot_1.adaptation_patterns_snapshot, snapshot_2.adaptation_patterns_snapshot, "adaptation_strategy"
    )
    clinical_pattern_differences = _diff_pattern_lists(
        snapshot_1.clinical_pattern_hypotheses_snapshot, snapshot_2.clinical_pattern_hypotheses_snapshot, "pattern_key"
    )

    # Step 11f: diff the State tier too - the fast-moving counterpart to
    # personality_differences above.
    state_differences = _diff_state_profile(snapshot_1.state_profile_snapshot, snapshot_2.state_profile_snapshot)

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
    
    # State summary (Step 11f) - only variables actually present in both
    # snapshots participate in a "changed" comparison; newly/no-longer-
    # tracked variables are real information but not a "moved by X" claim.
    significant_state_changes = [
        key for key, diff in state_differences.items()
        if diff["difference"] is not None and abs(diff["difference"]) >= 0.1
    ]
    if significant_state_changes:
        state_descriptions = []
        for key in significant_state_changes:
            diff = state_differences[key]
            direction = "increased" if diff["difference"] > 0 else "decreased"
            state_descriptions.append(f"{key} {direction} ({diff['difference']:+.2f})")
        summary_parts.append(f"State changes: {', '.join(state_descriptions)}.")

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

    # Pattern summary - this is the "explain why the trajectories diverge"
    # material the product spec asks for (section 13), not just a number
    # going up or down.
    if adaptation_pattern_differences["new"]:
        names = ", ".join(f'"{p["pattern_name"]}"' for p in adaptation_pattern_differences["new"])
        summary_parts.append(f"New pattern(s) emerged in {snapshot_2.label}: {names}.")

    if adaptation_pattern_differences["resolved"]:
        names = ", ".join(f'"{p["pattern_name"]}"' for p in adaptation_pattern_differences["resolved"])
        summary_parts.append(f"Pattern(s) no longer present in {snapshot_2.label}: {names}.")

    for change in adaptation_pattern_differences["changed"]:
        p1, p2 = change["snapshot_1"], change["snapshot_2"]
        delta = change["evidence_strength_change"]
        direction = "strengthened" if (delta or 0) > 0 else "weakened" if (delta or 0) < 0 else "shifted status"
        summary_parts.append(
            f'"{p2["pattern_name"]}" {direction} ({p1["status"]} → {p2["status"]}, '
            f"evidence: {evidence_strength_label(p1.get('evidence_strength'))} → {evidence_strength_label(p2.get('evidence_strength'))})."
        )

    if not any([adaptation_pattern_differences["new"], adaptation_pattern_differences["resolved"], adaptation_pattern_differences["changed"]]) \
            and (snapshot_1.adaptation_patterns_snapshot or snapshot_2.adaptation_patterns_snapshot):
        summary_parts.append("Developmental patterns remain consistent between the two scenarios.")

    summary = " ".join(summary_parts)

    return {
        "snapshot_1": {
            "id": snapshot_1.id,
            "label": snapshot_1.label,
            "personality": snapshot_1.personality_snapshot,
            "state": snapshot_1.state_profile_snapshot or {},
            "symptoms": list(symptoms_1),
            "symptom_severity": severity_1,
            "adaptation_patterns": snapshot_1.adaptation_patterns_snapshot or [],
            "clinical_pattern_hypotheses": snapshot_1.clinical_pattern_hypotheses_snapshot or [],
        },
        "snapshot_2": {
            "id": snapshot_2.id,
            "label": snapshot_2.label,
            "personality": snapshot_2.personality_snapshot,
            "state": snapshot_2.state_profile_snapshot or {},
            "symptoms": list(symptoms_2),
            "symptom_severity": severity_2,
            "adaptation_patterns": snapshot_2.adaptation_patterns_snapshot or [],
            "clinical_pattern_hypotheses": snapshot_2.clinical_pattern_hypotheses_snapshot or [],
        },
        "personality_differences": personality_differences,
        "state_differences": state_differences,
        "adaptation_pattern_differences": adaptation_pattern_differences,
        "clinical_pattern_differences": clinical_pattern_differences,
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
    persona_id: str,
    baseline_snapshot_id: str
) -> Dict:
    """
    Calculate the impact of interventions by comparing current state to baseline.
    
    Args:
        db: Database session
        persona_id: Persona ID (String)
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
        targeted_symptoms = intervention.target_symptoms or intervention.actual_symptoms_targeted or []
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
        "persona_id": persona_id,
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
    persona_id: str,
    template_id: Optional[str] = None
) -> List[Dict]:
    """
    Get remix suggestions for a persona.
    
    If template_id provided, returns template-specific suggestions.
    Otherwise returns generic suggestions based on persona state.
    
    Args:
        db: Database session
        persona_id: Persona ID (String)
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

    # Suggestion 4 (step 9): target the dominant established pattern
    # directly, not just a generic protective-factor placeholder. Only
    # fires once AdaptationPattern rows actually exist for a persona -
    # currently that's never, in production, since steps 2-5 aren't wired
    # into a creation route yet (see docs/MIGRATION_MAP.md).
    established_patterns = db.query(AdaptationPattern).filter(
        AdaptationPattern.persona_id == persona_id,
        AdaptationPattern.status == "established"
    ).order_by(AdaptationPattern.evidence_strength.desc()).all()

    if established_patterns:
        dominant = established_patterns[0]
        age_phrase = f"age {dominant.first_emerged_age}" if dominant.first_emerged_age is not None else "the pattern's origin"
        suggestions.append({
            "title": f'Interrupt "{dominant.pattern_name}" - What if a protective factor arrived earlier?',
            "changes": [
                f"Add a protective factor active from {age_phrase}, buffering the domains this pattern draws on",
                "Keep the original exposures that gave rise to the pattern",
            ],
            "hypothesis": (
                f'"{dominant.pattern_name}" (adaptive strategy: {dominant.adaptation_strategy}) is currently '
                f"established with {evidence_strength_label(dominant.evidence_strength)} evidence. A protective "
                f"factor present from its origin might change the interpretation that produced it, not just "
                f"soften its later severity."
            ),
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


