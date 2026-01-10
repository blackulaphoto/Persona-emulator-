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
    whatIs: "Experiences are the building blocks of psychological development. Each experience affects symptoms, personality traits, and functioning based on its type, severity, and age of occurrence."
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
    whatIs: "Interventions represent therapeutic treatments that can reduce symptoms and improve functioning. The effectiveness depends on the modality, duration, and match to symptoms."
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
