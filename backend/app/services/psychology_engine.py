"""
Psychology Engine - AI-powered experience and intervention analysis.

Uses OpenAI GPT-4 + developmental psychology + therapy database to analyze
how life experiences shape personality over time.
"""
import json
import os
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.services.openai_service import OpenAIService
from app.utils.developmental_stages import (
    get_stage_context_for_event,
    explain_developmental_impact,
    calculate_trauma_impact_multiplier
)

# Import for defensive assertion only (not for ORM usage)
from app.models.persona import Persona


# Initialize OpenAI service
openai_service = OpenAIService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4"
)


def generate_experience_prompt(
    persona_data: Dict,
    experience_description: str,
    age_at_event: int,
    previous_experiences: List = None
) -> str:
    """
    Generate AI prompt for experience analysis.
    
    Args:
        persona_data: Dict with persona state (name, baseline_age, baseline_gender, 
                     baseline_background, current_personality, current_attachment_style, 
                     current_trauma_markers)
        experience_description: User's description of the experience
        age_at_event: Age when experience occurred
        previous_experiences: List of previous Experience objects
        
    Returns:
        Formatted prompt string for GPT-4
    """
    if previous_experiences is None:
        previous_experiences = []
    
    # Get developmental context
    dev_context = get_stage_context_for_event(age_at_event, "trauma")
    dev_explanation = explain_developmental_impact(
        age=age_at_event,
        event_type="trauma",
        event_description=experience_description
    )
    
    # Format previous experiences
    previous_context = ""
    if previous_experiences:
        previous_context = "\n\nPREVIOUS EXPERIENCES:\n"
        for exp in previous_experiences:
            previous_context += f"""
Experience #{exp.sequence_number} (age {exp.age_at_event}):
- Description: {exp.user_description}
- Symptoms developed: {exp.symptoms_developed}
- Severity: {exp.symptom_severity}
"""
    
    current_personality = persona_data.get('current_personality', {})
    
    # Build comprehensive prompt
    prompt = f"""You are a clinical psychologist analyzing how a life experience affects personality development.

PERSON CONTEXT:
Name: {persona_data.get('name', 'Unknown')}
Baseline Age: {persona_data.get('baseline_age', 0)}
Current Age: {age_at_event}
Gender: {persona_data.get('baseline_gender', 'Unknown')}
Background: {persona_data.get('baseline_background', 'Unknown')}

CURRENT PERSONALITY (Big Five, 0.0-1.0 scale):
- Openness: {current_personality.get('openness', 0.5)}
- Conscientiousness: {current_personality.get('conscientiousness', 0.5)}
- Extraversion: {current_personality.get('extraversion', 0.5)}
- Agreeableness: {current_personality.get('agreeableness', 0.5)}
- Neuroticism: {current_personality.get('neuroticism', 0.5)}

CURRENT ATTACHMENT STYLE: {persona_data.get('current_attachment_style', 'secure')}
CURRENT TRAUMA MARKERS: {persona_data.get('current_trauma_markers', [])}
{previous_context}

NEW EXPERIENCE (age {age_at_event}):
{experience_description}

{dev_explanation}

ANALYSIS INSTRUCTIONS:
1. **Immediate Effects** - How does this event change Big Five traits? Consider the {dev_context['impact_multiplier']}x impact multiplier.
2. **Long-term Patterns** - What behavioral/relational patterns emerge?
3. **Symptom Development** - What psychological symptoms develop? (anxiety, depression, hypervigilance, trust_issues, etc.)
4. **Symptom Severity** - Rate each symptom 0-10 (apply impact multiplier)
5. **Coping Mechanisms** - What adaptive/maladaptive coping develops?
6. **Worldview Shifts** - How do beliefs about trust, safety, self-worth change? (-1.0 to +1.0)
7. **Cross-Experience Triggers** - Does this reactivate previous experiences?
8. **Recommended Therapies** - Which therapies would address these symptoms? (CBT, ACT, EMDR, IFS, DBT, Somatic_Experiencing, Psychodynamic, ERP)
9. **Evidence-Based Reasoning** - Explain using attachment theory, developmental psychology, trauma research

CRITICAL INSTRUCTIONS:
- Apply the {dev_context['impact_multiplier']}x developmental impact multiplier to all effects
- At age {age_at_event}, person has limited coping capacity (see vulnerability factors above)
- Consider how this affects {dev_context['key_developmental_tasks'][0].replace('_', ' ')}
- If previous experiences exist, check for reactivation/compounding effects
- Be realistic: not all events cause severe symptoms, but developmental stage matters

OUTPUT FORMAT (valid JSON only):
{{
    "immediate_effects": {{
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.4,
        "agreeableness": 0.5,
        "neuroticism": 0.6,
        "trait_changes": {{
            "anxiety": 7,
            "trust_in_relationships": 3,
            "emotional_regulation": 4
        }}
    }},
    "long_term_patterns": [
        "fear_of_abandonment",
        "difficulty_trusting_relationships",
        "hypervigilance_to_conflict"
    ],
    "symptoms_developed": ["anxiety", "trust_issues", "hypervigilance"],
    "symptom_severity": {{
        "anxiety": 6,
        "trust_issues": 7,
        "hypervigilance": 5
    }},
    "coping_mechanisms": [
        "people_pleasing (maladaptive)",
        "hypervigilance (maladaptive)",
        "journaling (adaptive)"
    ],
    "worldview_shifts": {{
        "trust": -0.4,
        "safety": -0.3,
        "self_worth": -0.2,
        "control": -0.3
    }},
    "cross_experience_triggers": [
        "Reactivates Experience #1 abandonment wound"
    ],
    "recommended_therapies": ["CBT", "play_therapy", "family_therapy"],
    "reasoning": "Divorce at age {age_at_event} during {dev_context['stage']['name']} disrupts attachment security and identity formation. The {dev_context['impact_multiplier']}x multiplier reflects heightened vulnerability during this developmental period. Child likely internalizes blame and develops hypervigilance to relationship stability."
}}
"""
    
    return prompt


async def analyze_experience(
    persona_id: str,
    experience_description: str,
    age_at_event: int,
    db: Session,
    previous_experiences: List = None
) -> Dict:
    """
    Analyze how a life experience affects the persona.

    Args:
        persona_id: Persona ID (string, not ORM object)
        experience_description: User's description of the experience
        age_at_event: Age when experience occurred
        db: Database session
        previous_experiences: List of previous Experience objects

    Returns:
        Dict with analysis results (immediate_effects, long_term_patterns, etc.)
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"DEBUG: analyze_experience called with persona_id type: {type(persona_id)}, value: {persona_id}")

    # Normalize accidental ORM input to avoid SQLAlchemy comparison errors.
    if isinstance(persona_id, Persona):
        logger.warning("analyze_experience received Persona ORM object; normalizing to persona_id.")
        persona_id = str(persona_id.id)
    
    if previous_experiences is None:
        previous_experiences = []
    
    # Fetch persona if needed for analysis
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise ValueError(f"Persona {persona_id} not found")
    
    # Extract persona data as dict (avoid passing ORM object)
    persona_data = {
        "name": persona.name,
        "baseline_age": persona.baseline_age,
        "baseline_gender": persona.baseline_gender,
        "baseline_background": persona.baseline_background,
        "current_personality": persona.current_personality,
        "current_attachment_style": persona.current_attachment_style,
        "current_trauma_markers": persona.current_trauma_markers,
    }
    
    # Generate prompt
    prompt = generate_experience_prompt(
        persona_data=persona_data,
        experience_description=experience_description,
        age_at_event=age_at_event,
        previous_experiences=previous_experiences
    )
    
    # Call OpenAI
    response = await openai_service.analyze(
        prompt=prompt,
        system_message="You are a clinical psychologist specializing in developmental trauma and personality psychology. Respond ONLY with valid JSON.",
        temperature=0.7,
        max_tokens=2000
    )
    
    # Parse response
    return response


def apply_personality_changes(
    current_personality: Dict[str, float],
    changes: Dict[str, float]
) -> Dict[str, float]:
    """
    Apply personality changes to current personality.
    
    Args:
        current_personality: Current Big Five dict
        changes: New values for traits
        
    Returns:
        Updated personality dict
    """
    updated = current_personality.copy()
    
    for trait, new_value in changes.items():
        if trait in updated:
            # Clamp to 0.0-1.0 range
            updated[trait] = max(0.0, min(1.0, new_value))
    
    return updated


def calculate_symptom_severity(
    symptom: str,
    age_at_event: int,
    event_severity: float,
    impact_multiplier: float = None
) -> int:
    """
    Calculate symptom severity (0-10) based on age and event severity.
    
    Args:
        symptom: Symptom name
        age_at_event: Age when event occurred
        event_severity: Base severity (0-10)
        impact_multiplier: Override impact multiplier (or auto-calculate from age)
        
    Returns:
        Severity score (0-10)
    """
    if impact_multiplier is None:
        impact_multiplier = calculate_trauma_impact_multiplier(age_at_event, "trauma")
    
    # Apply multiplier
    severity = event_severity * impact_multiplier
    
    # Clamp to 0-10
    return int(max(0, min(10, severity)))


def extract_event_metadata(description: str) -> Dict:
    """
    Extract basic metadata from event description.
    
    Args:
        description: Event description text
        
    Returns:
        Dict with event_type, estimated_severity
    """
    # Simple keyword-based classification
    # In production, could use AI for this too
    
    description_lower = description.lower()
    
    # Classify event type
    if any(word in description_lower for word in ["divorce", "separated", "left", "abandoned"]):
        event_type = "loss"
    elif any(word in description_lower for word in ["abuse", "trauma", "hurt", "violence"]):
        event_type = "trauma"
    elif any(word in description_lower for word in ["achievement", "success", "won", "graduated"]):
        event_type = "positive"
    elif any(word in description_lower for word in ["moved", "changed", "new"]):
        event_type = "transition"
    else:
        event_type = "relationship"
    
    return {
        "event_type": event_type,
        "requires_ai_analysis": True
    }


def validate_analysis_response(response: Dict) -> bool:
    """
    Validate that AI response has all required fields.
    
    Args:
        response: AI response dict
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_fields = [
        "immediate_effects",
        "long_term_patterns",
        "symptoms_developed",
        "symptom_severity",
        "coping_mechanisms",
        "worldview_shifts",
        "recommended_therapies",
        "reasoning"
    ]
    
    for field in required_fields:
        if field not in response:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate immediate_effects has Big Five traits
    if "immediate_effects" in response:
        required_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        for trait in required_traits:
            if trait not in response["immediate_effects"]:
                raise ValueError(f"Missing Big Five trait in immediate_effects: {trait}")
    
    return True


async def batch_analyze_experiences(
    persona_id: str,
    experiences: List[tuple],
    db: Session
) -> List[Dict]:
    """
    Analyze multiple experiences in sequence.
    
    Args:
        persona_id: Persona ID (string, not ORM object)
        experiences: List of (description, age) tuples
        db: Database session
        
    Returns:
        List of analysis results
    """
    # Defensive assertion: ensure persona_id is not an ORM object
    assert not isinstance(persona_id, Persona), "batch_analyze_experiences received Persona ORM object instead of persona_id"
    
    results = []
    previous_experiences = []
    
    for i, (description, age) in enumerate(experiences):
        result = await analyze_experience(
            persona_id=persona_id,
            experience_description=description,
            age_at_event=age,
            db=db,
            previous_experiences=previous_experiences
        )
        
        results.append(result)
        
        # Create mock experience object for context
        # In real usage, this would be actual database objects
        from types import SimpleNamespace
        mock_exp = SimpleNamespace(
            sequence_number=i+1,
            age_at_event=age,
            user_description=description,
            symptoms_developed=result.get("symptoms_developed", []),
            symptom_severity=result.get("symptom_severity", {})
        )
        previous_experiences.append(mock_exp)
    
    return results
