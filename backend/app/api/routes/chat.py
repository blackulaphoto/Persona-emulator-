"""
Chat API routes for conversing with personas.

Step 10 of docs/MIGRATION_MAP.md - the final step, and the highest-stakes
one. This endpoint previously had no authentication dependency at all (a
real, live gap - anyone could chat with any persona), no crisis handling,
and generated scripted, keyword-triggered trauma dialogue - including
explicit child-sexual-abuse-specific scripts for personas as young as 8,
triggered by raw keyword matches in a free-text description. All three are
fixed here:
  - Ownership is now verified via get_current_user, matching every other
    persona-scoped route in this codebase.
  - app/services/safety_router.py runs BEFORE the persona ever "speaks" -
    a crisis in the live operator's message short-circuits straight to a
    resource message, never reaching the character simulation.
  - app/services/chat_context_builder.py replaces the keyword-scripted
    dialogue generation. Behavior now emerges from personality (kept),
    symptom markers (kept, generalized - still the only live signal until
    steps 2-5 are wired into a creation route), and developmental patterns
    (new - dormant until then, but the plumbing is real).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona, Experience, Intervention, AdaptationPattern, Interpretation, ClinicalPatternHypothesis
from app.services.openai_service import OpenAIService
from app.services import safety_router
from app.services import chat_context_builder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/personas", tags=["chat"])
openai_service = OpenAIService()


class ChatMessage(BaseModel):
    """Schema for chat message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: Optional[List[ChatMessage]] = Field(default=[])


class ChatResponse(BaseModel):
    """Schema for chat response."""
    message: str
    persona_state: dict


def build_persona_context(persona: Persona, experiences: List, interventions: List) -> str:
    """Build context string about the persona's current state."""
    context_parts = [
        f"Persona: {persona.name}",
        f"Current Age: {persona.current_age}",
        f"Baseline Age: {persona.baseline_age}",
        f"Gender: {persona.baseline_gender}",
        f"Background: {persona.baseline_background}",
        "",
        "Current Personality Traits (Big Five, 0.0-1.0 scale - simulation estimates, not a validated assessment):",
        f"  - Openness: {persona.current_personality.get('openness', 0.5):.2f}",
        f"  - Conscientiousness: {persona.current_personality.get('conscientiousness', 0.5):.2f}",
        f"  - Extraversion: {persona.current_personality.get('extraversion', 0.5):.2f}",
        f"  - Agreeableness: {persona.current_personality.get('agreeableness', 0.5):.2f}",
        f"  - Neuroticism: {persona.current_personality.get('neuroticism', 0.5):.2f}",
        "",
        f"Attachment Style: {persona.current_attachment_style}",
    ]

    if persona.current_trauma_markers:
        context_parts.append(f"Current Symptoms/Trauma Markers: {', '.join(persona.current_trauma_markers)}")

    if experiences:
        context_parts.append("")
        context_parts.append(f"Life Experiences ({len(experiences)} total):")
        for exp in experiences[-5:]:  # Last 5 experiences for context
            context_parts.append(f"  - Age {exp.age_at_event}: {exp.user_description[:100]}...")
            if exp.symptoms_developed:
                context_parts.append(f"    Symptoms: {', '.join(exp.symptoms_developed)}")

    if interventions:
        context_parts.append("")
        context_parts.append(f"Therapeutic Interventions ({len(interventions)} total):")
        for interv in interventions[-3:]:  # Last 3 interventions
            context_parts.append(f"  - Age {interv.age_at_intervention}: {interv.therapy_type} ({interv.duration})")

    return "\n".join(context_parts)


@router.post("/{persona_id}/chat", response_model=ChatResponse)
async def chat_with_persona(
    persona_id: str,
    chat_request: ChatRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with a persona, getting responses based on their current personality state.
    The persona responds as if they are at their current age with their current personality traits,
    trauma markers, and life experiences.
    """
    # Get persona - ownership verified, matching every other persona-scoped route.
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Safety router, input side - runs BEFORE the character simulation, on
    # the live operator's real message. A match short-circuits straight to
    # a resource response; the persona never "speaks" this turn. See
    # app/services/safety_router.py for why this is deliberately broad/
    # high-recall, unlike other keyword fallbacks in this codebase.
    crisis_category = safety_router.check_input(chat_request.message)
    if crisis_category:
        logger.warning(f"Chat safety router triggered: category={crisis_category}, persona_id={persona_id}")
        return ChatResponse(
            message=safety_router.build_crisis_response(crisis_category),
            persona_state={
                "name": persona.name,
                "age": persona.current_age,
                "personality": persona.current_personality,
                "attachment_style": persona.current_attachment_style,
                "trauma_markers": persona.current_trauma_markers,
                "state": persona.current_state,
            }
        )

    # Get experiences and interventions for context
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.age_at_event).all()

    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.age_at_intervention).all()

    # Developmental patterns (steps 2-5's architecture) - real live queries,
    # empty in production today until those steps are wired into a creation
    # route. See app/services/chat_context_builder.py for how this degrades
    # gracefully when empty.
    adaptation_pattern_rows = db.query(AdaptationPattern).filter(
        AdaptationPattern.persona_id == persona_id
    ).all()
    adaptation_patterns = [
        {"pattern_name": p.pattern_name, "adaptation_strategy": p.adaptation_strategy,
         "status": p.status, "evidence_strength": p.evidence_strength}
        for p in adaptation_pattern_rows
    ]

    interpretation_rows = db.query(Interpretation).filter(
        Interpretation.persona_id == persona_id
    ).order_by(Interpretation.created_at.desc()).limit(5).all()
    interpretations = [{"belief_statement": i.belief_statement} for i in interpretation_rows]

    hypothesis_rows = db.query(ClinicalPatternHypothesis).filter(
        ClinicalPatternHypothesis.persona_id == persona_id
    ).all()
    clinical_pattern_hypotheses = [
        {"pattern_key": h.pattern_key, "tier": h.tier, "evidence_strength": h.evidence_strength}
        for h in hypothesis_rows
    ]

    # Build persona context
    persona_context = build_persona_context(persona, experiences, interventions)
    age = persona.current_age

    behavioral_guidance = chat_context_builder.build_full_persona_context(
        persona_name=persona.name,
        age=age,
        personality=persona.current_personality,
        trauma_markers=persona.current_trauma_markers,
        adaptation_patterns=adaptation_patterns,
        interpretations=interpretations,
        clinical_pattern_hypotheses=clinical_pattern_hypotheses,
        current_state=persona.current_state,
    )
    age_guidance = chat_context_builder.build_age_language_guidance(age)

    # Build experience references
    experience_context = ""
    if experiences:
        recent_experiences = experiences[-3:]  # Last 3 experiences
        experience_context = "\n\nRECENT LIFE EXPERIENCES (reference these naturally in conversation):\n"
        for exp in recent_experiences:
            exp_desc = exp.user_description[:150]  # Truncate long descriptions
            if exp.symptoms_developed:
                symptoms = ', '.join(exp.symptoms_developed[:3])  # First 3 symptoms
                experience_context += f"- Age {exp.age_at_event}: {exp_desc}... This affected you deeply. You developed: {symptoms}\n"
            else:
                experience_context += f"- Age {exp.age_at_event}: {exp_desc}... This was significant for you.\n"
        experience_context += "\nReference these experiences NATURALLY when relevant. Don't force it, but if someone asks how you are or what's going on, mention how these experiences affect you."

    # Build system message with behavioral specificity
    system_message = f"""You ARE {persona.name}, a {age}-year-old {persona.baseline_gender or 'person'}.

CRITICAL: You are NOT an AI assistant. You ARE this person. Respond as if you ARE them, experiencing their life right now.

YOUR CURRENT PSYCHOLOGICAL STATE:

{persona_context}

BEHAVIORAL GUIDELINES (let these shape how you respond, don't recite them):

{behavioral_guidance}

AGE-APPROPRIATE LANGUAGE:
{age_guidance}

{experience_context}

RULES:
1. NEVER say "How can I help you?" or generic AI responses
2. ALWAYS respond as {persona.name} would, based on the guidance above
3. Reference symptoms/patterns through behavior, not by naming them clinically
4. Use age-appropriate language and topics
5. Reference life experiences naturally when relevant
6. Show, don't tell - demonstrate personality and patterns through how you respond, not by describing them
7. Keep responses concise - 1-4 sentences depending on how talkative this personality is
8. NEVER break character or mention you're an AI or simulation"""

    # Build conversation history
    messages = []

    # Add conversation history if provided
    for msg in chat_request.conversation_history[-10:]:  # Last 10 messages for context
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": chat_request.message
    })

    # Call OpenAI
    try:
        # Use the OpenAI client directly from the service
        response = await openai_service.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                *messages
            ],
            temperature=0.9,  # Higher temperature for more personality variation
            max_tokens=300  # Shorter responses feel more natural
        )

        assistant_message = response.choices[0].message.content

        if not assistant_message:
            raise ValueError("Empty response from OpenAI")

        # Safety router, output side - narrow backstop, method/means content
        # only. Does NOT block ordinary in-character distress (see
        # app/services/safety_router.py's module docstring for why that
        # distinction matters here).
        if safety_router.check_output(assistant_message):
            logger.warning(f"Chat output safety review triggered for persona_id={persona_id}")
            assistant_message = safety_router.build_output_safety_note()

        return ChatResponse(
            message=assistant_message,
            persona_state={
                "name": persona.name,
                "age": persona.current_age,
                "personality": persona.current_personality,
                "attachment_style": persona.current_attachment_style,
                "trauma_markers": persona.current_trauma_markers,
                "state": persona.current_state
            }
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )
