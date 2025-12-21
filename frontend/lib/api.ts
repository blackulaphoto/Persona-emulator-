import { auth } from '@/lib/firebase';

const API_ROOT = process.env.NEXT_PUBLIC_API_URL;
if (!API_ROOT) {
  throw new Error('NEXT_PUBLIC_API_URL is not configured. Set it to your backend URL.');
}
const API_BASE = `${API_ROOT}/api/v1`;

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
  experiences_count: number;
  interventions_count: number;
  created_at: string;
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
    if (!response.ok) throw new Error('Failed to create persona');
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
