"""
Narrative Service

Generates comprehensive AI-powered narratives about personas using GPT-4.
"""
import time
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import openai
import os
from app.core.config import settings

from app.models.persona import Persona
from app.models.experience import Experience
from app.models.intervention import Intervention
from app.models.persona_narrative import PersonaNarrative


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
    
    # Count existing narratives for generation number
    existing_count = db.query(PersonaNarrative).filter(
        PersonaNarrative.persona_id == persona_id
    ).count()
    generation_number = existing_count + 1
    
    # Build comprehensive prompt for GPT-4
    prompt = _build_narrative_prompt(persona, experiences, interventions)
    
    # Call GPT-4
    try:
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        client = openai.OpenAI(api_key=api_key)
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
    interventions: List[Intervention]
) -> str:
    """
    Build comprehensive prompt for GPT-4 narrative generation.
    """
    
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

3. **Organizes narrative into these sections** (use markdown headers):

## EXECUTIVE SUMMARY
(2-3 paragraphs: Who is this person? Core psychological profile rooted in their ACTUAL background, key developmental themes, current functioning level)

## DEVELOPMENTAL TIMELINE
(Chronological narrative organized by developmental periods. For each period, describe how the BACKGROUND and experiences shaped development:
- **Early Childhood (0-6)**: How did the caregiving environment affect attachment? What were the actual conditions?
- **Middle Childhood (7-11)**: How did early experiences manifest in school/peer relationships?
- **Adolescence (12-18)**: How did accumulated adversity affect identity formation?
- **Adulthood (19+)**: Current patterns stemming from developmental history)

## CURRENT PRESENTATION
(How they navigate the world NOW: Daily behaviors, relationship patterns, coping mechanisms, emotional regulation - all connected to their actual background and experiences)

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
