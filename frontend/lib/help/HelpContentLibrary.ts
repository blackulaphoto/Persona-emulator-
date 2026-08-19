/**
 * Help Content Library
 * 
 * Centralized content for tooltips, examples, and guidance across the app
 */

export const HELP_CONTENT = {
  // ============================================
  // PERSONA CREATION
  // ============================================
  persona: {
    name: {
      tooltip: "The persona's name - can be real (de-identified) or fictional",
      examples: ["Ryan Myers", "Sarah Chen", "Alex Johnson", "Maria Rodriguez"],
      helpText: "Use a realistic name that helps you remember and relate to the person"
    },
    
    age: {
      tooltip: "Current age of the persona (0-120 years)",
      examples: ["28", "15", "42", "7"],
      helpText: "This represents their present-day age in your simulation"
    },
    
    gender: {
      tooltip: "Gender identity of the persona",
      examples: ["Male", "Female", "Non-binary", "Transgender", "Other"],
      helpText: "Choose what's clinically relevant for the case you're building"
    },
    
    backstory: {
      tooltip: "The general shape of their upbringing - kept broad on purpose. Specific events go in Experiences, not here.",
      whatToInclude: [
        "General family structure (e.g., 'single mother, father absent')",
        "Overall tone of early childhood (stable vs. chaotic, warm vs. cold)",
        "How reliable/present their caregivers were",
        "Natural temperament (curious, cautious, sociable, sensitive...)",
        "Broad cultural or socioeconomic context, if relevant"
      ],
      whatNotToInclude: [
        "Specific dated events (a divorce, an assault, a diagnosis) - add these as Experiences after creating the persona",
        "A list of current symptoms - these emerge from the events you add, not from this page",
        "Anything you'd want the AI to analyze on its own timeline - that's what Experiences are for"
      ],
      examples: [
        {
          title: "Example 1: Chaotic but loving",
          text: "Home environment: Chaotic and financially unstable, but affectionate. Caregivers: Raised by a single mother who worked long hours; present but stretched thin. Additional context: Naturally sociable and quick to bounce back from setbacks."
        },
        {
          title: "Example 2: Emotionally cold, high-achieving",
          text: "Home environment: Materially comfortable, emotionally distant. Achievement was valued over connection. Caregivers: Both parents present but reserved and demanding. Additional context: Cautious, perfectionistic temperament from an early age."
        },
        {
          title: "Example 3: Stable and secure",
          text: "Home environment: Stable, predictable, warm. Caregivers: Two reliable, supportive parents. Additional context: Curious and even-tempered as a child."
        }
      ],
      tips: [
        "A sentence or two per question is enough - this just sets the starting point",
        "Describe the general tone, not specific incidents",
        "It's fine to leave the optional field blank",
        "Think temperament and atmosphere, not plot"
      ],
      commonMistakes: [
        "Listing specific events here instead of adding them as Experiences next",
        "Writing a long clinical case history (that's what the Experiences timeline is for)",
        "Naming current symptoms directly - let them emerge from the events you add"
      ]
    }
  },
  
  // ============================================
  // EXPERIENCE CREATION
  // ============================================
  experience: {
    category: {
      tooltip: "Type of experience - choose the most specific category",
      categories: [
        { name: "Trauma", description: "Physical/sexual abuse, assault, natural disaster, accident" },
        { name: "Neglect", description: "Emotional or physical neglect, abandonment" },
        { name: "Loss", description: "Death, divorce, separation, pet loss" },
        { name: "Abuse", description: "Ongoing abuse, domestic violence" },
        { name: "Achievement", description: "Success, award, accomplishment" },
        { name: "Relationship", description: "Significant relationship forming or ending" },
        { name: "Medical", description: "Illness, injury, hospitalization" },
        { name: "Social", description: "Peer experiences, bullying, rejection, acceptance" },
        { name: "Family", description: "Family changes, sibling birth, moving" }
      ]
    },
    
    severity: {
      tooltip: "How impactful was this experience?",
      definitions: {
        mild: "Minor impact, brief distress, full recovery",
        moderate: "Notable impact, some lasting effects, eventual adaptation",
        severe: "Major impact, significant distress, long-term effects",
        extreme: "Life-altering impact, profound distress, lasting trauma"
      },
      examples: {
        mild: "Brief teasing at school, minor disappointment, small success",
        moderate: "Parents' divorce, friend moving away, academic failure",
        severe: "Physical abuse, serious medical event, prolonged bullying",
        extreme: "Sexual assault, parent's death, severe trauma"
      }
    },
    
    age: {
      tooltip: "Age when this experience occurred",
      helpText: "Earlier experiences often have greater developmental impact"
    },
    
    description: {
      tooltip: "Detailed description of what happened",
      examples: [
        "Witnessed father hitting mother during argument. Police were called and father was arrested. Felt scared and confused.",
        "Selected for gifted program at school. Felt proud but also pressure to perform. Parents emphasized importance of achievement.",
        "Sexually molested by older cousin during family gathering. Felt ashamed and afraid to tell anyone. Kept it secret for years."
      ],
      tips: [
        "Include emotional impact ('felt scared, ashamed, confused')",
        "Mention context (where, with whom, what led to it)",
        "Note if it was single incident or ongoing",
        "Describe immediate aftermath or consequences"
      ]
    }
  },
  
  // ============================================
  // INTERVENTION CREATION
  // ============================================
  intervention: {
    modality: {
      tooltip: "Type of therapy or intervention",
      modalities: [
        { name: "CBT", description: "Cognitive Behavioral Therapy - focuses on thoughts and behaviors" },
        { name: "DBT", description: "Dialectical Behavior Therapy - emotion regulation, distress tolerance" },
        { name: "EMDR", description: "Eye Movement Desensitization - trauma processing" },
        { name: "Psychodynamic", description: "Insight-oriented, explores unconscious patterns" },
        { name: "ACT", description: "Acceptance and Commitment Therapy - mindfulness-based" },
        { name: "IFS", description: "Internal Family Systems - parts work" },
        { name: "Medication", description: "Psychopharmacology - antidepressants, mood stabilizers" },
        { name: "Group Therapy", description: "Therapy in group setting" }
      ]
    },
    
    duration: {
      tooltip: "How long did this intervention last?",
      examples: ["12 weeks", "6 months", "2 years", "Ongoing"],
      helpText: "Longer duration usually = greater impact"
    }
  },
  
  // ============================================
  // GENERAL FAQS
  // ============================================
  faq: {
    general: [
      {
        question: "How much detail should I include?",
        answer: "For the Starting Point questions, a sentence or two each is enough - keep it general. Save the detail for Experiences, where you add specific events one at a time and each one gets its own analysis."
      },
      {
        question: "Can I use real client information?",
        answer: "Only if completely de-identified! Change names, dates, locations, and any identifying details. If in doubt, create a composite or fictional case instead."
      },
      {
        question: "What if I don't know all the details?",
        answer: "That's okay! Fill in what you know. You can always add more experiences or details later. The simulation will work with whatever information you provide."
      },
      {
        question: "How does the AI generate narratives?",
        answer: "The AI uses evidence-based psychology principles (attachment theory, trauma research, developmental psychology) to create realistic narratives based on the information you provide."
      },
      {
        question: "Is this tool for diagnosis?",
        answer: "No! This is an EDUCATIONAL tool for learning about psychological development. It should never be used for actual diagnosis or treatment planning."
      },
      {
        question: "Can I delete or edit experiences?",
        answer: "Yes! Each experience has a delete button. You can also regenerate narratives after making changes."
      }
    ]
  }
};

// Helper function to get content by path
export function getHelp(path: string) {
  const parts = path.split('.');
  let content: any = HELP_CONTENT;
  
  for (const part of parts) {
    content = content[part];
    if (!content) return null;
  }
  
  return content;
}
