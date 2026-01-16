/**
 * SITE-WIDE HELP CONTENT
 *
 * Empathetic Modernism Voice:
 * - Human, not clinical
 * - Exploratory, not diagnostic
 * - Inviting, not overwhelming
 */

export const SITE_HELP = {
  // ============================================
  // PERSONA DETAIL PAGE
  // ============================================
  personaDetail: {
    pageHelp: {
      title: "Exploring This Person's Journey",
      content: "Here you can see how this person tends to think, feel, and respond to the world. As you add experiences, you'll watch their story unfold—see how moments shape who they become."
    },

    bigFive: {
      tooltip: "How this person tends to think, feel, and respond",
      whatIs: "The Big Five describes how people approach life. These tendencies are fairly stable, but can shift through major experiences and growth.",
      traits: {
        openness: {
          definition: "How curious and imaginative they tend to be",
          high: "Loves exploring ideas, trying new things, creating",
          low: "Prefers what's familiar, practical, and predictable"
        },
        conscientiousness: {
          definition: "How organized and goal-focused they tend to be",
          high: "Keeps things in order, follows through, plans ahead",
          low: "Goes with the flow, flexible about plans and details"
        },
        extraversion: {
          definition: "Where they get their energy—from people or from solitude",
          high: "Energized by being around others, outgoing",
          low: "Recharged by quiet time, keeps a smaller circle"
        },
        agreeableness: {
          definition: "How they tend to relate to and trust others",
          high: "Warm, empathetic, wants harmony in relationships",
          low: "Direct, independent, questions before trusting"
        },
        neuroticism: {
          definition: "How they experience and manage emotions",
          high: "Feels things deeply, sensitive to stress and worry",
          low: "Stays steady through ups and downs, less reactive"
        }
      }
    },

    symptoms: {
      tooltip: "What they're navigating right now",
      whatIs: "Based on what this person has been through, here's what they might be dealing with emotionally and mentally. This reflects realistic patterns you'd see in real life.",
      howGenerated: [
        "We look at what happened to them and when",
        "Earlier experiences shape us more deeply",
        "Multiple challenges can build on each other",
        "The patterns mirror what clinicians see in real cases"
      ],
      clickToExpand: "Click any symptom to understand when it started and why"
    },

    timeline: {
      tooltip: "See how their life story has unfolded",
      whatIs: "This timeline shows the moments that shaped them. You can trace how experiences led to who they are now.",
      howToUse: [
        "Each point is a significant moment in their life",
        "Colors show different types of experiences",
        "Bigger moments had more impact",
        "Click any experience to explore it deeper"
      ]
    }
  },

  // ============================================
  // ADD EXPERIENCE MODAL
  // ============================================
  experience: {
    pageHelp: {
      title: "Adding Moments That Matter",
      content: "Life experiences shape us. Add specific moments—with context about when and how they happened—and see how they influence this person's journey."
    },
    tooltip: "Add a moment that shaped this person's path",
    whatIs: "Experiences are how we become who we are. Each one affects how someone sees themselves, relates to others, and moves through the world.",
    age: {
      tooltip: "When something happens matters—earlier experiences shape us more deeply."
    },
    description: {
      tooltip: "Tell the story: What happened? How long did it last? How did it feel?"
    }
  },

  // ============================================
  // ADD INTERVENTION/THERAPY MODAL
  // ============================================
  intervention: {
    pageHelp: {
      title: "Exploring Support and Healing",
      content: "Track therapy or other support to see how it helps. Different approaches work better for different challenges."
    },
    tooltip: "Add therapy or support to see how it helps",
    whatIs: "Support comes in many forms—therapy, medication, community. Here you can explore how different kinds of help affect this person's wellbeing over time.",
    modalityPicker: {
      tooltip: "Different therapy approaches work better for different challenges",
      whatIs: "There are many ways to approach healing. Some focus on changing thoughts, others on processing trauma, others on building skills. The best fit depends on what someone's dealing with."
    },
    duration: {
      tooltip: "Therapy takes time. Longer engagement often means deeper change."
    },
    age: {
      tooltip: "When someone gets support matters, especially for earlier wounds"
    }
  },

  // ============================================
  // NARRATIVE VIEW
  // ============================================
  narrative: {
    pageHelp: {
      title: "Their Story So Far",
      content: "This is their life as a narrative—not a list of symptoms, but a story of how experiences shaped a person."
    },
    tooltip: "See how their story unfolds",
    whatIs: "The narrative weaves together everything you know about this person into a coherent story. It helps you understand them holistically, not just diagnostically.",
    howGenerated: "We look at their background, what they've been through, and how it all connects into who they've become.",
    readingTime: "Take your time with this. These are real human complexities."
  },

  // ============================================
  // PERSONAS LIST PAGE
  // ============================================
  personasList: {
    pageHelp: {
      title: "Welcome to Your Collection",
      content: "Each persona represents a unique psychological journey. Create new ones to explore different life paths, or continue developing existing stories."
    },
    emptyState: {
      title: "Start Exploring Human Development",
      subtitle: "Create your first persona to see how experiences shape personality, symptoms, and growth over time.",
      steps: [
        {
          title: "Create a Person",
          description: "Start with basics—name, age, and their early life context"
        },
        {
          title: "Add Experiences",
          description: "Build their story with moments that shaped who they became"
        },
        {
          title: "Explore Their Timeline",
          description: "See how personality and wellbeing evolved across their life"
        },
        {
          title: "Understand the Pattern",
          description: "Watch how early experiences, relationships, and support interweave"
        }
      ]
    },
    personaCard: {
      age: "How old they are right now",
      experiences: "Moments that have shaped their journey",
      symptoms: "What they're currently navigating"
    }
  },

  // ============================================
  // CREATE PERSONA PAGE
  // ============================================
  createPersona: {
    pageHelp: {
      title: "Creating a New Person",
      content: "You're about to shape a life story. Start with who they are and what their early years were like—this sets the foundation for everything that follows."
    },
    backgroundStory: {
      tooltip: "Describe their early life—family, environment, formative experiences",
      whatIs: "Early life sets the stage. Family dynamics, stability, early relationships—these shape the lens through which someone sees the world.",
      examples: [
        "Raised by a single parent who worked two jobs",
        "Grew up in a chaotic household with addiction issues",
        "Had a stable, supportive family in a tight-knit community",
        "Moved frequently, struggled to form lasting friendships"
      ]
    },
    initialPersonality: {
      tooltip: "How would you describe their natural temperament?",
      whatIs: "Some of who we are is there from the start. Think of this as their baseline—before life experiences shape them further."
    }
  },

  // ============================================
  // TEMPLATES PAGE
  // ============================================
  templates: {
    pageHelp: {
      title: "Explore Real Psychological Patterns",
      content: "These templates represent real clinical presentations and developmental trajectories. Use them to learn, teach, or as starting points for your own explorations."
    },
    whatAreTemplates: "Templates are pre-built personas based on real psychological patterns—complex trauma, developmental journeys, treatment response examples.",
    howToUse: [
      "Browse patterns you want to understand better",
      "Use as teaching examples for students or colleagues",
      "Start from a template and modify to explore 'what ifs'",
      "Compare how different interventions affect similar starting points"
    ]
  },

  // ============================================
  // SNAPSHOT FEATURE
  // ============================================
  snapshot: {
    tooltip: "Capture who they are at this moment in time",
    whatIs: "Snapshots freeze a moment in their development. Later, you can compare snapshots to see how they've changed—what's shifted, what's grown, what's healed.",
    whyUseful: "Growth isn't always obvious day-to-day. Snapshots let you step back and see the journey.",
    howToUse: "Save snapshots at key moments—before major life changes, before/after therapy, at different life stages."
  },

  // ============================================
  // REMIX FEATURE
  // ============================================
  remix: {
    tooltip: "Explore an alternate path for this person's story",
    whatIs: "Remix creates a new version of this persona so you can explore 'what if' scenarios. What if they'd gotten support earlier? What if a key experience had been different?",
    useCases: [
      "See how earlier intervention changes outcomes",
      "Explore how one changed experience ripples forward",
      "Compare different therapy approaches",
      "Understand protective vs. risk factors by toggling them"
    ]
  }
}
