"""
Intervention Engine - AI-powered therapy efficacy analysis.

Uses OpenAI GPT-4 + therapy database + developmental stages to analyze
how therapeutic interventions affect symptoms and personality.
"""
import json
import os
from typing import Dict, List, Optional
from app.services.openai_service import OpenAIService
from app.utils.therapy_database import (
    get_therapy_info,
    calculate_therapy_match_score
)
from app.utils.developmental_stages import (
    get_recommended_interventions_by_age,
    get_age_appropriate_coping_capacity
)


# Initialize OpenAI service
openai_service = OpenAIService(
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY"),
    model="gpt-4"
)


def generate_intervention_prompt(
    persona,
    therapy_type: str,
    duration: int,
    intensity: str,
    age_at_intervention: int
) -> str:
    """
    Generate AI prompt for intervention analysis.
    
    Args:
        persona: Persona object with current symptoms
        therapy_type: Type of therapy (CBT, ACT, EMDR, etc.)
        duration: Duration in weeks
        intensity: "weekly", "twice_weekly", "monthly"
        age_at_intervention: Age when intervention begins
        
    Returns:
        Formatted prompt string for GPT-4
    """
    # Get therapy metadata from database
    therapy_info = get_therapy_info(therapy_type)
    if not therapy_info:
        raise ValueError(f"Unknown therapy type: {therapy_type}")
    
    # Get current symptoms from trauma markers
    current_symptoms = persona.current_trauma_markers if persona.current_trauma_markers else []
    
    # Calculate baseline efficacy match
    baseline_efficacy = calculate_therapy_match_score(therapy_type, current_symptoms)
    
    # Get age-appropriate context
    recommended_therapies = get_recommended_interventions_by_age(age_at_intervention)
    coping_capacity = get_age_appropriate_coping_capacity(age_at_intervention)
    
    # Build comprehensive prompt
    prompt = f"""You are a clinical psychologist analyzing therapeutic intervention outcomes.

PERSON CONTEXT:
Name: {persona.name}
Current Age: {age_at_intervention}
Baseline Background: {persona.baseline_background}

CURRENT PERSONALITY (Big Five, 0.0-1.0 scale):
- Openness: {persona.current_personality.get('openness', 0.5)}
- Conscientiousness: {persona.current_personality.get('conscientiousness', 0.5)}
- Extraversion: {persona.current_personality.get('extraversion', 0.5)}
- Agreeableness: {persona.current_personality.get('agreeableness', 0.5)}
- Neuroticism: {persona.current_personality.get('neuroticism', 0.5)}

CURRENT ATTACHMENT STYLE: {persona.current_attachment_style}

CURRENT SYMPTOMS & TRAUMA MARKERS:
{', '.join(current_symptoms) if current_symptoms else 'None reported'}

INTERVENTION DETAILS:
Therapy Type: {therapy_info['name']}
Duration: {duration} weeks
Intensity: {intensity}
Age at Start: {age_at_intervention}

THERAPY PROFILE:
Mechanism: {therapy_info['mechanism']}
Best For: {', '.join(therapy_info['best_for'])}
Limitations: {', '.join(therapy_info['limitations'])}
Evidence Base: {therapy_info['evidence_base']}
Typical Duration: {therapy_info['typical_duration']}

BASELINE EFFICACY MATCH: {baseline_efficacy:.2f} (0.0-1.0 scale)
- This indicates how well the therapy targets the current symptoms
- 0.8+ = Excellent match
- 0.5-0.8 = Moderate match
- <0.5 = Poor match (therapy not designed for these symptoms)

AGE-APPROPRIATE CONTEXT (Age {age_at_intervention}):
Recommended Therapies for This Age: {', '.join(recommended_therapies)}
Coping Capacity:
- Cognitive Processing: {coping_capacity['cognitive_processing']*100:.0f}%
- Emotional Regulation: {coping_capacity['emotional_regulation']*100:.0f}%
- Verbal Articulation: {coping_capacity['verbal_articulation']*100:.0f}%
- Agency/Autonomy: {coping_capacity['agency']*100:.0f}%

ANALYSIS INSTRUCTIONS:
1. **Efficacy Match** (0.0-1.0): How well does this therapy target these specific symptoms?
   - Consider baseline match score above
   - Adjust based on duration (too short = reduced efficacy)
   - Consider age-appropriateness

2. **Symptom Changes** (Before/After):
   - Rate each symptom 0-10 before and after
   - Calculate percentage improvement
   - Be REALISTIC: therapy helps but rarely "cures"
   - Wrong therapy = minimal improvement (10-20%)
   - Right therapy = significant improvement (40-60%)
   - Deep trauma requires long-term work

3. **Personality Changes** (Big Five):
   - Therapy can reduce neuroticism (anxiety)
   - May increase conscientiousness (structure/coping)
   - Modest changes only (0.1-0.2 shift maximum)

4. **Coping Skills Gained**:
   - What specific skills does this therapy teach?
   - Are they adaptive (healthy) or still limited?

5. **Sustained Effects**:
   - What changes persist after therapy ends?
   - What requires ongoing practice/maintenance?
   - Be honest about relapse risk

6. **Limitations** (CRITICAL):
   - What does this therapy NOT address?
   - What symptoms persist despite treatment?
   - Why isn't this a complete cure?
   - Example: "ACT reduces hoarding behavior but doesn't address underlying attachment trauma"

7. **Evidence-Based Reasoning**:
   - Use attachment theory, trauma research, therapy outcome studies
   - Reference the therapy's mechanism and limitations
   - Explain why efficacy is high/low for these specific symptoms

CRITICAL REALISM REQUIREMENTS:
- Behavioral change ≠ trauma resolution
- Symptoms improve but rarely disappear completely
- Wrong therapy can still help a little (supportive relationship, general coping)
- Root causes may persist even with symptom reduction
- Deep attachment wounds require years of therapy, not weeks
- Therapy is not magic - it's hard work with modest gains

OUTPUT FORMAT (valid JSON only):
{{
    "efficacy_match": 0.85,
    "symptom_changes": {{
        "before": {{"hoarding": 8, "anxiety": 6, "avoidance": 7}},
        "after": {{"hoarding": 4, "anxiety": 5, "avoidance": 4}},
        "percentage_improvement": {{"hoarding": 50, "anxiety": 17, "avoidance": 43}}
    }},
    "personality_changes": {{
        "neuroticism": 0.6,
        "conscientiousness": 0.5
    }},
    "coping_skills_gained": [
        "mindful acceptance of discomfort",
        "values-based decision making",
        "defusion from attachment to objects"
    ],
    "sustained_effects": [
        "Hoarding behavior reduced with ongoing practice",
        "Anxiety reduction partial - root trauma unaddressed",
        "Behavioral gains maintainable with continued mindfulness"
    ],
    "limitations": [
        "Does not address underlying attachment trauma",
        "Anxiety about relationships persists (insecure attachment unchanged)",
        "Requires ongoing practice to maintain gains",
        "Deep wounds require longer-term psychodynamic/IFS therapy"
    ],
    "reasoning": "ACT is evidence-based for hoarding (efficacy match: {baseline_efficacy:.2f}) through increasing psychological flexibility and values-based action. The {duration}-week duration is {get_duration_assessment(duration, therapy_info)}. However, ACT addresses behavioral symptoms without processing underlying trauma. The person's insecure attachment and core wounds persist despite behavioral improvement. This is a realistic outcome: hoarding improves significantly but attachment anxiety remains, requiring additional therapy modalities for complete healing."
}}
"""
    
    return prompt


def get_duration_assessment(duration: int, therapy_info: Dict) -> str:
    """Get assessment of whether duration is appropriate."""
    typical = therapy_info['typical_duration']
    
    # Parse typical duration (e.g., "12-20 weeks")
    if '-' in typical:
        min_weeks = int(typical.split('-')[0].split()[0])
        if duration < min_weeks:
            return "shorter than recommended (may reduce efficacy)"
        elif duration >= min_weeks:
            return "appropriate"
    
    return "appropriate"


async def analyze_intervention(
    persona,
    therapy_type: str,
    duration: int,
    intensity: str,
    age_at_intervention: int
) -> Dict:
    """
    Analyze how a therapeutic intervention affects the persona.
    
    Args:
        persona: Persona object
        therapy_type: Type of therapy (CBT, ACT, EMDR, etc.)
        duration: Duration in weeks
        intensity: "weekly", "twice_weekly", "monthly"
        age_at_intervention: Age when intervention begins
        
    Returns:
        Dict with analysis results (efficacy_match, symptom_changes, etc.)
    """
    # Generate prompt
    prompt = generate_intervention_prompt(
        persona=persona,
        therapy_type=therapy_type,
        duration=duration,
        intensity=intensity,
        age_at_intervention=age_at_intervention
    )
    
    # Call OpenAI
    response = await openai_service.analyze(
        prompt=prompt,
        system_message="You are a clinical psychologist specializing in therapy outcome research and evidence-based practice. Respond ONLY with valid JSON. Be realistic about therapy limitations.",
        temperature=0.7,
        max_tokens=2000
    )
    
    # Parse response
    return response


def calculate_baseline_efficacy_match(therapy_type: str, symptoms: List[str]) -> float:
    """
    Calculate baseline efficacy match using therapy database.
    
    Args:
        therapy_type: Type of therapy
        symptoms: List of current symptoms
        
    Returns:
        Efficacy score (0.0-1.0)
    """
    return calculate_therapy_match_score(therapy_type, symptoms)


def apply_symptom_changes(
    current_severity: Dict[str, int],
    changes: Dict
) -> Dict[str, int]:
    """
    Apply symptom changes to current severity.
    
    Args:
        current_severity: Current symptom severity dict
        changes: Changes dict with "after" key
        
    Returns:
        Updated severity dict
    """
    updated = current_severity.copy()
    
    if "after" in changes:
        for symptom, new_severity in changes["after"].items():
            updated[symptom] = max(0, min(10, new_severity))
    
    return updated


def calculate_duration_impact(duration: int, recommended_duration: int) -> float:
    """
    Calculate how therapy duration affects efficacy.
    
    Args:
        duration: Actual duration in weeks
        recommended_duration: Recommended duration in weeks
        
    Returns:
        Impact multiplier (0.5-1.2)
    """
    ratio = duration / recommended_duration
    
    if ratio < 0.5:
        # Too short - significantly reduced efficacy
        return 0.5
    elif ratio < 0.75:
        # Short - moderately reduced efficacy
        return 0.75
    elif ratio <= 1.5:
        # Appropriate duration
        return 1.0
    else:
        # Extended duration - slightly enhanced efficacy
        return min(1.2, 1.0 + (ratio - 1.5) * 0.1)


def validate_intervention_response(response: Dict) -> bool:
    """
    Validate that AI response has all required fields.
    
    Args:
        response: AI response dict
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_fields = [
        "efficacy_match",
        "symptom_changes",
        "personality_changes",
        "coping_skills_gained",
        "sustained_effects",
        "limitations",
        "reasoning"
    ]
    
    for field in required_fields:
        if field not in response:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate symptom_changes structure
    if "symptom_changes" in response:
        required_subfields = ["before", "after", "percentage_improvement"]
        for subfield in required_subfields:
            if subfield not in response["symptom_changes"]:
                raise ValueError(f"Missing symptom_changes subfield: {subfield}")
    
    return True


async def batch_analyze_interventions(
    persona,
    interventions: List[tuple]
) -> List[Dict]:
    """
    Analyze multiple interventions in sequence.
    
    Args:
        persona: Persona object
        interventions: List of (therapy_type, duration, intensity, age) tuples
        
    Returns:
        List of analysis results
    """
    results = []
    
    for therapy_type, duration, intensity, age in interventions:
        result = await analyze_intervention(
            persona=persona,
            therapy_type=therapy_type,
            duration=duration,
            intensity=intensity,
            age_at_intervention=age
        )
        
        results.append(result)
        
        # Update persona symptoms for next intervention
        # (In real usage, this would update the database)
        if "symptom_changes" in result and "after" in result["symptom_changes"]:
            # Simulate symptom update (simplified)
            pass
    
    return results


def explain_why_therapy_works_or_not(
    therapy_type: str,
    symptoms: List[str],
    efficacy_match: float
) -> str:
    """
    Generate human-readable explanation of therapy efficacy.
    
    Args:
        therapy_type: Type of therapy
        symptoms: Current symptoms
        efficacy_match: Calculated efficacy match
        
    Returns:
        Explanation string
    """
    therapy_info = get_therapy_info(therapy_type)
    
    if efficacy_match >= 0.8:
        explanation = f"{therapy_info['name']} is an excellent match (efficacy: {efficacy_match:.0%}) because it's specifically designed to treat {', '.join(symptoms)}."
    elif efficacy_match >= 0.5:
        explanation = f"{therapy_info['name']} is a moderate match (efficacy: {efficacy_match:.0%}). It may help with some symptoms but isn't optimized for all of them."
    else:
        explanation = f"{therapy_info['name']} is a poor match (efficacy: {efficacy_match:.0%}). This therapy is designed for {', '.join(therapy_info['best_for'][:3])}, not {', '.join(symptoms)}."
    
    return explanation
