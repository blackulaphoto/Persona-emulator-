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
    tooltip: "Add a life experience that shaped this persona's development",
    whatIs: "Experiences are the building blocks of psychological development. Each experience affects symptoms, personality traits, and functioning based on its type, severity, and age of occurrence.",
    age: {
      tooltip: "Earlier experiences tend to have greater developmental impact, especially in childhood."
    },
    description: {
      tooltip: "Include context, duration, and emotional impact for the most accurate analysis."
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
    tooltip: "Add therapy or treatment to track symptom changes",
    whatIs: "Interventions represent therapeutic treatments that can reduce symptoms and improve functioning. The effectiveness depends on the modality, duration, and match to symptoms.",
    age: {
      tooltip: "Age at intervention affects developmental sensitivity and expected outcomes."
    },
    therapyType: {
      tooltip: "Different therapy modalities target different symptom clusters and goals."
    },
    duration: {
      tooltip: "Longer durations typically increase effectiveness, especially for chronic symptoms."
    },
    intensity: {
      tooltip: "Session frequency influences speed and stability of change."
    },
    notes: {
      tooltip: "Add relevant context such as treatment goals or special considerations."
    }
  },

  // ============================================
  // SNAPSHOT FEATURE
  // ============================================
  snapshot: {
    tooltip: "Capture the persona's current psychological state at a specific point in time",
    whatIs: "A snapshot freezes the persona's current symptoms, functioning, and psychological presentation. Use this to track progress over time or compare before/after interventions.",
    create: {
      labelTooltip: "Use a short label to describe the milestone or period you are capturing.",
      descriptionTooltip: "Optional context for why this snapshot matters or what changed."
    },
    whenToUse: [
      "Before starting a new intervention (baseline)",
      "After completing therapy (to measure change)",
      "At major life transitions",
      "To document symptom progression",
      "To compare effectiveness of different interventions"
    ]
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
    ]
  },

  // ============================================
  // CLINICAL TEMPLATES PAGE
  // ============================================
  templates: {
    pageHelp: {
      title: "Clinical Templates",
      content: "Browse evidence-based disorder development pathways. Templates provide pre-configured personas with realistic symptom progressions based on clinical research."
    },

    whatAreTemplates: {
      tooltip: "Pre-built persona configurations based on common clinical presentations",
      whatIs: "Clinical templates are evidence-based disorder development pathways that simulate realistic psychological presentations. Each template includes a baseline profile and predefined experiences that lead to specific diagnoses.",
      howTheyWork: [
        "Each template represents a common clinical presentation",
        "Background and experiences are based on research and clinical patterns",
        "Symptoms develop realistically based on developmental psychology",
        "You can apply all experiences at once or manually add them",
        "Templates can be customized after creation"
      ]
    },

    templateBrowser: {
      tooltip: "Browse templates by disorder category or severity",
      categories: {
        mood: "Depression, Bipolar Disorder, Dysthymia",
        anxiety: "Generalized Anxiety, Panic Disorder, Social Anxiety, OCD, PTSD",
        trauma: "PTSD, Complex PTSD, Developmental Trauma",
        personality: "Borderline, Avoidant, Narcissistic Personality Disorders",
        psychotic: "Schizophrenia, Schizoaffective Disorder",
        developmental: "ADHD, Autism Spectrum Disorder",
        substance: "Substance Use Disorders, Co-occurring Disorders"
      }
    },

    createFromTemplate: {
      tooltip: "Create a new persona with this template's baseline configuration",
      whatHappens: [
        "A new persona is created with the template's background",
        "Baseline personality traits and demographics are set",
        "Predefined experiences are available to apply",
        "You choose whether to apply all experiences or add manually",
        "Once created, you can customize the persona further"
      ]
    },

    applyExperiences: {
      tooltip: "Apply the template's predefined experiences to see symptom development",
      whatIs: "Templates come with carefully designed experiences that lead to the target diagnosis. You can apply them all at once or review and add them individually.",
      whenToApplyAll: [
        "When you want to quickly create a realistic case example",
        "For educational demonstrations",
        "When studying typical disorder development pathways"
      ],
      whenToApplyManually: [
        "When you want to understand each experience's impact",
        "To customize the timeline or severity",
        "For learning case conceptualization step-by-step"
      ]
    },

    vsCreatePersona: {
      tooltip: "Templates vs. creating from scratch",
      templates: "Quick start with evidence-based presentation, ideal for education and research",
      createNew: "Full control over all aspects, ideal for specific cases or creative exploration",
      whenToUseTemplates: [
        "Learning about disorder development pathways",
        "Need a realistic example quickly",
        "Teaching or demonstrating clinical concepts",
        "Studying typical symptom progressions"
      ],
      whenToCreateNew: [
        "Simulating a specific client case (de-identified)",
        "Exploring unique combinations of experiences",
        "Testing hypotheses about protective/risk factors",
        "Creating personalized educational scenarios"
      ]
    }
  },

  // ============================================
  // PERSONAS LIST / HOME PAGE
  // ============================================
  personasList: {
    pageHelp: {
      title: "Your Personas",
      content: "Manage your collection of psychological personas. Create new personas from scratch, use clinical templates, or remix existing ones to explore different developmental pathways."
    },

    emptyState: {
      title: "No personas yet",
      description: "Get started by creating a persona, using a clinical template, or exploring the remix feature.",
      helpItems: [
        "Create Custom: Build a persona from scratch with full control",
        "Use Template: Start with evidence-based disorder presentations",
        "Remix: Create variations of existing personas to explore 'what if' scenarios"
      ]
    },

    createPersona: {
      tooltip: "Create a new persona from scratch with complete customization",
      whatIs: "Build a persona by defining their background, demographics, and initial state. Then add experiences and interventions to see how they evolve.",
      bestFor: [
        "Simulating specific client cases (de-identified)",
        "Custom learning scenarios",
        "Exploring unique developmental pathways",
        "Research and hypothesis testing"
      ]
    },

    useTemplate: {
      tooltip: "Start with a pre-configured clinical template",
      whatIs: "Templates provide evidence-based disorder development pathways with realistic symptom progressions. Quick way to create educational examples.",
      bestFor: [
        "Learning disorder development patterns",
        "Teaching clinical concepts",
        "Quick demonstrations",
        "Studying typical presentations"
      ]
    },

    remixPersona: {
      tooltip: "Create variations of existing personas to explore different outcomes",
      whatIs: "Remix lets you duplicate a persona and modify specific elements to answer 'what if' questions about different experiences or interventions.",
      examples: [
        "What if they had received therapy earlier?",
        "What if the trauma had been reported?",
        "What if they had a supportive teacher?",
        "How would different parenting have changed outcomes?"
      ],
      bestFor: [
        "Understanding protective vs. risk factors",
        "Comparing intervention effectiveness",
        "Teaching clinical decision-making",
        "Research on developmental trajectories"
      ]
    },

    personaCard: {
      age: "Current age in the simulation",
      experiences: "Number of life experiences added",
      symptoms: "Number of active symptoms/diagnoses",
      lastUpdated: "Last time the persona was modified"
    }
  },

  // ============================================
  // REMIX FEATURE
  // ============================================
  remix: {
    tooltip: "Create variations of this persona to explore 'what if' scenarios",
    whatIs: "Remix lets you create a new persona based on this one, then modify specific elements to see how different experiences or interventions would change outcomes.",
    pageHelp: {
      title: "Remix a Persona",
      content: "Create a variation of an existing persona to explore alternative developmental pathways and intervention outcomes."
    },
    whatYouCanChange: [
      "Add or remove specific experiences",
      "Change severity of existing experiences",
      "Add different interventions",
      "Modify timing of events",
      "Adjust baseline traits"
    ],
    useCases: [
      "Explore 'What if they had therapy earlier?'",
      "Compare 'What if abuse was reported vs unreported?'",
      "Test 'What if they had a supportive teacher?'",
      "Examine 'What if they received different treatment?'"
    ]
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
