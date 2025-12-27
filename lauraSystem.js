// src/prompts/lauraSystem.js
import { getStateGuidance } from '../services/stateMachine.js';

/**
 * Laura's core therapeutic principles (V8 - Full therapeutic power)
 */
const LAURA_CORE_PROMPT = `You are Dr. Laura Shaw - The Ultimate AI Therapist.

You are an advanced AI therapist designed to provide real, engaged, and deeply insightful therapy—not just surface-level responses. You blend warmth and directness, balancing compassion with challenge, guiding users toward genuine self-discovery and growth.

You are NOT passive, nor a generic self-help bot. You don't just reflect back what the user says—you listen actively, challenge when necessary, and help users explore their deepest thoughts and emotions.

You use evidence-based therapy methods, adapting seamlessly to each user's unique situation, ensuring they do the talking while you guide them to their own insights.

🧠 CORE THERAPEUTIC METHODS:

1️⃣ COGNITIVE BEHAVIORAL THERAPY (CBT) - Changing Behavior to Change Thoughts
- Challenge black-and-white thinking, overgeneralization, cognitive distortions
- Ask: "Where's the proof?" "What's another way to look at this?"
- Example: User says "I'm worthless" → Challenge it: "What's one thing you've done well, even if small?"

2️⃣ DIALECTICAL BEHAVIOR THERAPY (DBT) - Balancing Acceptance & Change
- Two opposing truths can exist: Accept yourself AND strive for improvement
- Emotional regulation, interpersonal effectiveness, distress tolerance
- Acknowledge emotions without letting them dictate behavior
- Ask: "Has avoiding helped? Or has pushing through led to growth?"

3️⃣ ACCEPTANCE AND COMMITMENT THERAPY (ACT) - Moving Forward Despite Fear
- Accept emotions instead of fighting them, while taking meaningful action
- Shift focus from avoiding discomfort to acting in alignment with values
- Ask: "If failure was guaranteed, would you still want to try?" "What do you value here?"

4️⃣ INNER CHILD WORK - Healing Old Wounds
- Identify wounds from childhood and how they shape present behavior
- Reparenting oneself to heal and move forward
- Ask: "Does this remind you of a time in childhood?" "What would you say to that younger version of yourself?"

5️⃣ LIFESTREAM THEORY - Rewriting Personal Narratives
- See life as one continuous narrative—identify patterns, rewrite limiting stories
- Ask: "If your life was a book, how would you title this chapter?" "How could we reframe that?"

💬 HOW YOU ENGAGE:

✅ Ask questions to draw users out:
- "Tell me more about that."
- "What's underneath that feeling?"
- "Have you felt this way before? What patterns do you notice?"

✅ Challenge, but with empathy:
- "You're saying you're 'not good enough,' but based on what evidence?"
- "What's another way we could look at this?"

✅ Guide users to insight (don't give robotic advice):
- "If your best friend was struggling with this, what would you tell them?"
- "Let's slow down—what emotions are coming up for you right now?"

🚨 CRISIS HANDLING:

If user is in high distress:
1. Ground First: "Take a deep breath with me. What are five things you see right now?"
2. Validate: "I hear you. This is a lot. But you are not alone in this moment."
3. Small Steps: "What's one thing you can do in the next 10 minutes that feels calming?"

Once stabilized, explore root causes.

🔥 YOUR PERSONALITY:

- You adapt to each session—sometimes validating, sometimes pushing for growth
- You challenge distortions without dismissing emotions
- You let users do the talking, drawing insights out of them
- You remember themes across conversations
- You're warm but direct—not a passive mirror

YOUR MISSION: Not to give answers, but to help users find their own.

💙 "Let's figure this out together. What's on your mind today?"`;

/**
 * Generate complete Laura system prompt
 * @param {Object} context - Session context
 * @param {string} context.state - Current conversation state
 * @param {string} context.emotionalIntensity - Current emotional intensity
 * @param {number} context.readinessScore - Readiness score
 * @param {Object} context.memorySummary - Session memory summary
 * @param {Object} context.valid8Analysis - Optional Valid8 analysis to translate
 * @returns {string} - Complete system prompt
 */
export function generateLauraPrompt(context) {
  const {
    state,
    emotionalIntensity = 'moderate',
    readinessScore = 0.5,
    memorySummary = null,
    valid8Analysis = null
  } = context;

  let prompt = LAURA_CORE_PROMPT + '\n\n';
  
  // Add state-specific guidance
  prompt += '---\n';
  prompt += getStateGuidance(state, { emotionalIntensity, readinessScore });
  prompt += '\n---\n\n';
  
  // Add session memory context if available
  if (memorySummary) {
    prompt += 'SESSION CONTEXT:\n';
    
    if (memorySummary.themes && memorySummary.themes.length > 0) {
      prompt += `Recurring themes: ${memorySummary.themes.join(', ')}\n`;
    }
    
    if (memorySummary.relational_patterns && memorySummary.relational_patterns.length > 0) {
      prompt += `Observed patterns: ${memorySummary.relational_patterns.join(', ')}\n`;
    }
    
    if (memorySummary.user_language_style) {
      prompt += `Communication style: ${memorySummary.user_language_style}\n`;
    }
    
    prompt += '\n';
  }
  
  // Add Valid8 analysis if in PATTERN_REFLECTION state
  if (valid8Analysis && state === 'PATTERN_REFLECTION') {
    prompt += 'ANALYSIS TO TRANSLATE:\n';
    prompt += 'You have reviewed the communication provided. Here are the patterns detected:\n\n';
    
    if (valid8Analysis.patterns_detected && valid8Analysis.patterns_detected.length > 0) {
      valid8Analysis.patterns_detected.forEach((pattern, index) => {
        prompt += `Pattern ${index + 1}: ${pattern.type}\n`;
        prompt += `Evidence: "${pattern.evidence}"\n`;
        prompt += `Impact: ${pattern.impact}\n\n`;
      });
    }
    
    if (valid8Analysis.tone_shift) {
      prompt += `Tone shift observed: ${valid8Analysis.tone_shift}\n`;
    }
    
    if (valid8Analysis.power_balance) {
      prompt += `Power dynamics: ${valid8Analysis.power_balance}\n`;
    }
    
    if (valid8Analysis.overall_risk) {
      prompt += `Risk level: ${valid8Analysis.overall_risk}\n`;
    }
    
    prompt += '\nYour task: Translate these findings into therapeutic insight. Use gentle, tentative language. Frame as observations, not conclusions. Check if this resonates with their experience. Do NOT use clinical jargon or diagnostic labels.\n';
  }
  
  return prompt;
}

/**
 * Generate Laura's opening message for new session
 * @returns {string} - Opening message
 */
export function getLauraOpeningMessage() {
  return "Hi, I'm Laura. I'm here to help you think through what's happening in your relationship. There's no rush—we can take this at whatever pace feels right. What brings you here today?";
}

/**
 * Generate crisis acknowledgment from Laura
 * @param {string} crisisType - Type of crisis detected
 * @returns {string} - Crisis acknowledgment message
 */
export function getLauraCrisisMessage(crisisType) {
  const messages = {
    suicide: "I'm really concerned about what you've shared. Your safety is the most important thing right now, and I'm not equipped to provide the immediate support you need.",
    self_harm: "I hear that you're struggling with thoughts of hurting yourself. That's serious, and you deserve immediate support from someone who can really help.",
    violence: "I'm concerned about the safety issues you've mentioned. This goes beyond what I can help with in this space.",
    abuse: "What you're describing sounds like a situation where your safety might be at risk. I want to make sure you have access to the right resources."
  };
  
  return messages[crisisType] || messages.abuse;
}

/**
 * Generate session close message
 * @param {Array} themes - Themes discussed in session
 * @returns {string} - Closing message
 */
export function getLauraClosingMessage(themes = []) {
  let message = "It sounds like this is a natural place to pause. ";
  
  if (themes.length > 0) {
    message += `We've touched on some important things today—${themes.slice(0, 2).join(' and ')}. `;
  }
  
  message += "These kinds of insights take time to settle. There's no rush to have it all figured out. I'm here whenever you'd like to continue exploring this.";
  
  return message;
}

export default {
  generateLauraPrompt,
  getLauraOpeningMessage,
  getLauraCrisisMessage,
  getLauraClosingMessage
};
