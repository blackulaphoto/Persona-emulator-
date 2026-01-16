// Mock data for Persona Evolution application

export interface PersonalityTrait {
  name: string;
  value: number; // 0-100
  description: string;
}

export interface Symptom {
  name: string;
  severity: number; // 0-10
}

export interface LifeEvent {
  id: string;
  age: number;
  title: string;
  description: string;
  type: 'growth' | 'challenge' | 'neutral' | 'therapy';
  impact: string;
  personalityChanges?: {
    trait: string;
    before: number;
    after: number;
  }[];
  symptoms?: Symptom[];
  // Therapy-specific fields
  therapyApproach?: string; // e.g., "CBT", "DBT", "Psychodynamic"
  sessionCount?: number;
  therapyOutcomes?: {
    metric: string; // e.g., "Anxiety reduction", "Improved trust"
    improvement: number; // percentage improvement
  }[];
}

export interface Persona {
  id: string;
  name: string;
  age: number;
  gender: string;
  tagline: string;
  backgroundStory: string;
  personalityTraits: PersonalityTrait[];
  currentSymptoms: Symptom[];
  lifeEvents: LifeEvent[];
  emotionalStability: number; // 0-100
  narrative?: string;
}

// Mock personas
export const mockPersonas: Persona[] = [
  {
    id: '1',
    name: 'emma',
    age: 15,
    gender: 'female',
    tagline: 'Learning to trust again',
    backgroundStory: 'Emma grew up in a loving family until age 12, when her parents divorced. She struggled with feelings of abandonment and trust issues.',
    emotionalStability: 60,
    personalityTraits: [
      {
        name: 'Openness',
        value: 65,
        description: 'Curious about new experiences but cautious due to past trauma'
      },
      {
        name: 'Conscientiousness',
        value: 70,
        description: 'Organized and responsible, uses structure as a coping mechanism'
      },
      {
        name: 'Extraversion',
        value: 45,
        description: 'Somewhat reserved, prefers small groups of trusted friends'
      },
      {
        name: 'Agreeableness',
        value: 55,
        description: 'Wants to trust others but struggles with vulnerability'
      },
      {
        name: 'Emotional Sensitivity',
        value: 75,
        description: 'Highly attuned to emotional shifts in relationships'
      }
    ],
    currentSymptoms: [
      { name: 'Trust concerns', severity: 7 },
      { name: 'Mild anxiety', severity: 5 },
      { name: 'Attachment worries', severity: 6 }
    ],
    lifeEvents: [
      {
        id: 'e1',
        age: 8,
        title: 'A Safe Beginning',
        description: 'Emma had a stable, loving childhood with both parents present',
        type: 'growth',
        impact: 'Developed secure attachment and basic trust in relationships',
        personalityChanges: [
          { trait: 'Emotional Stability', before: 50, after: 70 }
        ]
      },
      {
        id: 'e2',
        age: 12,
        title: 'A Turning Point',
        description: 'Parents divorced after prolonged conflict. Emma felt caught in the middle.',
        type: 'challenge',
        impact: 'Developed trust issues and anxiety around relationships',
        personalityChanges: [
          { trait: 'Emotional Stability', before: 70, after: 50 },
          { trait: 'Trust', before: 80, after: 45 }
        ],
        symptoms: [
          { name: 'Anxiety', severity: 7 },
          { name: 'Trust issues', severity: 8 },
          { name: 'Hypervigilance', severity: 6 }
        ]
      },
      {
        id: 'e3',
        age: 14,
        title: 'Finding Support',
        description: 'Started therapy and joined a support group for children of divorce',
        type: 'therapy',
        impact: 'Began processing emotions and rebuilding sense of security',
        therapyApproach: 'Cognitive Behavioral Therapy (CBT)',
        sessionCount: 16,
        personalityChanges: [
          { trait: 'Emotional Stability', before: 50, after: 60 },
          { trait: 'Trust', before: 45, after: 55 }
        ],
        symptoms: [
          { name: 'Anxiety', severity: 5 },
          { name: 'Trust issues', severity: 7 }
        ],
        therapyOutcomes: [
          { metric: 'Anxiety symptoms', improvement: 29 },
          { metric: 'Trust in relationships', improvement: 22 },
          { metric: 'Emotional regulation', improvement: 35 },
          { metric: 'Sleep quality', improvement: 40 }
        ]
      }
    ],
    narrative: `Emma is a 15-year-old navigating the complex terrain of adolescence while processing significant family disruption. Her early years were marked by stability and warmth—both parents were present, attentive, and loving. This foundation gave her a secure attachment style and a baseline trust in relationships that would later be tested.

At age 12, Emma's world shifted when her parents divorced after months of escalating conflict. She found herself caught between two people she loved, each seeking her loyalty. The experience shattered her sense of security and introduced persistent anxiety about relationships. She became hypervigilant to signs of conflict and began questioning whether people she cared about would stay.

Despite these challenges, Emma has shown remarkable resilience. At 14, she began therapy and joined a support group for children of divorce. These interventions have helped her process her emotions and start rebuilding her sense of safety. She's learning that trust can be rebuilt, even after it's been broken.

Today, Emma is cautiously optimistic. She's organized and responsible—traits she uses to create structure in an uncertain world. While she's more reserved than she once was, she's slowly opening up to trusted friends. Her journey illustrates how early security can provide a foundation for healing, even after significant disruption.`
  },
  {
    id: '2',
    name: 'james',
    age: 12,
    gender: 'male',
    tagline: 'Navigating loss and instability',
    backgroundStory: 'James experienced early trauma with the death of his father at age 7. His mother later developed a substance use disorder, creating ongoing instability.',
    emotionalStability: 40,
    personalityTraits: [
      {
        name: 'Openness',
        value: 60,
        description: 'Imaginative, uses creativity as an escape'
      },
      {
        name: 'Conscientiousness',
        value: 60,
        description: 'Tries to maintain control through organization'
      },
      {
        name: 'Extraversion',
        value: 40,
        description: 'Introverted, struggles with social connections'
      },
      {
        name: 'Agreeableness',
        value: 50,
        description: 'Wants to please but guards emotions carefully'
      },
      {
        name: 'Emotional Sensitivity',
        value: 91,
        description: 'Highly sensitive to stress and emotional instability'
      }
    ],
    currentSymptoms: [
      { name: 'Generalized anxiety', severity: 9 },
      { name: 'Trust concerns', severity: 8 },
      { name: 'Hypervigilance', severity: 7 },
      { name: 'Depression symptoms', severity: 8 }
    ],
    lifeEvents: [
      {
        id: 'j1',
        age: 7,
        title: 'A Profound Loss',
        description: 'James\'s father died suddenly in a car accident',
        type: 'challenge',
        impact: 'Experienced grief, loss of security, and fear of abandonment',
        personalityChanges: [
          { trait: 'Emotional Stability', before: 70, after: 45 },
          { trait: 'Trust', before: 75, after: 55 }
        ],
        symptoms: [
          { name: 'Grief', severity: 10 },
          { name: 'Anxiety', severity: 7 },
          { name: 'Sleep disruption', severity: 8 }
        ]
      },
      {
        id: 'j2',
        age: 10,
        title: 'Stability Restored',
        description: 'Mother remarried to a supportive stepfather. James began to feel safe again.',
        type: 'growth',
        impact: 'Began healing from loss, developed new attachment',
        personalityChanges: [
          { trait: 'Emotional Stability', before: 45, after: 60 }
        ],
        symptoms: [
          { name: 'Anxiety', severity: 5 },
          { name: 'Trust issues', severity: 6 }
        ]
      },
      {
        id: 'j3',
        age: 12,
        title: 'A New Crisis',
        description: 'Mother developed a methamphetamine addiction, creating chaos at home',
        type: 'challenge',
        impact: 'Retraumatization, heightened anxiety, loss of safety',
        personalityChanges: [
          { trait: 'Emotional Stability', before: 60, after: 40 },
          { trait: 'Neuroticism', before: 70, after: 91 }
        ],
        symptoms: [
          { name: 'Anxiety', severity: 9 },
          { name: 'Trust issues', severity: 8 },
          { name: 'Hypervigilance', severity: 7 },
          { name: 'Depression', severity: 8 }
        ]
      }
    ],
    narrative: `James is a 12-year-old boy navigating a tumultuous developmental landscape shaped by significant early adversity. At age seven, James experienced a profound trauma with the sudden death of his father in a car accident. This event precipitated a cascade of challenges, as his already struggling mother was thrust into deeper financial hardship. Despite these considerable challenges, James initially developed a secure attachment style, likely rooted in the stability and care he received during his early years, before his father's death.

However, his environment transformed dramatically, and his mother's subsequent methamphetamine addiction, which emerged when James was 12, has introduced a new layer of instability and emotional neglect. James' psychological profile is marked by high emotional sensitivity, indicating a predisposition to experience negative emotions such as anxiety and depression. His low extraversion and agreeableness suggest a tendency toward introversion and potential difficulties in social interactions, possibly exacerbated by his experiences of loss and instability.

This combination of traits and experiences has fostered trust issues, hypervigilance, and generalized anxiety, making it challenging for James to navigate social and academic environments. Understanding James requires a trauma-informed perspective that acknowledges the profound impact his early experiences have had on his current psychological state and ongoing development.`
  }
];

// Helper function to get persona by ID
export function getPersonaById(id: string): Persona | undefined {
  return mockPersonas.find(p => p.id === id);
}

// Helper function to get all personas
export function getAllPersonas(): Persona[] {
  return mockPersonas;
}

// Helper function to get event type color
export function getEventTypeColor(type: 'growth' | 'challenge' | 'neutral'): string {
  switch (type) {
    case 'growth':
      return 'var(--sage-green)';
    case 'challenge':
      return 'var(--muted-coral)';
    case 'neutral':
      return 'var(--periwinkle)';
  }
}

// Helper function to get event type label
export function getEventTypeLabel(type: 'growth' | 'challenge' | 'neutral' | 'therapy'): string {
  switch (type) {
    case 'growth':
      return 'Growth';
    case 'challenge':
      return 'Challenge';
    case 'therapy':
      return 'Therapy';
    case 'neutral':
      return 'Turning Point';
  }
}
