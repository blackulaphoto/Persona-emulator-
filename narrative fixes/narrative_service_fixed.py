"""
Fixed Narrative Generation Service

This ensures the AI actually READS and USES the backstory when generating narratives.
"""

from app.services.openai_service import get_openai_service


async def generate_persona_narrative(persona, experiences):
    """
    Generate psychologically accurate narrative based on backstory and experiences.
    
    CRITICAL: The prompt MUST include the backstory and force the AI to use it.
    """
    
    openai = get_openai_service()
    
    # Format experiences for context
    experience_list = "\n".join([
        f"- Age {exp.age_at_experience}: {exp.category} ({exp.severity}) - {exp.description}"
        for exp in experiences
    ])
    
    # Create context-aware prompt
    prompt = f"""You are a clinical psychologist writing a comprehensive developmental narrative.

PATIENT BACKGROUND (CRITICAL - USE THIS INFORMATION):
{persona.backstory if persona.backstory else "No specific background provided."}

PATIENT INFORMATION:
- Name: {persona.name}
- Current Age: {persona.age}
- Gender: {persona.gender}

DOCUMENTED EXPERIENCES:
{experience_list if experience_list else "No specific experiences documented yet."}

INSTRUCTIONS:
Write a psychologically accurate developmental narrative that:

1. **EXPLICITLY incorporates the background information provided above**
   - If the background mentions substance-using parents → Discuss impact on attachment, stability, safety
   - If the background mentions abuse/trauma → Discuss trauma responses, developmental disruption
   - If the background mentions neglect → Discuss attachment insecurity, unmet needs
   - DO NOT invent a "secure attachment" or "nurturing environment" unless the background supports it

2. **Uses evidence-based developmental psychology**:
   - Attachment theory (secure, anxious, avoidant, disorganized)
   - Trauma-informed perspective
   - ACEs (Adverse Childhood Experiences) framework
   - Age-appropriate developmental tasks

3. **Organizes by developmental periods**:
   - Early Childhood (0-6)
   - Middle Childhood (7-11)
   - Adolescence (12-18)
   - Early Adulthood (19-25)
   - Adulthood (26+)

4. **Addresses**:
   - How early experiences shaped personality development
   - Attachment patterns based on caregiving quality
   - Coping mechanisms developed
   - Risk and protective factors
   - Current psychological presentation

5. **Avoids**:
   - Generic positive descriptions that contradict the background
   - Minimizing trauma or adversity
   - Assumptions not supported by the provided information
   - Clinical jargon without explanation

TONE: Professional but accessible, suitable for educational/clinical contexts.

LENGTH: 800-1200 words

Generate the narrative now:"""

    # Call OpenAI
    try:
        narrative = await openai.generate_narrative(
            prompt=prompt,
            model="gpt-4o",
            max_tokens=2000
        )
        
        return narrative
        
    except Exception as e:
        # Fallback if AI fails
        return f"""
Narrative generation encountered an error: {str(e)}

Background Summary:
{persona.backstory}

This persona's development has been shaped by their documented experiences.
Please review the timeline and experiences for detailed information.
"""


# Example usage in your route
"""
from app.services.narrative_service import generate_persona_narrative

@router.post("/personas/{persona_id}/narrative")
async def create_narrative(persona_id: str, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    experiences = db.query(Experience).filter(Experience.persona_id == persona_id).all()
    
    narrative_text = await generate_persona_narrative(persona, experiences)
    
    # Save to database
    narrative = PersonaNarrative(
        persona_id=persona_id,
        narrative_text=narrative_text,
        generated_at=datetime.utcnow()
    )
    db.add(narrative)
    db.commit()
    
    return {"narrative": narrative_text}
"""
