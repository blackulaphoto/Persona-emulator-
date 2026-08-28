import { auth } from '@/lib/firebase';

const API_ROOT = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
const API_BASE = API_ROOT ? `${API_ROOT}/api/v1` : '/api/v1';

export interface Persona {
  id: string;
  name: string;
  baseline_age: number;
  baseline_gender: string;
  baseline_background: string;
  current_age: number;
  current_personality: PersonalityTraits;
  current_attachment_style: string;
  current_trauma_markers: string[];
  /**
   * Fast-moving psychological state (0.0-1.0 per dimension). Reacts to a
   * single event far more readily than the Big Five does. Only contains
   * dimensions something has actually moved - an untouched dimension is
   * absent rather than sitting at an unearned baseline.
   */
  current_state?: Record<string, number> | null;
  adaptation_patterns?: AdaptationPattern[];
  clinical_pattern_hypotheses?: ClinicalPatternHypothesis[];
  experiences_count: number;
  interventions_count: number;
  created_at: string;
}

/** An earned coping/adaptation pattern, and how established it has become. */
export interface AdaptationPattern {
  adaptation_strategy: string | null;
  pattern_name: string;
  status: string; // emerging | established | weakening | resolved
  evidence_strength: number | null;
  confidence: number | null; // 0-100
  first_emerged_age: number | null;
}

/**
 * An evolving pattern-match hypothesis. NOT a diagnosis: `confidence` is how
 * strongly this persona's currently-known history matches the pattern, and it
 * moves down as well as up as more history arrives.
 */
export interface ClinicalPatternHypothesis {
  pattern_key: string;
  tier: string;
  status: string;
  evidence_strength: number | null;
  confidence: number | null; // 0-100
  direction: 'strengthening' | 'weakening' | 'stable' | null;
  opened_at_age: number | null;
  developmental_precursors: string[];
}

export interface PersonalityTraits {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

export interface Experience {
  id: string;
  persona_id: string;
  sequence_number: number;
  age_at_event: number;
  user_description: string;
  symptoms_developed: string[];
  symptom_severity: Record<string, number>;
  long_term_patterns: string[];
  recommended_therapies: string[];
}

export interface Intervention {
  id: string;
  persona_id: string;
  sequence_number: number;
  therapy_type: string;
  duration: string;
  intensity: string;
  age_at_intervention: number;
  user_notes?: string;
  actual_symptoms_targeted: string[];
  efficacy_match: number;
  symptom_changes: Record<string, number>;
  coping_skills_gained: string[];
}

export interface TimelineEvent {
  type: 'experience' | 'intervention';
  age: number;
  sequence_number: number;
  description?: string;
  therapy_type?: string;
  personality_snapshot: {
    personality_profile: PersonalityTraits;
    trauma_markers: string[];
    symptom_severity: Record<string, number>;
  };
}

export interface Timeline {
  persona: Persona;
  experiences: Experience[];
  interventions: Intervention[];
  timeline_events: TimelineEvent[];
}

class ApiClient {
  private async getAuthHeaders(): Promise<HeadersInit> {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');

    const user = auth.currentUser;
    if (!user) {
      throw new Error('Not authenticated');
    }

    const token = await user.getIdToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async createPersona(data: {
    name: string;
    baseline_age: number;
    baseline_gender: string;
    baseline_background: string;
  }): Promise<Persona> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      // Include status code in error message for persona limit detection
      throw new Error(`Failed to create persona (${response.status})`);
    }
    return response.json();
  }

  async getPersonas(): Promise<Persona[]> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas`, { headers });
    if (!response.ok) throw new Error('Failed to fetch personas');
    return response.json();
  }

  async getPersona(id: string): Promise<Persona> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${id}`, { headers });
    if (!response.ok) throw new Error('Failed to fetch persona');
    return response.json();
  }

  async addExperience(personaId: string, data: {
    user_description: string;
    age_at_event: number;
  }): Promise<Experience> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/experiences`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to add experience');
    return response.json();
  }

  async addIntervention(personaId: string, data: {
    therapy_type: string;
    duration: string;
    intensity: string;
    age_at_intervention: number;
    user_notes?: string;
  }): Promise<Intervention> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/interventions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Intervention API error:', response.status, errorText);
      throw new Error(`Failed to add intervention: ${response.status} ${errorText}`);
    }
    return response.json();
  }

  async getTimeline(personaId: string): Promise<Timeline> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/timeline`, { headers });
    if (!response.ok) throw new Error('Failed to fetch timeline');
    return response.json();
  }

  async deletePersona(id: string): Promise<void> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!response.ok) throw new Error('Failed to delete persona');
  }

  async chatWithPersona(personaId: string, message: string, conversationHistory?: ChatMessage[]): Promise<ChatResponse> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory || []
      }),
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Chat API error:', response.status, errorText);
      throw new Error(`Failed to send message: ${response.status} ${errorText}`);
    }
    return response.json();
  }
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  message: string;
  persona_state: {
    name: string;
    age: number;
    personality: PersonalityTraits;
    attachment_style: string;
    trauma_markers: string[];
  };
}

export const api = new ApiClient();
