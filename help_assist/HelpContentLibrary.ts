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
      tooltip: "Comprehensive developmental and clinical history - THE MOST IMPORTANT FIELD",
      whatToInclude: [
        "Family structure and parenting style (e.g., 'single mother, father absent')",
        "Early childhood environment (0-6 years: stable vs. chaotic, nurturing vs. neglectful)",
        "Attachment patterns with primary caregivers",
        "Significant trauma or adverse experiences (with ages)",
        "School and peer relationships",
        "Major life transitions (divorce, moves, losses)",
        "Medical or psychiatric history",
        "Current symptoms or presenting concerns",
        "Protective factors and strengths",
        "Cultural or socioeconomic context"
      ],
      examples: [
        {
          title: "Example 1: Depression with Childhood Trauma",
          text: "28-year-old male presenting with major depressive disorder. Raised by emotionally neglectful, alcoholic parents (ages 0-12). Father physically absent, mother emotionally unavailable and verbally harsh. Witnessed domestic violence between parents (ages 4-8). Parents divorced when he was 10, lived primarily with mother. First depressive episode at age 15 after being bullied at school. Struggled academically despite high intelligence. Brief period of substance experimentation in college (ages 18-20) but discontinued. Currently experiencing recurrent depression, low self-esteem, difficulty maintaining relationships. Strengths include high conscientiousness, creative outlets (music), and stable employment."
        },
        {
          title: "Example 2: Anxiety with Perfectionism",
          text: "22-year-old female college student with generalized anxiety disorder. Raised in upper-middle-class family by high-achieving, perfectionistic parents (both physicians). Early childhood was materially stable but emotionally cold - parents prioritized achievement over emotional connection. Developed perfectionism and performance anxiety by age 8. Excelled academically but at cost of chronic stress and poor self-care. Experienced panic attacks starting at age 16 during exam periods. Recently developed insomnia and health anxiety. Has few close friendships due to difficulty being vulnerable. Strengths include intelligence, work ethic, and recent willingness to seek help."
        },
        {
          title: "Example 3: PTSD from Combat",
          text: "34-year-old male military veteran with PTSD. Grew up in stable, loving middle-class home with supportive parents and two siblings. No childhood trauma or mental health history. Joined military at age 20, deployed to Afghanistan at age 22. During deployment, witnessed multiple casualties including death of close friend in IED explosion. Returned at age 23 with nightmares, hypervigilance, emotional numbing. Struggled to readjust to civilian life. Married at 26, relationship strained by PTSD symptoms (irritability, withdrawal, avoidance). Divorced at 30. Currently experiencing increased symptoms after car accident triggered trauma memories. Strengths include strong pre-trauma foundation, intelligence, and support from veteran community."
        },
        {
          title: "Example 4: Borderline Personality Development",
          text: "26-year-old female with borderline personality disorder. Mother had untreated bipolar disorder, creating chaotic and unpredictable home environment. Father left when she was 3. Experienced emotional neglect and intermittent verbal abuse throughout childhood. Developed insecure/disorganized attachment. Sexually molested by mother's boyfriend at age 11, which she didn't disclose until age 18. First suicide attempt at age 14 following breakup. Multiple brief hospitalizations during late teens for self-harm and suicidal ideation. Unstable relationship history characterized by intense idealization/devaluation cycles. Currently in DBT treatment, showing some progress in emotion regulation. Strengths include artistic talent, intelligence, and growing self-awareness."
        },
        {
          title: "Example 5: Child with ADHD and Family Stress",
          text: "9-year-old male with ADHD, combined type. Born to young parents (both 19) who were unprepared for parenthood. Early childhood marked by frequent moves due to parents' financial instability. Parents divorced when he was 4, with contentious custody battle. Currently lives primarily with mother, who struggles financially as single parent. Father has inconsistent involvement. ADHD symptoms (inattention, hyperactivity, impulsivity) apparent since age 5 but not diagnosed until age 8. Struggles academically and socially - peers find him 'annoying,' leading to rejection and conflict. Teachers report he's 'smart but can't focus.' Recently started medication with some improvement. Strengths include creativity, enthusiasm, and close relationship with maternal grandmother who provides stability."
        }
      ],
      tips: [
        "Write 200-500 words for best results - more detail = more accurate simulation",
        "Include BOTH problems AND strengths/protective factors",
        "Specify ages when significant events occurred",
        "Think like a therapist taking an intake history",
        "Use concrete examples rather than vague descriptions",
        "Include family dynamics and attachment patterns",
        "Mention cultural or socioeconomic factors if relevant"
      ],
      commonMistakes: [
        "Being too vague ('had a difficult childhood' - specify what made it difficult!)",
        "Only listing problems without any strengths",
        "Omitting ages when events occurred",
        "Leaving out family/parenting information",
        "Not mentioning current symptoms or concerns"
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
        answer: "More is better! For backstory, aim for 200-500 words. Include specific ages, events, and family context. Think of it like writing a clinical intake summary."
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
