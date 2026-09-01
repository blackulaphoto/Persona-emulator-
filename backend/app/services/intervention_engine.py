"""
Intervention Engine - AI-powered therapy efficacy analysis.

Uses OpenAI GPT-4 + therapy database + developmental stages to analyze
how therapeutic interventions affect symptoms and personality.

Step 7 of docs/MIGRATION_MAP.md: this file used to contain a second set of
functions (match_disorders_to_therapies, calculate_comprehensive_therapy_
efficacy, get_disorder_specific_recommendations, batch_analyze_interventions,
calculate_duration_impact, apply_symptom_changes, explain_why_therapy_works_
or_not, calculate_baseline_efficacy_match) that duplicated app/utils/
symptom_assessment_engine.py's hardcoded disorder x therapy effectiveness
table instead of using this file's own real, evidence-flavored matching
(therapy_database.calculate_therapy_match_score). None of them were called
from anywhere outside this file - confirmed by repo-wide grep - so they were
removed rather than "consolidated," there was nothing live depending on them.
symptom_assessment_engine.calculate_intervention_effect itself is NOT
removed - app/api/routes/symptoms.py's POST /interventions/effectiveness
endpoint calls it directly and is live. It's still the same arbitrary
hardcoded table the original audit flagged, but retiring it means either
breaking that route or migrating it to the new system, which is a route-
level decision deserving its own explicit sign-off, not a side effect of
this cleanup - see its own updated docstring.
"""
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


# Initialize services
openai_service = OpenAIService(
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY"),
    model="gpt-4o"
)


# ============================================================
# Bridges ClinicalPatternHypothesis.pattern_key (app/utils/symptom_taxonomy.py
# keys, e.g. "borderline_personality") to therapy_database.py's best_for
# vocabulary (e.g. "bpd") - the two were never aligned. Confirmed by direct
# check: 9 of the 12 pattern_keys the evidence accumulator can actually
# produce (see evidence_accumulator.EXPOSURE_HYPOTHESIS_PRIORS) have ZERO
# direct match against best_for. Feeding pattern_keys into
# calculate_therapy_match_score unaliased would silently produce near-zero
# match scores for most patterns. Deliberately NOT exhaustive - a pattern
# with no good alias (e.g. adjustment_disorder, prolonged_grief_disorder)
# is left unmapped rather than forced into a clinically wrong bridge (e.g.
# obsessive_compulsive_personality is NOT the same disorder as OCD, so it is
# NOT aliased to ERP's "compulsive_behaviors" target even though the names
# look similar).
# ============================================================
PATTERN_KEY_THERAPY_ALIASES: Dict[str, List[str]] = {
    "reactive_attachment_disorder": ["attachment_wounds", "childhood_trauma"],
    "complex_ptsd": ["complex_trauma", "childhood_trauma", "attachment_wounds"],
    "generalized_anxiety": ["anxiety", "chronic_anxiety"],
    "borderline_personality": ["bpd", "relationship_instability", "emotion_dysregulation", "self_harm"],
    "illness_anxiety_disorder": ["health_anxiety"],
    "avoidant_personality": ["avoidance_behaviors", "attachment_wounds"],
}


def _aliased_pattern_symptoms(pattern_keys: List[str]) -> List[str]:
    """Expands pattern_keys through PATTERN_KEY_THERAPY_ALIASES for matching against therapy_database.py."""
    aliased = []
    for key in pattern_keys:
        aliased.append(key)  # keep the original too, in case it does match directly (e.g. "ptsd")
        aliased.extend(PATTERN_KEY_THERAPY_ALIASES.get(key, []))
    return aliased


def select_targeted_pattern(adaptation_patterns: Optional[List[Dict]]) -> Optional[Dict]:
    """
    Step 11e (docs/MIGRATION_MAP.md): deterministically picks the single
    AdaptationPattern (as a dict from pattern_engine.accumulate_patterns())
    this intervention's Trait-tier gating is evaluated against.

    Only "established" patterns are eligible - an "emerging" pattern is not
    a real enough target for a course of therapy to earn Trait credit
    against (same evidence bar state_trait_engine.trait_gate_open already
    requires elsewhere). Among established patterns, picks the one with the
    highest evidence_strength, on the simple assumption that a course of
    therapy is presumed directed at the persona's most significant
    established issue - deliberately not a therapy-type-aware match (that
    would require aliasing adaptation_strategy against therapy_database.py's
    best_for vocabulary, which does not exist for that vocabulary the way
    PATTERN_KEY_THERAPY_ALIASES does for pattern_key). Returns None if no
    established pattern exists yet.
    """
    established = [p for p in (adaptation_patterns or []) if p.get("status") == "established"]
    if not established:
        return None
    return max(established, key=lambda p: p.get("evidence_strength") or 0.0)


def generate_intervention_prompt(
    persona,
    therapy_type: str,
    duration: int,
    intensity: str,
    age_at_intervention: int,
    adaptation_patterns: Optional[List[Dict]] = None,
    clinical_pattern_hypotheses: Optional[List[Dict]] = None,
) -> str:
    """
    Generate AI prompt for intervention analysis.

    Args:
        persona: Persona object with current symptoms
        therapy_type: Type of therapy (CBT, ACT, EMDR, etc.)
        duration: Duration in weeks
        intensity: "weekly", "twice_weekly", "monthly"
        age_at_intervention: Age when intervention begins
        adaptation_patterns: optional [{pattern_name, adaptation_strategy, status,
            evidence_strength, current_manifestations}, ...] from
            pattern_engine.accumulate_patterns() (step 5). When provided,
            enriches matching and asks the model to state which patterns this
            therapy's mechanism plausibly touches vs. leaves unresolved.
        clinical_pattern_hypotheses: optional [{pattern_key, tier, evidence_strength,
            current_manifestations}, ...] from evidence_accumulator.accumulate_evidence()
            (step 4). Not yet passed by any live route - see docs/MIGRATION_MAP.md.

    Returns:
        Formatted prompt string for GPT-4
    """
    # Get therapy metadata from database
    therapy_info = get_therapy_info(therapy_type)
    if not therapy_info:
        raise ValueError(f"Unknown therapy type: {therapy_type}")

    adaptation_patterns = adaptation_patterns or []
    clinical_pattern_hypotheses = clinical_pattern_hypotheses or []

    # Legacy symptom source, unchanged - kept so existing callers (that don't
    # pass pattern data) behave exactly as before.
    current_symptoms = persona.current_trauma_markers if persona.current_trauma_markers else []

    # When pattern data IS provided, the match score is computed from the
    # richer evidence too, bridged through PATTERN_KEY_THERAPY_ALIASES -
    # otherwise a pattern_key like "borderline_personality" would silently
    # fail to match DBT's best_for=["bpd", ...] and understate the match.
    pattern_keys = [h["pattern_key"] for h in clinical_pattern_hypotheses if h.get("pattern_key")]
    strategy_keys = [p["adaptation_strategy"] for p in adaptation_patterns if p.get("adaptation_strategy")]
    matching_symptoms = list(current_symptoms) + _aliased_pattern_symptoms(pattern_keys) + strategy_keys

    # Calculate baseline efficacy match
    baseline_efficacy = calculate_therapy_match_score(therapy_type, matching_symptoms)

    # Get age-appropriate context
    recommended_therapies = get_recommended_interventions_by_age(age_at_intervention)
    coping_capacity = get_age_appropriate_coping_capacity(age_at_intervention)

    patterns_section = ""
    if adaptation_patterns:
        lines = "\n".join(
            f"- {p['pattern_name']} (strategy: {p['adaptation_strategy']}, status: {p['status']}, "
            f"evidence: {p.get('evidence_strength')})"
            for p in adaptation_patterns
        )
        patterns_section = f"""
ESTABLISHED DEVELOPMENTAL PATTERNS (from the persona's full timeline, not just current symptoms):
{lines}

For each pattern above, state in your reasoning whether this therapy's mechanism plausibly
touches it or leaves it unresolved - do not assume symptom improvement means the underlying
pattern changed. Example of the standard this should meet: "DBT substantially improves emotional
regulation and impulsive behavior, but the attachment expectation that closeness leads to
abandonment remains only partially changed."
"""

    hypotheses_section = ""
    if clinical_pattern_hypotheses:
        lines = "\n".join(
            f"- {h['pattern_key']} (tier: {h['tier']}, evidence: {h.get('evidence_strength')})"
            for h in clinical_pattern_hypotheses
        )
        hypotheses_section = f"""
CLINICAL PATTERN HYPOTHESES (tiered, not diagnoses - see docs/MIGRATION_MAP.md):
{lines}
"""

    # Build comprehensive prompt
    prompt = f"""You are a clinical psychologist analyzing therapeutic intervention outcomes.

PERSON CONTEXT:
Name: {persona.name}
Current Age: {age_at_intervention}
Baseline Background: {persona.baseline_background}

CURRENT PERSONALITY (Big Five, 0.0-1.0 scale - simulation estimates, not a validated assessment):
- Openness: {persona.current_personality.get('openness', 0.5)}
- Conscientiousness: {persona.current_personality.get('conscientiousness', 0.5)}
- Extraversion: {persona.current_personality.get('extraversion', 0.5)}
- Agreeableness: {persona.current_personality.get('agreeableness', 0.5)}
- Neuroticism: {persona.current_personality.get('neuroticism', 0.5)}

CURRENT ATTACHMENT STYLE: {persona.current_attachment_style}

CURRENT SYMPTOMS & TRAUMA MARKERS:
{', '.join(current_symptoms) if current_symptoms else 'None reported'}
{patterns_section}{hypotheses_section}
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
- This indicates how well the therapy targets the current symptoms{' and established patterns' if (adaptation_patterns or clinical_pattern_hypotheses) else ''}
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
    age_at_intervention: int,
    adaptation_patterns: Optional[List[Dict]] = None,
    clinical_pattern_hypotheses: Optional[List[Dict]] = None,
) -> Dict:
    """
    Analyze how a therapeutic intervention affects the persona.

    Args:
        persona: Persona object
        therapy_type: Type of therapy (CBT, ACT, EMDR, etc.)
        duration: Duration in weeks
        intensity: "weekly", "twice_weekly", "monthly"
        age_at_intervention: Age when intervention begins
        adaptation_patterns: optional pattern_engine.accumulate_patterns() output - see
            generate_intervention_prompt's docstring. Not yet passed by
            app/api/routes/interventions.py; wiring it in is a deliberate next
            step, not bundled into this one (see docs/MIGRATION_MAP.md).
        clinical_pattern_hypotheses: optional evidence_accumulator.accumulate_evidence()
            output - same caveat.

    Returns:
        Dict with analysis results (efficacy_match, symptom_changes, etc.)
    """
    # Generate prompt
    prompt = generate_intervention_prompt(
        persona=persona,
        therapy_type=therapy_type,
        duration=duration,
        intensity=intensity,
        age_at_intervention=age_at_intervention,
        adaptation_patterns=adaptation_patterns,
        clinical_pattern_hypotheses=clinical_pattern_hypotheses,
    )

    # Call OpenAI
    response = await openai_service.analyze(
        prompt=prompt,
        system_message="You are a clinical psychologist specializing in therapy outcome research and evidence-based practice. Respond ONLY with valid JSON. Be realistic about therapy limitations.",
        temperature=0.0,
        max_tokens=2000
    )

    # Parse response
    return response
