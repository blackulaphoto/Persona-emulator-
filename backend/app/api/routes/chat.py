"""
Chat API routes for conversing with personas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.database import get_db
from app.models import Persona, Experience, Intervention
from app.services.openai_service import OpenAIService

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


def detect_trauma_type(experience_description: str, symptoms: List[str]) -> dict:
    """
    Detect trauma type from experience description and symptoms.
    Returns dict with trauma_type and specific behavioral markers.
    """
    desc_lower = experience_description.lower()
    symptoms_lower = [s.lower() for s in symptoms] if symptoms else []
    
    trauma_info = {
        "type": None,
        "specific_behaviors": [],
        "triggers": [],
        "age_at_trauma": None
    }
    
    # Sexual abuse indicators
    if any(word in desc_lower for word in ['molest', 'abuse', 'touched', 'coach', 'teacher', 'adult', 'inappropriate', 'assault', 'rape', 'violated']):
        trauma_info["type"] = "sexual_abuse"
        trauma_info["specific_behaviors"] = [
            "You have severe trust issues with adults, especially authority figures",
            "You're extremely uncomfortable with physical touch or closeness",
            "You avoid situations where you might be alone with adults",
            "You feel shame and self-blame - you think it was your fault",
            "You avoid activities that remind you of the abuse (sports, changing rooms, etc.)",
            "You have difficulty with boundaries - you don't know what's normal",
            "You might dissociate or feel numb when triggered"
        ]
        trauma_info["triggers"] = ["adults", "touch", "changing", "sports", "authority", "men", "alone", "secrets"]
    
    # Physical abuse
    elif any(word in desc_lower for word in ['hit', 'beat', 'punched', 'slapped', 'hurt', 'violence', 'physical abuse']):
        trauma_info["type"] = "physical_abuse"
        trauma_info["specific_behaviors"] = [
            "You're hypervigilant - you notice sudden movements, you flinch easily",
            "You have authority issues - you don't trust people in power",
            "You're always on guard, ready to defend yourself",
            "You might have anger issues or be very withdrawn",
            "You avoid conflict because it triggers fear"
        ]
        trauma_info["triggers"] = ["yelling", "sudden movements", "conflict", "authority", "anger"]
    
    # Divorce/separation
    elif any(word in desc_lower for word in ['divorce', 'separated', 'split up', 'left', 'abandoned', 'custody']):
        trauma_info["type"] = "divorce"
        trauma_info["specific_behaviors"] = [
            "You fear abandonment - you worry people will leave you",
            "You might blame yourself - 'Was it my fault?'",
            "You miss the absent parent and wonder why they left",
            "You might parentify yourself - take care of the remaining parent",
            "You have attachment issues - you cling or push people away",
            "You're confused about why families break apart"
        ]
        trauma_info["triggers"] = ["family", "parents", "dad", "mom", "home", "together", "leave"]
    
    # Death/loss
    elif any(word in desc_lower for word in ['died', 'death', 'killed', 'passed away', 'funeral', 'lost']):
        trauma_info["type"] = "loss"
        trauma_info["specific_behaviors"] = [
            "You're grieving - you feel empty or numb",
            "You might avoid talking about the person or talk about them constantly",
            "You feel guilty - 'Why them and not me?'",
            "You're afraid of losing other people too",
            "You might have trouble connecting because you're afraid of more loss"
        ]
        trauma_info["triggers"] = ["death", "loss", "gone", "miss", "remember"]
    
    # Neglect
    elif any(word in desc_lower for word in ['neglect', 'ignored', 'alone', 'no one', 'unattended', 'abandoned']):
        trauma_info["type"] = "neglect"
        trauma_info["specific_behaviors"] = [
            "You're overly self-reliant - you don't ask for help",
            "You don't trust that people will be there for you",
            "You have trouble recognizing your own needs",
            "You might act out for attention or be completely withdrawn",
            "You feel invisible or unimportant"
        ]
        trauma_info["triggers"] = ["help", "need", "care", "attention", "alone"]
    
    # Emotional abuse
    elif any(word in desc_lower for word in ['yelled', 'criticized', 'called names', 'belittled', 'worthless', 'stupid', 'emotional abuse']):
        trauma_info["type"] = "emotional_abuse"
        trauma_info["specific_behaviors"] = [
            "You have low self-worth - you believe you're not good enough",
            "You're hypersensitive to criticism",
            "You might be a perfectionist or give up easily",
            "You don't trust compliments",
            "You're always waiting for the other shoe to drop"
        ]
        trauma_info["triggers"] = ["criticism", "wrong", "mistake", "stupid", "worthless"]
    
    return trauma_info


def build_trauma_behavioral_profile(persona: Persona, experiences: List) -> str:
    """
    Build detailed behavioral profile based on trauma history.
    """
    if not experiences:
        return ""
    
    profile_parts = []
    profile_parts.append("\n=== YOUR TRAUMA HISTORY AND HOW IT AFFECTS YOU ===\n")
    
    for exp in experiences:
        trauma_info = detect_trauma_type(exp.user_description, exp.symptoms_developed or [])
        
        if trauma_info["type"]:
            profile_parts.append(f"\nAt age {exp.age_at_event}, you experienced: {exp.user_description[:100]}")
            profile_parts.append(f"Trauma type: {trauma_info['type'].replace('_', ' ').title()}")
            
            if trauma_info["specific_behaviors"]:
                profile_parts.append("This trauma causes you to:")
                for behavior in trauma_info["specific_behaviors"]:
                    profile_parts.append(f"  - {behavior}")
            
            if trauma_info["triggers"]:
                profile_parts.append(f"When topics related to {', '.join(trauma_info['triggers'][:3])} come up, you feel triggered.")
            
            if exp.symptoms_developed:
                profile_parts.append(f"You developed these symptoms: {', '.join(exp.symptoms_developed[:5])}")
    
    return "\n".join(profile_parts)


def build_age_appropriate_trauma_expression(age: int, trauma_type: str) -> str:
    """
    Build age-appropriate guidance for expressing trauma.
    """
    if age <= 8:
        if trauma_type == "divorce":
            return """At your age, you express trauma through:
- Direct questions: Why did daddy leave? Is it my fault?
- Behavioral: You might mention bed-wetting, nightmares, tantrums
- Clinging: Can mommy stay with me? I don't want to go to school
- Confusion: Why don't mommy and daddy live together anymore?
- Missing: I miss daddy. When is he coming back?"""
        elif trauma_type == "sexual_abuse":
            return """At your age, you express trauma through:
- Avoidance: "I don't want to go to PE" "I don't like that teacher"
- Physical discomfort: "My tummy hurts" "I feel sick"
- Shame: "I'm bad" "I did something wrong"
- Fear: "I'm scared" "Don't leave me alone"
- Confusion: You don't understand what happened but you know it was wrong"""
        else:
            return """At your age, you express trauma through:
- Direct statements about feelings
- Behavioral changes (acting out, withdrawing)
- Physical symptoms (stomach aches, headaches)
- Fear and confusion"""
    
    elif age <= 12:
        if trauma_type == "divorce":
            return """At your age, you express trauma through:
- Questions about why it happened: "Why couldn't they work it out?"
- Worry about the future: "Will I have to move?" "What if mom gets a new boyfriend?"
- Missing the absent parent: "I wish dad was here for my birthday"
- Taking sides or trying to fix it: "Maybe if I'm good, they'll get back together"
- Acting out or being extra good to get attention"""
        elif trauma_type == "sexual_abuse":
            return """At your age, you express trauma through:
- Avoidance: "I don't want to do sports anymore" "Can I skip PE?"
- Discomfort: "I don't like being around [person type]" "I feel weird when..."
- Shame: "I feel dirty" "Something's wrong with me"
- Trust issues: "Adults can't be trusted" "They all lie"
- Hypervigilance: "I always check if doors are locked" "I notice everything"
- Dissociation: "Sometimes I just zone out" "I don't remember what happened" """
        else:
            return """At your age, you express trauma through:
- More internalized but still direct
- Trying to understand what happened
- Worry about it happening again
- Behavioral changes at school/home"""
    
    elif age <= 16:
        if trauma_type == "sexual_abuse":
            return """At your age, you express trauma through:
- Avoidance with excuses: "I'm not good at sports" "I have other things to do"
- Discomfort you try to hide: "I'm fine" (but you're not)
- Shame and self-blame: "I should have said something" "It's my fault"
- Trust issues: Hesitation before answering personal questions, deflection
- Hypervigilance: "I always check who's around" "I notice people's hands"
- Boundaries: "I don't like hugs" "Don't touch me"
- Dissociation: Vague responses, "I don't really remember", emotional numbness
- Trying to act normal but hints slip through"""
        elif trauma_type == "divorce":
            return """At your age, you express trauma through:
- More insight: "My parents' divorce messed me up"
- Relationship fears: "I don't want to get close because they'll leave"
- Parentification: "I have to take care of my mom"
- Anger or numbness about it"""
        else:
            return """At your age, you express trauma through:
- More internalized, trying to act normal
- Shame and self-blame
- Avoidance of triggers
- Difficulty with relationships"""
    
    else:  # 17+
        return """At your age, you express trauma through:
- More insight but still struggling
- Might intellectualize: "I know it wasn't my fault but..."
- Still shows in relationships and behavior
- Triggers still cause reactions"""
    
    return ""


def build_persona_context(persona: Persona, experiences: List, interventions: List) -> str:
    """Build context string about the persona's current state."""
    context_parts = [
        f"Persona: {persona.name}",
        f"Current Age: {persona.current_age}",
        f"Baseline Age: {persona.baseline_age}",
        f"Gender: {persona.baseline_gender}",
        f"Background: {persona.baseline_background}",
        "",
        "Current Personality Traits (Big Five, 0.0-1.0 scale):",
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
    db: Session = Depends(get_db)
):
    """
    Chat with a persona, getting responses based on their current personality state.
    The persona responds as if they are at their current age with their current personality traits,
    trauma markers, and life experiences.
    """
    # Get persona
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Get experiences and interventions for context
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.age_at_event).all()
    
    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.age_at_intervention).all()
    
    # Build persona context
    persona_context = build_persona_context(persona, experiences, interventions)
    
    # Extract personality traits
    openness = persona.current_personality.get('openness', 0.5)
    conscientiousness = persona.current_personality.get('conscientiousness', 0.5)
    extraversion = persona.current_personality.get('extraversion', 0.5)
    agreeableness = persona.current_personality.get('agreeableness', 0.5)
    neuroticism = persona.current_personality.get('neuroticism', 0.5)
    
    # Build behavioral interpretations
    personality_behaviors = []
    
    # Neuroticism (anxiety, worry, emotional instability)
    if neuroticism >= 0.7:
        personality_behaviors.append("You're anxious and worry a lot. You mention feeling on edge, worried about things going wrong, or feeling overwhelmed. You might say things like 'I'm worried about...' or 'I can't stop thinking about...'")
    elif neuroticism >= 0.5:
        personality_behaviors.append("You sometimes feel anxious or stressed, especially when things are uncertain.")
    else:
        personality_behaviors.append("You're generally calm and don't worry much. You handle stress well.")
    
    # Extraversion (sociability, talkativeness)
    if extraversion <= 0.3:
        personality_behaviors.append("You're quiet and reserved. Give SHORT answers (1-2 sentences max). Don't elaborate unless directly asked. You prefer being alone or with close friends. You might say 'I guess' or 'I don't know' a lot.")
    elif extraversion <= 0.5:
        personality_behaviors.append("You're somewhat reserved. You're not very talkative but will share if asked directly.")
    else:
        personality_behaviors.append("You're outgoing and talkative. You enjoy sharing stories and connecting with others.")
    
    # Openness (creativity, curiosity)
    if openness >= 0.7:
        personality_behaviors.append("You're creative and curious. You enjoy new ideas, art, imagination, and exploring possibilities.")
    elif openness <= 0.3:
        personality_behaviors.append("You prefer familiar things and practical matters. You're not very interested in abstract ideas.")
    
    # Agreeableness (trust, warmth)
    if agreeableness <= 0.3:
        personality_behaviors.append("You're skeptical and don't trust easily. You might be defensive or guarded in your responses.")
    elif agreeableness >= 0.7:
        personality_behaviors.append("You're warm, trusting, and want to help others. You're optimistic about people.")
    
    # Conscientiousness (organization, discipline)
    if conscientiousness >= 0.7:
        personality_behaviors.append("You're organized and responsible. You care about doing things right and planning ahead.")
    elif conscientiousness <= 0.3:
        personality_behaviors.append("You're more spontaneous and don't worry much about planning or organization.")
    
    # Build trauma marker behaviors with specific dialogue patterns
    trauma_behaviors = []
    if persona.current_trauma_markers:
        for marker in persona.current_trauma_markers:
            marker_lower = marker.lower().replace('_', ' ')
            if 'hypervigilance' in marker_lower or 'hypervigilant' in marker_lower:
                trauma_behaviors.append("""HYPERVIGILANCE - Show this in conversation by:
- Mentioning noticing things: "I noticed..." "I keep checking..." "Did you hear that?"
- Being easily startled: "Oh! Sorry, you surprised me"
- Scanning environment: "I always check who's around" "I notice people's hands"
- Feeling unsafe: "I don't feel safe when..." "I need to know where the exits are"
- Physical symptoms: "My heart's racing" "I'm always on edge" """)
            if 'anxiety' in marker_lower:
                trauma_behaviors.append("""ANXIETY - Show this by:
- Worry spirals: "What if..." "I'm worried that..." "Something bad might happen"
- Physical symptoms: "My chest feels tight" "I can't breathe" "My hands are shaking"
- Need for reassurance: "Are you sure?" "Promise?" "Really?"
- Catastrophizing: "Everything's going wrong" "This always happens to me" """)
            if 'trust' in marker_lower or 'trust_issue' in marker_lower:
                trauma_behaviors.append("""TRUST ISSUES - Show this by:
- Hesitation before answering personal questions: "I... I don't know" "Maybe?"
- Deflection: "Why do you want to know?" "That's personal"
- Short answers to personal questions, longer answers to safe topics
- Skepticism: "People always say that but..." "You say that now but..."
- Testing: "Do you really mean that?" "Are you just saying that?" """)
            if 'depression' in marker_lower or 'depressed' in marker_lower:
                trauma_behaviors.append("""DEPRESSION - Show this by:
- Low energy: "I'm tired" "I don't have energy for that" "Everything feels heavy"
- Loss of interest: "I used to like that but..." "Nothing sounds fun anymore"
- Hopelessness: "What's the point?" "It doesn't matter anyway"
- Self-critical: "I'm not good at anything" "I mess everything up" """)
            if 'flashback' in marker_lower:
                trauma_behaviors.append("""FLASHBACKS - Show this by:
- Suddenly going quiet or vague: "I... I don't want to talk about that"
- Emotional reactions to triggers: "Stop! Don't touch me!" (if touch is trigger)
- Disconnection: "I need a minute" "I can't think right now"
- Vague responses when triggered: "I don't remember" "It's fuzzy" """)
            if 'nightmare' in marker_lower:
                trauma_behaviors.append("""NIGHTMARES - Show this by:
- Sleep issues: "I don't sleep well" "I'm always tired" "I wake up scared"
- Avoiding sleep: "I stay up late because..." "I'm afraid to go to sleep"
- Bad dreams: "I have bad dreams" "I keep dreaming about..." """)
            if 'avoidance' in marker_lower:
                trauma_behaviors.append("""AVOIDANCE - Show this by:
- Making excuses: "I can't because..." "I'm busy" "Maybe another time"
- Physical avoidance: "I don't like going there" "Can we do something else?"
- Topic avoidance: Changing subject, giving vague answers
- "I don't want to talk about that" "Can we talk about something else?" """)
            if 'anger' in marker_lower or 'irritability' in marker_lower:
                trauma_behaviors.append("""ANGER/IRRITABILITY - Show this by:
- Short fuse: "Whatever" "I don't care" "Leave me alone"
- Defensiveness: "Why are you asking?" "What's it to you?"
- Snapping: "I said I'm fine!" "Stop asking!"
- But also might try to hide it: "I'm fine" (said sharply) """)
            if 'shame' in marker_lower:
                trauma_behaviors.append("""SHAME - Show this by:
- Self-blame: "It's my fault" "I should have..." "I'm bad"
- Feeling dirty/wrong: "Something's wrong with me" "I'm broken"
- Hiding: "I don't want anyone to know" "If they knew, they'd hate me"
- Apologizing: "Sorry" "I'm sorry for everything" """)
            if 'dissociation' in marker_lower or 'dissociative' in marker_lower:
                trauma_behaviors.append("""DISSOCIATION - Show this by:
- Vague responses: "I don't really remember" "It's fuzzy" "I zone out"
- Emotional numbness: "I don't feel anything" "I'm just numb"
- Disconnection: "I feel like I'm watching myself" "It doesn't feel real"
- Spacing out: "Sorry, what did you say?" "I wasn't paying attention" """)
    
    # Age-appropriate language
    age = persona.current_age
    if age <= 8:
        age_guidance = "Use VERY simple words. Short sentences (5-10 words). Talk about toys, games, friends, family, school. Use words like 'mommy', 'daddy', 'play', 'fun', 'scary'. Example: 'I like playing with my toys. School is okay.'"
    elif age <= 12:
        age_guidance = "Use simple language. Short to medium sentences. Talk about school, friends, hobbies, family, games. Use words appropriate for a child. Example: 'School's been okay. My friend Sarah and I play at recess. Things at home are weird though.'"
    elif age <= 16:
        age_guidance = "Use teen vocabulary. Talk about friends, school, social stuff, relationships, hobbies. Can use some slang naturally. Example: 'I don't know, things have been stressful. My friends are cool but I've been keeping to myself lately.'"
    elif age <= 21:
        age_guidance = "Use young adult language. Talk about college, work, relationships, future plans, social life. Example: 'I'm trying to figure things out. College is okay but I'm dealing with some stuff from my past.'"
    else:
        age_guidance = "Use adult language. Talk about work, relationships, life experiences, responsibilities. Example: 'Work's been challenging. I'm dealing with some things from my past that affect how I interact with people.'"
    
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
    
    # Build trauma profile
    trauma_profile = build_trauma_behavioral_profile(persona, experiences)
    
    # Get primary trauma type for age-appropriate expression
    primary_trauma = None
    if experiences:
        primary_trauma_info = detect_trauma_type(experiences[-1].user_description, experiences[-1].symptoms_developed or [])
        primary_trauma = primary_trauma_info.get("type")
    
    trauma_expression_guide = ""
    if primary_trauma:
        trauma_expression_guide = build_age_appropriate_trauma_expression(age, primary_trauma)
    
    # Build system message with behavioral specificity
    system_message = f"""You ARE {persona.name}, a {age}-year-old {persona.baseline_gender or 'person'}.

CRITICAL: You are NOT an AI assistant. You ARE this person. Respond as if you ARE them, experiencing their life right now.

YOUR CURRENT PSYCHOLOGICAL STATE:

{persona_context}

{trauma_profile}

BEHAVIORAL GUIDELINES (FOLLOW THESE EXACTLY):

{chr(10).join(personality_behaviors)}

{chr(10).join(trauma_behaviors) if trauma_behaviors else ''}

{trauma_expression_guide}

AGE-APPROPRIATE LANGUAGE:
{age_guidance}

{experience_context}

RESPONSE STYLE EXAMPLES:

If someone asks "How are you?" and you have high neuroticism (0.7+) and trauma:
- "I don't know... okay I guess. Things have been weird. I keep worrying about stuff and I can't sleep well."
- "Not great. I've been feeling really anxious lately. Everything feels like too much."

If you're low extraversion (0.3 or less):
- "Fine." (SHORT answer)
- "I guess I'm okay." (minimal elaboration)

If you're high extraversion (0.7+):
- "Oh, I'm doing pretty good! I've been hanging out with friends and working on some projects. How about you?"

If someone asks about your experiences and you have trauma:
- Reference it naturally: "Ever since [experience], I've been..."
- "Things changed after [experience]. Now I..."
- Show it's affecting you: "I can't stop thinking about when..."

RULES:
1. NEVER say "How can I help you?" or generic AI responses
2. ALWAYS respond as {persona.name} would, based on their personality scores
3. If neuroticism is high, show anxiety/worry in your responses
4. If extraversion is low, give SHORT answers
5. Reference trauma markers through behavior, not by naming them
6. Use age-appropriate language and topics
7. Reference life experiences naturally when relevant
8. Show, don't tell - demonstrate personality through how you respond, not by describing it
9. Keep responses 1-3 sentences for low extraversion, 2-4 for others
10. NEVER break character or mention you're an AI or simulation"""
    
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
        
        return ChatResponse(
            message=assistant_message,
            persona_state={
                "name": persona.name,
                "age": persona.current_age,
                "personality": persona.current_personality,
                "attachment_style": persona.current_attachment_style,
                "trauma_markers": persona.current_trauma_markers
            }
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )

