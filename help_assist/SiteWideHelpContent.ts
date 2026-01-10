/**
 * SITE-WIDE HELP CONTENT
 * 
 * Tooltips, examples, and guidance for EVERY feature in the app
 */

export const SITE_HELP = {
  // ============================================
  // PERSONA DETAIL PAGE
  // ============================================
  personaDetail: {
    pageHelp: {
      title: "Understanding Your Persona",
      content: "This page shows your persona's psychological profile based on their background and experiences. Add experiences to see how their symptoms and personality evolve over time."
    },
    
    bigFive: {
      tooltip: "The Big Five personality traits that shape behavior and responses",
      whatIs: "The Big Five (OCEAN) is the most scientifically validated personality model. These traits are relatively stable but can shift with major life experiences.",
      traits: {
        openness: {
          definition: "Openness to new experiences, creativity, intellectual curiosity",
          high: "Imaginative, curious, adventurous, artistic",
          low: "Practical, conventional, prefers routine"
        },
        conscientiousness: {
          definition: "Organization, responsibility, self-discipline, goal-orientation",
          high: "Organized, reliable, hardworking, planful",
          low: "Spontaneous, flexible, casual"
        },
        extraversion: {
          definition: "Sociability, assertiveness, energy level in social situations",
          high: "Outgoing, talkative, energetic, seeks social interaction",
          low: "Reserved, quiet, prefers solitude or small groups"
        },
        agreeableness: {
          definition: "Compassion, cooperation, trust in others",
          high: "Kind, empathetic, trusting, cooperative",
          low: "Direct, skeptical, competitive, independent"
        },
        neuroticism: {
          definition: "Emotional stability, anxiety, sensitivity to stress",
          high: "Anxious, moody, sensitive to stress, worries frequently",
          low: "Calm, resilient, emotionally stable"
        }
      }
    },
    
    symptoms: {
      tooltip: "Current mental health symptoms and diagnoses based on experiences",
      whatIs: "These symptoms are generated based on the persona's background and experiences using evidence-based psychology. They follow DSM-5 diagnostic criteria.",
      howGenerated: [
        "Experiences are analyzed for trauma, neglect, loss, etc.",
        "Age at experience affects severity (earlier = greater impact)",
        "Multiple experiences compound to create complex presentations",
        "Symptoms reflect realistic clinical patterns and comorbidities"
      ],
      clickToExpand: "Click any symptom to see detailed breakdown and onset age"
    },
    
    timeline: {
      tooltip: "Visual representation of the persona's life experiences over time",
      whatIs: "The timeline shows key experiences in chronological order, helping you understand how their psychological development unfolded.",
      howToUse: [
        "Each point represents a significant experience",
        "Color indicates category (trauma, achievement, relationship, etc.)",
        "Size indicates severity of impact",
        "Click any experience to see details"
      ]
    }
  },
  
  // ============================================
  // ADD EXPERIENCE MODAL
  // ============================================
  experience: {
    pageHelp: {
      title: "Adding Life Experiences",
      content: "Experiences shape psychological development. Add specific events with ages to see how they affect symptoms, personality, and functioning over time."
    },
    
    category: {
      tooltip: "Type of experience - choose the most specific category that fits",
      categories: {
        trauma: {
          name: "Trauma",
          description: "Single traumatic events: physical/sexual abuse, assault, accidents, natural disasters, witnessing violence",
          examples: ["Car accident", "Physical assault", "Natural disaster", "Witnessing death"]
        },
        neglect: {
          name: "Neglect",
          description: "Ongoing lack of care: emotional neglect, physical neglect, abandonment, lack of supervision",
          examples: ["Emotionally unavailable parents", "Left alone frequently", "Basic needs not met", "Lack of affection"]
        },
        abuse: {
          name: "Abuse",
          description: "Ongoing abuse: repeated physical abuse, sexual abuse, emotional abuse, domestic violence exposure",
          examples: ["Repeated beatings", "Ongoing sexual abuse", "Verbal abuse", "Witnessing domestic violence"]
        },
        loss: {
          name: "Loss & Grief",
          description: "Significant losses: death of loved one, divorce, separation, pet loss, friend moving away",
          examples: ["Parent's death", "Parents' divorce", "Best friend moved away", "Pet died"]
        },
        medical: {
          name: "Medical",
          description: "Health-related events: illness, injury, hospitalization, surgery, chronic conditions",
          examples: ["Cancer diagnosis", "Serious accident", "Chronic illness", "Major surgery"]
        },
        social: {
          name: "Social",
          description: "Peer experiences: bullying, rejection, acceptance, friendship changes, social success/failure",
          examples: ["Severe bullying", "Excluded by peer group", "Made close friends", "Popular at school"]
        },
        achievement: {
          name: "Achievement",
          description: "Success and accomplishments: academic, athletic, artistic, recognition, awards",
          examples: ["Won science fair", "Made varsity team", "Accepted to gifted program", "Lead role in play"]
        },
        relationship: {
          name: "Relationship",
          description: "Significant relationships: romantic relationships starting/ending, important friendships, mentors",
          examples: ["First serious relationship", "Breakup", "Found mentor", "Betrayal by friend"]
        },
        family: {
          name: "Family Changes",
          description: "Family structure changes: new sibling, parent remarriage, moving, family member's issues",
          examples: ["Baby sibling born", "Parent remarried", "Moved cities", "Parent lost job"]
        }
      }
    },
    
    severity: {
      tooltip: "How impactful was this experience on the person's psychological well-being?",
      guide: {
        mild: {
          impact: "Minor, brief distress with full recovery",
          examples: ["Brief teasing", "Minor disappointment", "Small achievement", "Short separation from parents"],
          symptoms: "Temporary upset, returns to normal quickly"
        },
        moderate: {
          impact: "Notable impact with some lasting effects but eventual adaptation",
          examples: ["Parents' divorce", "Moving to new city", "Academic failure", "Friendship ending"],
          symptoms: "Weeks of distress, some ongoing effects, but learns to cope"
        },
        severe: {
          impact: "Major impact with significant distress and long-term effects",
          examples: ["Physical abuse", "Prolonged bullying", "Parent's serious illness", "Sexual harassment"],
          symptoms: "Months of distress, changes behavior/relationships, lasting psychological impact"
        },
        extreme: {
          impact: "Life-altering impact with profound, lasting trauma",
          examples: ["Sexual assault", "Parent's death", "Severe abuse", "Near-death experience"],
          symptoms: "Persistent trauma symptoms, fundamentally changes worldview, requires treatment"
        }
      },
      howToChoose: [
        "Consider immediate emotional impact",
        "Think about how long effects lasted",
        "Assess whether it changed their behavior/relationships",
        "When in doubt, start with 'moderate' and adjust"
      ]
    },
    
    age: {
      tooltip: "Age when this experience occurred - earlier experiences typically have greater developmental impact",
      whyItMatters: [
        "0-6 years: Critical for attachment formation, impacts trust and security",
        "7-11 years: Affects self-esteem, peer relationships, academic self-concept",
        "12-18 years: Shapes identity, romantic relationships, independence",
        "19-25 years: Influences adult role formation, intimacy, career",
        "26+: Still impactful but person has more coping resources"
      ],
      tip: "The same experience at age 5 vs age 25 creates very different psychological effects"
    },
    
    description: {
      tooltip: "Detailed description of what happened and its emotional impact",
      whatToInclude: [
        "What actually happened (specific events)",
        "Who was involved",
        "Where it occurred",
        "Immediate emotional reaction",
        "Any consequences or aftermath",
        "Whether it was one-time or repeated"
      ],
      examples: [
        {
          category: "Trauma",
          text: "Was in severe car accident with mother. Car was hit by drunk driver, mother hospitalized for 3 weeks with broken bones. Felt terrified and helpless. Started having nightmares and became afraid of cars."
        },
        {
          category: "Neglect",
          text: "Parents often forgot to pick me up from school. Would wait alone for hours, sometimes until dark. Teachers noticed and called CPS. Felt unwanted and like a burden to my parents."
        },
        {
          category: "Achievement",
          text: "Won regional science fair with project on water purification. Parents were extremely proud, teachers recognized me publicly. Felt confident and capable. This success led to interest in environmental science."
        },
        {
          category: "Social",
          text: "Group of popular girls started excluding me from lunch table and spreading rumors. This went on for entire 7th grade year. Teachers didn't intervene. Felt humiliated and isolated. Started eating lunch alone in bathroom."
        }
      ],
      tips: [
        "Be specific rather than vague",
        "Include emotional impact, not just facts",
        "Mention if it was witnessed by others or secret",
        "Note any protective factors (supportive adult, etc.)"
      ]
    }
  },
  
  // ============================================
  // ADD INTERVENTION/THERAPY MODAL
  // ============================================
  intervention: {
    pageHelp: {
      title: "Adding Therapeutic Interventions",
      content: "Track therapy, medication, or other interventions to see how they affect symptoms over time. Different modalities have different effectiveness for different conditions."
    },
    
    modality: {
      tooltip: "Type of therapy or treatment approach",
      modalities: {
        CBT: {
          name: "Cognitive Behavioral Therapy (CBT)",
          description: "Focuses on identifying and changing negative thought patterns and behaviors",
          bestFor: ["Depression", "Anxiety", "OCD", "Eating disorders", "Substance use"],
          howItWorks: "Therapist helps identify distorted thinking, test thoughts against reality, develop coping strategies",
          typicalDuration: "12-20 sessions (3-5 months)"
        },
        DBT: {
          name: "Dialectical Behavior Therapy (DBT)",
          description: "Skills-based therapy for emotion regulation, distress tolerance, interpersonal effectiveness",
          bestFor: ["Borderline Personality Disorder", "Self-harm", "Suicidal ideation", "Emotion dysregulation"],
          howItWorks: "Individual therapy + skills group, focuses on mindfulness, distress tolerance, emotion regulation, interpersonal effectiveness",
          typicalDuration: "6-12 months (weekly individual + group)"
        },
        EMDR: {
          name: "Eye Movement Desensitization & Reprocessing (EMDR)",
          description: "Trauma processing using bilateral stimulation (eye movements, tapping)",
          bestFor: ["PTSD", "Trauma", "Phobias", "Panic"],
          howItWorks: "Reprocess traumatic memories while engaging in bilateral stimulation, reduces emotional charge",
          typicalDuration: "6-12 sessions for single trauma, longer for complex trauma"
        },
        psychodynamic: {
          name: "Psychodynamic Therapy",
          description: "Explores unconscious patterns, past relationships, and how they affect present",
          bestFor: ["Relationship issues", "Personality patterns", "Depression", "Identity issues"],
          howItWorks: "Insight-oriented, explores childhood experiences and unconscious conflicts",
          typicalDuration: "Long-term (1-2+ years)"
        },
        ACT: {
          name: "Acceptance & Commitment Therapy (ACT)",
          description: "Mindfulness-based approach focused on psychological flexibility and values",
          bestFor: ["Anxiety", "Depression", "Chronic pain", "OCD"],
          howItWorks: "Accept difficult thoughts/feelings, commit to value-aligned actions, mindfulness",
          typicalDuration: "8-16 sessions"
        },
        medication: {
          name: "Medication Management",
          description: "Psychopharmacology - antidepressants, mood stabilizers, antipsychotics, etc.",
          bestFor: ["Depression", "Anxiety", "Bipolar", "Schizophrenia", "ADHD"],
          types: [
            "SSRIs (Prozac, Zoloft) - depression, anxiety",
            "SNRIs (Effexor, Cymbalta) - depression, anxiety, pain",
            "Mood stabilizers (Lithium, Depakote) - bipolar",
            "Antipsychotics (Abilify, Seroquel) - psychosis, bipolar",
            "Stimulants (Adderall, Ritalin) - ADHD",
            "Benzodiazepines (Xanax, Klonopin) - acute anxiety"
          ],
          note: "Often combined with therapy for best results"
        },
        groupTherapy: {
          name: "Group Therapy",
          description: "Therapy in group setting with shared experiences",
          bestFor: ["Substance use", "Eating disorders", "Social anxiety", "Grief"],
          howItWorks: "Process groups, psychoeducation groups, support groups",
          typicalDuration: "Ongoing or time-limited (8-12 weeks)"
        },
        familyTherapy: {
          name: "Family Therapy",
          description: "Addresses family dynamics and communication patterns",
          bestFor: ["Child/adolescent issues", "Eating disorders", "Family conflict", "Substance use"],
          howItWorks: "Involves family members, focuses on communication and system dynamics",
          typicalDuration: "8-20 sessions"
        }
      }
    },
    
    duration: {
      tooltip: "How long did this treatment last?",
      guide: [
        "Short-term: 6-12 sessions (2-3 months)",
        "Medium-term: 12-24 sessions (3-6 months)",
        "Long-term: 24+ sessions (6+ months)",
        "Ongoing: Currently in treatment"
      ],
      whyItMatters: "Longer duration generally leads to greater symptom reduction, but effectiveness varies by modality and condition"
    },
    
    effectiveness: {
      tooltip: "How helpful was this intervention for the person?",
      levels: {
        notHelpful: "0-25%: Little to no improvement, may have discontinued early",
        somewhatHelpful: "25-50%: Some improvement but symptoms still significantly impair functioning",
        moderatelyHelpful: "50-75%: Noticeable improvement, better functioning, but some symptoms remain",
        veryHelpful: "75-100%: Significant improvement, major symptom reduction, much better functioning"
      },
      factors: [
        "Therapist fit and rapport",
        "Adherence to treatment (attended regularly, did homework)",
        "Severity of symptoms at start",
        "Comorbid conditions",
        "Social support during treatment",
        "Whether modality matched the condition"
      ]
    }
  },
  
  // ============================================
  // SNAPSHOT FEATURE
  // ============================================
  snapshot: {
    tooltip: "Capture the persona's current psychological state at a specific point in time",
    whatIs: "A snapshot freezes the persona's current symptoms, functioning, and psychological presentation. Use this to track progress over time or compare before/after interventions.",
    whenToUse: [
      "Before starting a new intervention (baseline)",
      "After completing therapy (to measure change)",
      "At major life transitions",
      "To document symptom progression",
      "To compare effectiveness of different interventions"
    ],
    whatItCaptures: [
      "Current symptom levels for all diagnoses",
      "Big Five personality traits",
      "Functioning level (work, relationships, daily activities)",
      "Protective factors and strengths",
      "Current age and life stage"
    ],
    examples: [
      "Baseline snapshot at age 15 before starting CBT for depression",
      "Post-intervention snapshot at age 16 after 6 months of therapy",
      "Crisis snapshot at age 28 after traumatic event",
      "Recovery snapshot at age 30 showing progress"
    ],
    tip: "Take snapshots at key points to visualize the persona's psychological journey"
  },
  
  // ============================================
  // NARRATIVE FEATURE
  // ============================================
  narrative: {
    tooltip: "AI-generated comprehensive psychological narrative based on all experiences and background",
    whatIs: "The narrative is a professionally-written developmental psychology report that synthesizes the persona's background, experiences, and current presentation into a cohesive story.",
    whatItIncludes: [
      "Developmental history organized by life stages",
      "Analysis of attachment patterns and family dynamics",
      "Impact of trauma and adverse experiences",
      "Personality development over time",
      "Current psychological presentation and symptoms",
      "Risk and protective factors",
      "Therapeutic implications and recommendations"
    ],
    howItsGenerated: [
      "Uses all background information from persona creation",
      "Incorporates every experience with age and severity",
      "Applies evidence-based psychology principles",
      "Follows DSM-5 diagnostic criteria",
      "Written in professional clinical language"
    ],
    whenToGenerate: [
      "After adding comprehensive background information",
      "After adding multiple significant experiences",
      "When you need a comprehensive case conceptualization",
      "For educational presentations or case studies"
    ],
    tips: [
      "More detailed backstory = better narrative",
      "Add multiple experiences across life stages for richness",
      "Regenerate after adding new experiences to update",
      "Use for learning case conceptualization skills"
    ]
  },
  
  // ============================================
  // CHAT FEATURE
  // ============================================
  chat: {
    tooltip: "Have a conversation with the AI persona as if they were a real person",
    whatIs: "The chat feature lets you interact with the persona in character. They'll respond based on their background, experiences, personality traits, and current symptoms.",
    howItWorks: [
      "Persona responds as if they're a real person with this history",
      "Answers reflect their personality traits (e.g., low extraversion = brief responses)",
      "Symptoms influence conversation (e.g., depression = low energy, hopelessness)",
      "Background shapes perspectives and beliefs"
    ],
    useCases: [
      "Practice therapeutic interviewing skills",
      "Understand how symptoms manifest in conversation",
      "Explore the persona's perspective on their experiences",
      "Role-play difficult conversations",
      "Learn empathic responding"
    ],
    limitations: [
      "Not a real person - responses are AI-generated",
      "May not perfectly match a real person with this history",
      "Use for educational purposes only, not actual therapy"
    ],
    tips: [
      "Ask open-ended questions",
      "Be empathic and non-judgmental",
      "Observe how symptoms affect conversation",
      "Practice reflective listening"
    ]
  },
  
  // ============================================
  // REMIX FEATURE
  // ============================================
  remix: {
    tooltip: "Create variations of this persona to explore 'what if' scenarios",
    whatIs: "Remix lets you create a new persona based on this one, then modify specific elements to see how different experiences or interventions would change outcomes.",
    whatYouCanChange: [
      "Add or remove specific experiences",
      "Change severity of existing experiences",
      "Add different interventions",
      "Modify personality traits",
      "Change family background elements"
    ],
    useCases: [
      "Explore 'What if they had therapy earlier?'",
      "Compare 'What if abuse was reported vs unreported?'",
      "Test 'What if they had a supportive teacher?'",
      "Examine 'What if they received different treatment?'"
    ],
    examples: [
      "Original: Severe bullying, no intervention → Remix: Same bullying + school counseling",
      "Original: Neglect → Remix: Same background but removed from home at age 8",
      "Original: Depression, no treatment → Remix: Depression + CBT at age 16"
    ],
    tip: "Use remix to understand protective factors and intervention effectiveness"
  }
};

// Helper function to get help content
export function getHelp(path: string) {
  const parts = path.split('.');
  let content: any = SITE_HELP;
  
  for (const part of parts) {
    content = content?.[part];
    if (!content) return null;
  }
  
  return content;
}
