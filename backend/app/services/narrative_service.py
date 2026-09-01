"""
Narrative Service

Generates comprehensive AI-powered narratives about personas.
"""
import time
import logging
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
from app.models.interpretation import Interpretation
from app.models.protective_factor import ProtectiveFactor
from app.services.evidence_accumulator import evidence_strength_label


logger = logging.getLogger(__name__)

NARRATIVE_MODEL = "gpt-5.6-luna"
NARRATIVE_MAX_OUTPUT_TOKENS = 8000
NARRATIVE_REASONING_EFFORT = "low"
NARRATIVE_SYSTEM_INSTRUCTIONS = (
    "You are a clinical psychologist writing comprehensive case narratives. "
    "Generate detailed, empathetic, professional narratives about psychological development."
)


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
    ).order_by(Experience.age_at_event, Experience.sequence_index, Experience.sequence_number).all()
    
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

    interpretations = db.query(Interpretation).filter(
        Interpretation.persona_id == persona_id
    ).order_by(Interpretation.age_at_event, Interpretation.created_at).all()

    protective_factors = db.query(ProtectiveFactor).filter(
        ProtectiveFactor.persona_id == persona_id
    ).order_by(ProtectiveFactor.active_from_age, ProtectiveFactor.created_at).all()

    # Count existing narratives for generation number
    existing_count = db.query(PersonaNarrative).filter(
        PersonaNarrative.persona_id == persona_id
    ).count()
    generation_number = existing_count + 1

    # Build the existing comprehensive narrative prompt.
    prompt = _build_narrative_prompt(
        persona, experiences, interventions,
        adaptation_patterns, clinical_pattern_hypotheses, persona_beliefs,
        interpretations, protective_factors,
    )
    
    # Call the Responses API for GPT-5.6 Luna reasoning support.
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
        response = client.responses.create(
            model=NARRATIVE_MODEL,
            instructions=NARRATIVE_SYSTEM_INSTRUCTIONS,
            input=prompt,
            reasoning={"effort": NARRATIVE_REASONING_EFFORT},
            max_output_tokens=NARRATIVE_MAX_OUTPUT_TOKENS,
        )

        narrative_text = response.output_text
        if not narrative_text:
            raise ValueError("OpenAI returned no narrative text")

        usage = response.usage
        logger.info(
            "Narrative generation completed model=%s input_tokens=%s output_tokens=%s reasoning_tokens=%s",
            response.model,
            getattr(usage, "input_tokens", None),
            getattr(usage, "output_tokens", None),
            getattr(getattr(usage, "output_tokens_details", None), "reasoning_tokens", None),
        )
        
    except Exception as e:
        raise Exception(f"Failed to generate narrative with {NARRATIVE_MODEL}: {str(e)}")
    
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
    interpretations: List[Interpretation] = None,
    protective_factors: List[ProtectiveFactor] = None,
) -> str:
    """
    Build the comprehensive narrative-generation prompt.
    """
    adaptation_patterns = adaptation_patterns or []
    clinical_pattern_hypotheses = clinical_pattern_hypotheses or []
    persona_beliefs = persona_beliefs or []
    interpretations = interpretations or []
    protective_factors = protective_factors or []

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

    if persona.baseline_personality:
        personality_delta_text = "\n".join(
            f"- {trait.capitalize()}: {persona.baseline_personality.get(trait, current):.2f} → {current:.2f} "
            f"(delta {current - persona.baseline_personality.get(trait, current):+.2f})"
            for trait, current in persona.current_personality.items()
        )
    else:
        personality_delta_text = "No trustworthy creation-time personality baseline is available for this legacy life."

    baseline_attachment = persona.baseline_attachment_dimensions or {}
    current_attachment = persona.current_attachment_dimensions or {}
    attachment_keys = sorted(set(baseline_attachment) | set(current_attachment))
    attachment_dimensions_text = "\n".join(
        f"- {key.replace('_', ' ').title()}: {baseline_attachment.get(key, current_attachment.get(key, 0)):.2f} → "
        f"{current_attachment.get(key, baseline_attachment.get(key, 0)):.2f} "
        f"(delta {current_attachment.get(key, 0) - baseline_attachment.get(key, current_attachment.get(key, 0)):+.2f})"
        for key in attachment_keys
    ) or "No dimensional attachment trajectory recorded."

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

    interpretations_text = "\n".join(
        f"- Age {item.age_at_event if item.age_at_event is not None else '?'}: "
        f"belief={item.belief_statement or 'none recorded'}; "
        f"adaptation={item.adaptation_strategy or 'none recorded'}; "
        f"developmental reasoning={item.reasoning or 'none recorded'}; "
        f"domains={', '.join(item.developmental_domains or []) or 'none'}; "
        f"pattern effect={item.reinforcement_effect or 'none'}; "
        f"protective factor ids={', '.join(item.protective_factor_ids or []) or 'none'}; "
        f"state implications={item.state_implications or {}}; trait implications={item.trait_implications or {}}"
        for item in interpretations
    ) or "No event-level developmental interpretations recorded."

    protective_factors_text = "\n".join(
        f"- id={factor.id}; {factor.factor_type.replace('_', ' ').title()}"
        f" (active from age {factor.active_from_age if factor.active_from_age is not None else 'unknown'}"
        f"{f' to {factor.active_to_age}' if factor.active_to_age is not None else ', ongoing or end not recorded'}; "
        f"buffers: {', '.join(factor.domains_buffered or []) or 'no domains recorded'}): "
        f"{factor.description or 'No description recorded.'}"
        for factor in protective_factors
    ) or "No canonical protective factors recorded. Do not invent a generic resilience story."

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

    active_hypotheses = [
        h for h in clinical_pattern_hypotheses
        if h.status not in ("dismissed", "resolved") and (h.evidence_strength or 0) > 0
    ]

    def _format_evidence(entries) -> str:
        if not entries:
            return "none recorded"
        return "; ".join(
            f"{entry.get('description') or entry.get('type') or 'evidence'}"
            + (f" (age {entry.get('age')})" if entry.get('age') is not None else "")
            for entry in entries
        )

    if active_hypotheses:
        hypotheses_text = "\n".join(
            f"- {h.pattern_key.replace('_', ' ').title()} "
            f"(canonical key: {h.pattern_key}; tier: {h.tier}; status: {h.status}; "
            f"evidence strength: {evidence_strength_label(h.evidence_strength)}; "
            f"direction: {'strengthening' if h.previous_evidence_strength is not None and h.evidence_strength > h.previous_evidence_strength else 'weakening' if h.previous_evidence_strength is not None and h.evidence_strength < h.previous_evidence_strength else 'not established'}). "
            f"Developmental precursors: {', '.join(h.developmental_precursors or []) or 'none recorded'}. "
            f"Current manifestations: {', '.join(h.current_manifestations or []) or 'none recorded'}. "
            f"WHAT SUPPORTS THIS: {_format_evidence(h.supporting_evidence)}. "
            f"WHAT COMPLICATES OR CONTRADICTS THIS: {_format_evidence(h.contradicting_evidence)}."
            for h in active_hypotheses
        )
    else:
        hypotheses_text = (
            "No clinical pattern hypothesis has accumulated enough meaningful canonical evidence. "
            "There is no active hypothesis to formulate; do not introduce syndrome or disorder speculation."
        )

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
Narrative Mode: {persona.narrative_mode}

**PERSONALITY TRAITS (Big Five, 0.0-1.0 scale)**
{personality_text}

**PERSONALITY TRAJECTORY (baseline → current; do not call a baseline temperament a life-caused shift)**
{personality_delta_text}

**ATTACHMENT TRAJECTORY**
Categorical: {persona.baseline_attachment_style or persona.current_attachment_style} → {persona.current_attachment_style}
{attachment_dimensions_text}

**DOCUMENTED EXPERIENCES (Chronological)**
{experiences_text}

**THERAPEUTIC INTERVENTIONS**
{interventions_text}

**CURRENT PSYCHOLOGICAL STATE**
Trauma Markers/Symptoms: {trauma_text}

**STATE TIER (fast-moving, reactive - see the arc below)**
{state_text}

**EVENT → INTERPRETATION/BELIEF → ADAPTATION → PATTERN LINKS**
(Canonical event-level engine interpretations. Use these to explain developmental mechanism; do not manufacture a causal bridge where none is recorded.)
{interpretations_text}

**PROTECTIVE FACTORS AND WHAT THEY BUFFER**
(Explain what each factor counteracts using its recorded description/domains and the pattern trajectory. Do not collapse these into generic resilience.)
{protective_factors_text}

**EMERGING DEVELOPMENTAL PATTERNS (reinforced more than once, not yet established)**
{emerging_patterns_text}

**ENGINE'S OWN FORMULATION - ESTABLISHED DEVELOPMENTAL PATTERNS**
(CURRENTLY active and durable. Built from the full timeline, not any single event.)
{established_patterns_text}

**HISTORICALLY IMPORTANT PATTERNS - NOW WEAKENING OR RESOLVED**
(These may explain the lifespan trajectory, but they are NOT current dominant patterns. Describe how they developed, were reinforced, and later weakened or resolved.)
{historical_patterns_text}

**ENGINE'S OWN FORMULATION - CLINICAL PATTERN HYPOTHESES**
(Only active, meaningfully evidenced canonical hypotheses. Tiered and evidence-tracked; never a diagnosis.)
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

4a. **Builds explicit developmental mechanisms from canonical links**:
   - Answer the chain WHAT HAPPENED → WHAT IT TAUGHT THEM → HOW THEY ADAPTED → HOW THAT FUNCTIONS NOW.
   - Use the recorded event interpretations, beliefs, adaptation strategies, reasoning, pattern effects, and chronology above. Do not reduce this to "event happened, therefore symptom."

4b. **Synthesizes current struggles instead of listing metrics**:
   - Translate current State, attachment, active coping patterns, and earned personality shifts into lived functioning: relationships, vulnerability, threat response, trust, mood, regulation, avoidance, and security.
   - Name tensions in the data, such as guardedness alongside durable attachment, rather than flattening the person into one pathology.

4c. **Handles clinical-pattern hypotheses with diagnostic humility but analytical clarity**:
   - Surface ONLY the active canonical hypotheses listed above. For each, explain the plain-language resemblance, current strength, why Rubicks is considering it, WHAT SUPPORTS THIS, WHAT COMPLICATES OR CONTRADICTS THIS, and WHAT IS STILL UNKNOWN.
   - Use "consistent with," "resembles," "raises the possibility of," "warrants consideration," or "current evidence supports/does not establish." Distinguish adaptation pattern, syndrome-like resemblance, hypothesis, and confirmed diagnosis.
   - Never create a diagnosis or hypothesis from event keywords, current State values, or general psychological knowledge alone. If the canonical hypothesis section is empty, say no larger syndrome-like pattern is currently supported and do not speculate.
   - Missing evidence must come from explicit gaps or contradictions in the canonical hypothesis data. Do not invent absent symptoms or emit a canned checklist.

4d. **Explains protective mechanisms specifically**:
   - For each canonical protective factor, explain what belief, State domain, attachment expectation, or coping pattern it counteracted when that connection is supported by the factor's recorded domains and the interpretation/pattern trajectory.
   - No generic "resilience" paragraph. If no protective factor is recorded, do not invent one.

5. **Organizes narrative into these sections** (use markdown headers):

## EXECUTIVE SUMMARY
(Use the subheading ### THE WHOLE PICTURE. In 2-3 paragraphs, formulate who this person became, what they are dealing with now, and the central developmental mechanism. Lead with THE VERDICT only if a currently established pattern exists. If only weakening/resolved patterns exist, describe their historical importance and present trajectory.)

## DEVELOPMENTAL FORMULATION
(Use these subheadings:
### HOW THEY GOT HERE — a concise chronological account by developmentally relevant periods, emphasizing turning points rather than retelling every event.
### WHAT THEY LEARNED ABOUT THEMSELVES AND OTHERS — beliefs/interpretations earned from the canonical links.
### HOW THEY LEARNED TO COPE — active and historical adaptation trajectories, including emerged, reinforced, weakened, and resolved.)

## CURRENT FORMULATION
(Use these subheadings:
### WHAT THEY ARE STRUGGLING WITH NOW — synthesize current lived functioning from State, attachment, active patterns, and earned trait shifts; do not merely repeat values.
### WHAT MAY BE TAKING SHAPE — for EACH active canonical clinical-pattern hypothesis, explain strength, supporting evidence, contradicting/complicating evidence, and what is genuinely still unknown. If none exist, say so briefly without adding pathology.
### WHAT PROTECTS THEM — connect canonical protective factors to the beliefs, domains, attachment expectations, or patterns they counteract.
### WHAT WE STILL DON'T KNOW — concise and case-specific; only recorded gaps implied by canonical evidence, never a generic diagnostic checklist.)

## TREATMENT RESPONSE
(If interventions exist: how support affected mechanisms, current struggles, hypotheses, or protective processes. If none exist, say no added intervention response can be evaluated.)

## PROGNOSIS & RECOMMENDATIONS
(Future outlook based on actual history: What's realistic? What additional support needed? Acknowledge both challenges and strengths)

**CRITICAL REQUIREMENTS:**
- Base ALL analysis on the actual background provided - DO NOT make up a happy childhood
- If parents were addicted/neglectful → Describe insecure/disorganized attachment
- If abuse occurred → Describe trauma impact, not "resilience overcame everything"
- If environment was chaotic → Describe hypervigilance, not "adapted well"
- Be empathetic but clinically accurate about the REAL impact of adversity
- Acknowledge protective factors where they exist, but don't minimize trauma
- Preserve complexity and contradictions; do not flatten a person into one dominant pathology
- This is a developmental formulation for a hypothetical simulator, not a diagnostic report
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
