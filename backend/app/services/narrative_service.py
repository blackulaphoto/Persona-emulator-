"""
Narrative Service

Generates comprehensive AI-powered narratives about personas using GPT-4.
"""
import time
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import openai
import httpx
import os
from app.core.config import settings

from app.models.persona import Persona
from app.models.experience import Experience
from app.models.intervention import Intervention
from app.models.persona_narrative import PersonaNarrative
from app.models.adaptation_pattern import AdaptationPattern
from app.models.clinical_pattern_hypothesis import ClinicalPatternHypothesis
from app.models.narration import PersonaBelief
from app.services.evidence_accumulator import evidence_strength_label


async def generate_persona_narrative(
    db: Session,
    persona_id: str,
    user_id: str
) -> PersonaNarrative:
    """
    Generate a comprehensive narrative about a persona's psychological journey.

    Analyzes:
    - Complete timeline of experiences
    - All interventions and treatments
    - Personality evolution
    - Current psychological state

    Returns:
    - PersonaNarrative object with structured sections
    """
    start_time = time.time()

    # Fetch persona with all related data and verify ownership
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()
    if not persona:
        raise ValueError(f"Persona {persona_id} not found")
    
    # Fetch experiences (ordered chronologically)
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.age_at_event).all()
    
    # Fetch interventions (ordered chronologically)
    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.age_at_intervention).all()

    # Step 8 (docs/MIGRATION_MAP.md): the persona's established developmental
    # patterns, clinical pattern hypotheses, and self-stated beliefs - the
    # "three realities" model (event reality / persona's belief / engine
    # formulation). These tables are populated by steps 2-5's engines, which
    # are not yet wired into any creation route, so these queries return
    # empty lists in the live app today - the prompt is written to degrade
    # gracefully when that's the case, not to apologize for it.
    adaptation_patterns = db.query(AdaptationPattern).filter(
        AdaptationPattern.persona_id == persona_id
    ).order_by(AdaptationPattern.first_emerged_age).all()

    clinical_pattern_hypotheses = db.query(ClinicalPatternHypothesis).filter(
        ClinicalPatternHypothesis.persona_id == persona_id
    ).all()

    persona_beliefs = db.query(PersonaBelief).filter(
        PersonaBelief.subject_id == persona_id
    ).all()

    # Count existing narratives for generation number
    existing_count = db.query(PersonaNarrative).filter(
        PersonaNarrative.persona_id == persona_id
    ).count()
    generation_number = existing_count + 1

    # Build comprehensive prompt for GPT-4
    prompt = _build_narrative_prompt(
        persona, experiences, interventions,
        adaptation_patterns, clinical_pattern_hypotheses, persona_beliefs,
    )
    
    # Call GPT-4
    try:
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")

        # Explicitly provide an httpx client to avoid compatibility issues with old openai library version
        http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=5.0,
                read=600.0,
                write=600.0,
                pool=600.0,
            ),
        )

        client = openai.OpenAI(api_key=api_key, http_client=http_client)
        response = client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4o for best results
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical psychologist writing comprehensive case narratives. Generate detailed, empathetic, professional narratives about psychological development."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Balanced creativity and consistency
            max_tokens=4000   # Allow for comprehensive narrative
        )
        
        narrative_text = response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Failed to generate narrative with GPT-4: {str(e)}")
    
    # Parse the structured narrative
    sections = _parse_narrative_sections(narrative_text)
    
    # Calculate metadata
    word_count = len(narrative_text.split())
    generation_time = int(time.time() - start_time)
    
    # Create narrative record
    narrative = PersonaNarrative(
        user_id=user_id,
        persona_id=persona_id,
        generated_at=datetime.utcnow(),
        generation_number=generation_number,
        persona_age_at_generation=persona.current_age,
        total_experiences_count=len(experiences),
        total_interventions_count=len(interventions),
        executive_summary=sections.get("executive_summary", ""),
        developmental_timeline=sections.get("developmental_timeline", ""),
        current_presentation=sections.get("current_presentation", ""),
        treatment_response=sections.get("treatment_response", ""),
        prognosis=sections.get("prognosis", ""),
        full_narrative=narrative_text,
        word_count=word_count,
        generation_time_seconds=generation_time
    )
    
    db.add(narrative)
    db.commit()
    db.refresh(narrative)
    
    return narrative


def _build_narrative_prompt(
    persona: Persona,
    experiences: List[Experience],
    interventions: List[Intervention],
    adaptation_patterns: List[AdaptationPattern] = None,
    clinical_pattern_hypotheses: List[ClinicalPatternHypothesis] = None,
    persona_beliefs: List[PersonaBelief] = None,
) -> str:
    """
    Build comprehensive prompt for GPT-4 narrative generation.
    """
    adaptation_patterns = adaptation_patterns or []
    clinical_pattern_hypotheses = clinical_pattern_hypotheses or []
    persona_beliefs = persona_beliefs or []

    # Format experiences timeline
    experiences_text = "\n".join([
        f"- Age {exp.age_at_event}: {exp.event_type or 'Experience'} (severity: {exp.severity or 'unknown'}) - {exp.user_description}"
        for exp in experiences
    ]) if experiences else "No experiences yet"

    # Format interventions
    interventions_text = "\n".join([
        f"- Age {intv.age_at_intervention}: {intv.therapy_type} ({intv.duration}, {intv.intensity})"
        for intv in interventions
    ]) if interventions else "No therapeutic interventions yet"

    # Format personality traits
    personality_text = "\n".join([
        f"- {trait.capitalize()}: {value:.2f}"
        for trait, value in persona.current_personality.items()
    ])

    # Format current trauma markers (symptoms)
    trauma_text = ", ".join(persona.current_trauma_markers) if persona.current_trauma_markers else "None identified"

    # Step 11f: the State tier (app/services/state_trait_engine.py) - fast-
    # moving, reactive psychological state, the first rung of the arc below.
    # Only ever contains keys that have actually been touched by a real
    # proposal (current_state starts at {}) - never padded with an unearned
    # 0.5 for every STATE_VARIABLE.
    if persona.current_state:
        state_text = "\n".join(f"- {variable.replace('_', ' ').title()}: {value:.2f}" for variable, value in persona.current_state.items())
    else:
        state_text = "No State-tier movement recorded yet."

    # Step 8: the engine's own accumulated formulation - a real conclusion
    # (THE PATTERN), with evidence strength as secondary framing, not the
    # leading voice (see docs/MIGRATION_MAP.md / product spec section 8).
    # Step 11f: split into emerging vs. established so the narrative can
    # follow the actual arc (see ARC_GUIDANCE below) instead of treating
    # every AdaptationPattern row the same regardless of how earned it is.
    emerging_patterns = [p for p in adaptation_patterns if p.status == "emerging"]
    established_patterns = [p for p in adaptation_patterns if p.status == "established"]
    historical_patterns = [p for p in adaptation_patterns if p.status in ("weakening", "resolved")]

    def _format_pattern(p) -> str:
        history = ", ".join(
            f"age {entry.get('age', '?')}: {entry.get('effect', 'noted')}"
            for entry in (p.reinforcement_history or [])
        ) or "no recorded trajectory entries"
        return (
            f"- \"{p.pattern_name}\" (adaptive strategy: {p.adaptation_strategy}, status: {p.status}, "
            f"CURRENT evidence strength: {evidence_strength_label(p.evidence_strength)}; trajectory: {history})"
            + (f" - {p.description}" if p.description else "")
        )

    established_patterns_text = (
        "\n".join(_format_pattern(p) for p in established_patterns)
        if established_patterns else "None yet - no adaptation strategy has reached the established evidence bar."
    )
    emerging_patterns_text = (
        "\n".join(_format_pattern(p) for p in emerging_patterns)
        if emerging_patterns else "None currently emerging."
    )
    historical_patterns_text = (
        "\n".join(_format_pattern(p) for p in historical_patterns)
        if historical_patterns else "None weakened or resolved."
    )

    if clinical_pattern_hypotheses:
        hypotheses_text = "\n".join(
            f"- {h.pattern_key} (tier: {h.tier}, evidence strength: {evidence_strength_label(h.evidence_strength)})"
            for h in clinical_pattern_hypotheses
        )
    else:
        hypotheses_text = "No clinical pattern hypothesis has accumulated enough evidence yet."

    # Step 8: the "three realities" - event reality (experiences_text above),
    # the persona's own belief about their history, and what the engine's
    # own pattern analysis suggests. The gap between them, when one exists,
    # is real material - the narrative should name it, not silently pick one.
    if persona_beliefs:
        beliefs_text = "\n".join(
            f"- {persona.name} believes: \"{b.belief_text}\""
            + (f" [timeline evaluation: {b.timeline_evaluation}]" if b.timeline_evaluation else "")
            + (f" | Engine formulation: {b.engine_interpretation}" if b.engine_interpretation else "")
            for b in persona_beliefs
        )
    else:
        beliefs_text = f"{persona.name} has not stated an explicit belief about the origin of their difficulties yet."

    prompt = f"""You are a clinical psychologist writing a comprehensive developmental narrative.

**CRITICAL: PATIENT BACKGROUND - USE THIS INFORMATION**
{persona.baseline_background if persona.baseline_background else "No specific background provided."}

**PERSONA OVERVIEW**
Name: {persona.name}
Age: {persona.current_age}
Gender: {persona.baseline_gender or 'Not specified'}
Baseline Age: {persona.baseline_age}
Attachment Style: {persona.current_attachment_style}

**PERSONALITY TRAITS (Big Five, 0.0-1.0 scale)**
{personality_text}

**DOCUMENTED EXPERIENCES (Chronological)**
{experiences_text}

**THERAPEUTIC INTERVENTIONS**
{interventions_text}

**CURRENT PSYCHOLOGICAL STATE**
Trauma Markers/Symptoms: {trauma_text}

**STATE TIER (fast-moving, reactive - see the arc below)**
{state_text}

**EMERGING DEVELOPMENTAL PATTERNS (reinforced more than once, not yet established)**
{emerging_patterns_text}

**ENGINE'S OWN FORMULATION - ESTABLISHED DEVELOPMENTAL PATTERNS**
(CURRENTLY active and durable. Built from the full timeline, not any single event.)
{established_patterns_text}

**HISTORICALLY IMPORTANT PATTERNS - NOW WEAKENING OR RESOLVED**
(These may explain the lifespan trajectory, but they are NOT current dominant patterns. Describe how they developed, were reinforced, and later weakened or resolved.)
{historical_patterns_text}

**ENGINE'S OWN FORMULATION - CLINICAL PATTERN HYPOTHESES**
(Tiered, evidence-tracked - never a diagnosis, regardless of tier)
{hypotheses_text}

**{persona.name.upper()}'S OWN STATED BELIEFS ABOUT THEIR HISTORY**
(This is {persona.name}'s self-report, not necessarily what the timeline supports - see instruction 4 below)
{beliefs_text}

**HOW TO READ THE STATE -> PATTERN -> TRAIT ARC (see instruction 3a below)**
This engine models psychological change as four stages, each requiring more evidence than the last:
1. STATE (above) - an immediate, reactive shift after a single event. Can move quickly and can also move back.
2. EMERGING PATTERN (above) - the same adaptation strategy showing up more than once, but not yet reinforced enough to call durable.
3. ESTABLISHED PATTERN (above) - reinforced enough across the timeline to be a real, durable developmental formulation.
4. TRAIT SHIFT (see PERSONALITY TRAITS above) - {persona.name}'s Big Five only ever moves in small steps, and only once a pattern has reached ESTABLISHED. A Big Five value that differs from a neutral baseline is NOT automatic evidence of this - it may simply reflect {persona.name}'s starting temperament. Only describe a trait as having SHIFTED from the developmental history if an established pattern above plausibly explains the direction of that shift.

---

**INSTRUCTIONS:**
Write a psychologically accurate developmental narrative that:

1. **EXPLICITLY incorporates the background information provided above**
   - If the background mentions substance-using parents → Discuss impact on attachment, stability, safety, neglect
   - If the background mentions abuse/trauma → Discuss trauma responses, developmental disruption, betrayal
   - If the background mentions neglect → Discuss attachment insecurity, unmet needs, emotional dysregulation
   - If the background mentions molestation/sexual abuse → Discuss trauma, boundary violations, shame, lack of protection
   - DO NOT invent a "secure attachment" or "nurturing environment" unless the background supports it
   - DO NOT minimize or ignore severe adversity mentioned in the background

2. **Uses evidence-based developmental psychology**:
   - Attachment theory (secure, anxious, avoidant, disorganized based on actual caregiving)
   - Trauma-informed perspective (ACEs, complex trauma, developmental trauma)
   - Age-appropriate developmental tasks and how adversity disrupted them
   - Realistic coping mechanisms developed in response to actual environment

3. **States the engine's own formulation as a real conclusion, not a hedge**:
   - If a CURRENTLY ESTABLISHED developmental pattern exists above, name it explicitly (e.g. "The dominant pattern here is...") - this is THE VERDICT, and it should be stated with the same directness a thoughtful clinician would use, not wrapped in "it's possible that" for every sentence
   - NEVER call a weakening or resolved historical pattern dominant, active, or current. Discuss its historical importance and trajectory explicitly: developed, reinforced, weakened, resolved, or remains active.
   - Evidence strength (high/moderate/low/no evidence yet) is SECONDARY framing - mention it after the conclusion, to support it, never as a replacement for making one. "There isn't enough information" is not an acceptable substitute for engaging with what the timeline actually shows
   - If no pattern has accumulated enough reinforcement yet, say so plainly and reason from the objective experience timeline instead - that is a legitimate, honest state, not a gap to apologize for

3a. **Narrates through the STATE -> PATTERN -> TRAIT arc explicitly, using the actual data above - do not collapse the stages together**:
   - Describe what is still just a current STATE reaction (recent, could shift with different circumstances) separately from what has become an EMERGING pattern (repeating, but not yet durable) separately from what is genuinely ESTABLISHED (durable, evidence-backed), and separately from what is historically important but now WEAKENING or RESOLVED
   - Only attribute a TRAIT SHIFT to {persona.name}'s developmental history when an established pattern above plausibly explains its direction - otherwise, personality differences from a neutral baseline are just {persona.name}'s starting temperament, not something the timeline caused, and should be described that way
   - This is not optional narrative color: conflating a passing State reaction with a permanent personality change is exactly the kind of overclaiming a careful clinician avoids

4. **Names the gap when {persona.name}'s stated belief and the engine's formulation diverge**:
   - If {persona.name} has stated a belief about their own history (see above) that the timeline only partially supports, say so directly - e.g. "{persona.name} sees [X] as the origin of their difficulties; the timeline suggests [earlier pattern] was already present, and [X] more plausibly reinforced it than originated it."
   - This divergence, when it exists, is some of the most clinically interesting material available - do not silently pick one account over the other or smooth the discrepancy over
   - If {persona.name} has not stated a belief, do not invent one

5. **Organizes narrative into these sections** (use markdown headers):

## EXECUTIVE SUMMARY
(2-3 paragraphs: Who is this person? Lead with THE VERDICT only if a currently established pattern exists - name it directly, e.g. "The dominant pattern here is..." - then the reasoning. If only historical weakening/resolved patterns exist, describe their earlier importance and present trajectory instead of calling them currently dominant. Core psychological profile rooted in their ACTUAL background, key developmental themes, current functioning level. If {persona.name} has stated a belief that diverges from the engine's formulation, name that gap here too.)

## DEVELOPMENTAL TIMELINE
(Chronological narrative organized by developmental periods. For each period, describe how the BACKGROUND and experiences shaped development, and connect specific periods to WHAT IT CONNECTS TO later - which later events reinforced or weakened the pattern identified above:
- **Early Childhood (0-6)**: How did the caregiving environment affect attachment? What were the actual conditions?
- **Middle Childhood (7-11)**: How did early experiences manifest in school/peer relationships?
- **Adolescence (12-18)**: How did accumulated adversity affect identity formation?
- **Adulthood (19+)**: Current patterns stemming from developmental history)

## CURRENT PRESENTATION
(How they navigate the world NOW: Daily behaviors, relationship patterns, coping mechanisms, emotional regulation - all connected to their actual background and experiences. State evidence strength for the named pattern here, as secondary framing after the substantive description, not before it.)

## TREATMENT RESPONSE
(If interventions exist: How did therapy help? What changed? What symptoms improved? What remains challenging? Be realistic about limitations.)

## PROGNOSIS & RECOMMENDATIONS
(Future outlook based on actual history: What's realistic? What additional support needed? Acknowledge both challenges and strengths)

**CRITICAL REQUIREMENTS:**
- Base ALL analysis on the actual background provided - DO NOT make up a happy childhood
- If parents were addicted/neglectful → Describe insecure/disorganized attachment
- If abuse occurred → Describe trauma impact, not "resilience overcame everything"
- If environment was chaotic → Describe hypervigilance, not "adapted well"
- Be empathetic but clinically accurate about the REAL impact of adversity
- Acknowledge protective factors where they exist, but don't minimize trauma
- Use professional yet accessible language suitable for educational/clinical contexts
- Total length: 1200-1800 words
- Connect every assertion to actual background/experiences provided
- Never write "there isn't enough information to say" as a substitute for reasoning from what's actually there - if the pattern data above is genuinely empty, reason confidently from the objective experience timeline instead

Begin the narrative:"""

    return prompt


def _parse_narrative_sections(narrative_text: str) -> Dict[str, str]:
    """
    Parse GPT-4 response into structured sections.
    
    Looks for markdown headers to split sections.
    """
    sections = {
        "executive_summary": "",
        "developmental_timeline": "",
        "current_presentation": "",
        "treatment_response": "",
        "prognosis": ""
    }
    
    # Simple parser - split by headers
    lines = narrative_text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        # Check if line is a header
        if line.startswith('## '):
            # Save previous section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Determine new section
            header = line.replace('##', '').strip().lower()
            if 'executive' in header or 'summary' in header:
                current_section = 'executive_summary'
            elif 'developmental' in header or 'timeline' in header:
                current_section = 'developmental_timeline'
            elif 'current' in header or 'presentation' in header:
                current_section = 'current_presentation'
            elif 'treatment' in header or 'response' in header:
                current_section = 'treatment_response'
            elif 'prognosis' in header or 'recommendation' in header:
                current_section = 'prognosis'
            else:
                current_section = None
            
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Save final section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections


async def get_persona_narratives(
    db: Session,
    persona_id: str,
    user_id: str,
    limit: int = 10
) -> List[PersonaNarrative]:
    """
    Get all narratives for a persona, ordered by most recent first.
    """
    narratives = db.query(PersonaNarrative).filter(
        PersonaNarrative.persona_id == persona_id,
        PersonaNarrative.user_id == user_id
    ).order_by(PersonaNarrative.generated_at.desc()).limit(limit).all()

    return narratives


async def get_narrative_by_id(
    db: Session,
    narrative_id: str,
    user_id: str
) -> PersonaNarrative:
    """
    Get a specific narrative by ID.
    """
    narrative = db.query(PersonaNarrative).filter(
        PersonaNarrative.id == narrative_id,
        PersonaNarrative.user_id == user_id
    ).first()

    if not narrative:
        raise ValueError(f"Narrative {narrative_id} not found")

    return narrative


async def delete_narrative(
    db: Session,
    narrative_id: str,
    user_id: str
) -> bool:
    """
    Delete a narrative.
    """
    narrative = db.query(PersonaNarrative).filter(
        PersonaNarrative.id == narrative_id,
        PersonaNarrative.user_id == user_id
    ).first()

    if not narrative:
        return False

    db.delete(narrative)
    db.commit()
    return True
