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

from app.models.persona import Persona
from app.models.experience import Experience
from app.models.intervention import Intervention
from app.models.persona_narrative import PersonaNarrative


async def generate_persona_narrative(
    db: Session,
    persona_id: str
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
    
    # Fetch persona with all related data
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
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
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
    
    prompt = f"""Generate a comprehensive psychological narrative for this persona.

**PERSONA OVERVIEW**
Name: {persona.name}
Age: {persona.current_age}
Gender: {persona.baseline_gender or 'Not specified'}
Attachment Style: {persona.current_attachment_style}

**PERSONALITY TRAITS (Big Five)**
{personality_text}

**DEVELOPMENTAL TIMELINE**
{experiences_text}

**THERAPEUTIC INTERVENTIONS**
{interventions_text}

**CURRENT PSYCHOLOGICAL STATE**
Trauma Markers/Symptoms: {trauma_text}

---

**GENERATE A COMPREHENSIVE NARRATIVE WITH THESE SECTIONS:**

## EXECUTIVE SUMMARY
(2-3 paragraphs: Who is this person? Core psychological profile, key developmental themes, current functioning level)

## DEVELOPMENTAL TIMELINE
(Chronological narrative: How did experiences shape their development? Connect each event to personality/behavioral changes. Use age markers.)

## CURRENT PRESENTATION
(How they navigate the world: Daily behaviors, relationship patterns, coping mechanisms, emotional regulation, cognitive patterns)

## TREATMENT RESPONSE
(If interventions exist: How did therapy help? What changed? What symptoms improved? Include specific impacts.)

## PROGNOSIS & RECOMMENDATIONS
(Future outlook: What's the trajectory? What additional support needed? Realistic goals? Expected outcomes?)

**GUIDELINES:**
- Write in professional yet compassionate tone
- Use psychological terminology accurately
- Connect experiences to behaviors causally
- Be specific about symptom manifestations
- Acknowledge complexity and nuance
- Total length: 1200-1800 words
- Use markdown headers for sections
- Be empathetic but clinical

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
    limit: int = 10
) -> List[PersonaNarrative]:
    """
    Get all narratives for a persona, ordered by most recent first.
    """
    narratives = db.query(PersonaNarrative).filter(
        PersonaNarrative.persona_id == persona_id
    ).order_by(PersonaNarrative.generated_at.desc()).limit(limit).all()
    
    return narratives


async def get_narrative_by_id(
    db: Session,
    narrative_id: str
) -> PersonaNarrative:
    """
    Get a specific narrative by ID.
    """
    narrative = db.query(PersonaNarrative).filter(
        PersonaNarrative.id == narrative_id
    ).first()
    
    if not narrative:
        raise ValueError(f"Narrative {narrative_id} not found")
    
    return narrative


async def delete_narrative(
    db: Session,
    narrative_id: str
) -> bool:
    """
    Delete a narrative.
    """
    narrative = db.query(PersonaNarrative).filter(
        PersonaNarrative.id == narrative_id
    ).first()
    
    if not narrative:
        return False
    
    db.delete(narrative)
    db.commit()
    return True
