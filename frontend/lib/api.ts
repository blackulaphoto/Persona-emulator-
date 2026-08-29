import { getAuthHeaders } from '@/lib/authHeaders';

const API_ROOT = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
const API_BASE = API_ROOT ? `${API_ROOT}/api/v1` : '/api/v1';

export interface Persona {
  id: string;
  name: string;
  baseline_age: number;
  baseline_gender: string;
  baseline_background: string;
  baseline_personality?: PersonalityTraits | null;
  current_age: number;
  current_personality: PersonalityTraits;
  current_attachment_style: string;
  baseline_attachment_style?: string;
  baseline_attachment_dimensions?: AttachmentDimensions;
  current_attachment_dimensions?: AttachmentDimensions;
  attachment_delta?: AttachmentDimensions;
  attachment_style_semantics?: 'derived_from_developmental_dimensions';
  personality_delta?: Partial<PersonalityTraits> | null;
  foundational_environment_signals?: Record<string, unknown>;
  narrative_mode?: 'case_subject' | 'self_authored';
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

export interface AttachmentDimensions {
  attachment_anxiety: number;
  attachment_avoidance: number;
  relational_security: number;
}

/** One entry in an AdaptationPattern's reinforcement_history: what happened, when. */
export interface PatternReinforcementEvent {
  experience_id?: string;
  age?: number;
  effect?: string; // created | reinforced | weakened
  [key: string]: unknown;
}

/** An earned coping/adaptation pattern, and how established it has become. */
export interface AdaptationPattern {
  adaptation_strategy: string | null;
  pattern_name: string;
  status: string; // emerging | established | weakening | resolved
  evidence_strength: number | null;
  confidence: number | null; // 0-100
  first_emerged_age: number | null;
  reinforcement_history: PatternReinforcementEvent[];
}

/** One piece of evidence for/against a clinical pattern hypothesis. */
export interface HypothesisEvidenceEntry {
  source_id?: string;
  experience_id?: string;
  age?: number;
  type?: string;
  description?: string;
  [key: string]: unknown;
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
  supporting_evidence: HypothesisEvidenceEntry[];
  contradicting_evidence: HypothesisEvidenceEntry[];
  evidence_count: number;
}

export interface PersonalityTraits {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

/**
 * One proposed state/trait implication value. The AI-success path proposes
 * a plain numeric delta; state_trait_engine's heuristic fallback proposes
 * {direction, magnitude} instead - both are real, so this stays a union
 * rather than a false Record<string, number>.
 */
export type StateTraitImplication = number | { direction: string; magnitude: string };

/** The engine's own interpretation of one experience — belief formed, adaptation strategy, reasoning. */
export interface InterpretationResponse {
  id: string;
  source_event_id?: string | null;
  belief_statement: string | null;
  adaptation_strategy: string | null;
  reasoning: string | null;
  state_implications: Record<string, StateTraitImplication> | null;
  trait_implications: Record<string, StateTraitImplication> | null;
}

/** How one experience connected to an adaptation pattern (created it, reinforced it, weakened it). */
export interface ExperiencePatternLink {
  pattern_id: string;
  pattern_name: string;
  adaptation_strategy: string | null;
  effect: string;
  age: number | null;
  current_status: string;
  current_evidence_strength: number | null;
}

/** How one experience connected to a clinical pattern hypothesis (supporting or contradicting). */
export interface ExperienceHypothesisLink {
  hypothesis_id: string;
  pattern_key: string;
  evidence_role: 'supporting' | 'contradicting' | string;
  evidence: HypothesisEvidenceEntry[];
  current_strength: number | null;
  direction: 'strengthening' | 'weakening' | 'stable' | null;
  evidence_count: number;
}

export interface Experience {
  id: string;
  persona_id: string;
  sequence_number: number;
  sequence_index: number;
  age_at_event: number;
  user_description: string;
  immediate_effects?: Record<string, unknown> | null;
  symptoms_developed: string[];
  symptom_severity: Record<string, number>;
  long_term_patterns: string[];
  worldview_shifts?: Record<string, number> | null;
  cross_experience_triggers?: string[] | null;
  recommended_therapies: string[];
  interpretation: InterpretationResponse | null;
  pattern_connections: ExperiencePatternLink[];
  hypothesis_connections: ExperienceHypothesisLink[];
  protective_factors: ProtectiveFactor[];
  created_at: string;
}

export interface ProtectiveFactor {
  id: string;
  factor_type: string;
  description?: string | null;
  domains_buffered: string[];
  source_event_id?: string | null;
  active_from_age?: number | null;
  active_to_age?: number | null;
  speaker_role: string;
}

export interface Intervention {
  id: string;
  persona_id: string;
  sequence_number: number;
  therapy_type: string;
  duration: string;
  intensity: string;
  age_at_intervention: number;
  user_notes?: string | null;
  actual_symptoms_targeted: string[] | null;
  efficacy_match: number | null;
  immediate_effects: Record<string, unknown> | null;
  /**
   * Backend types this Optional[Dict] (see schemas/__init__.py), but the
   * route builds the response by hand rather than through strict model
   * validation, so what actually comes back is whatever shape the AI
   * produced - observed in practice as a plain string list ("Reduction in
   * negative thought patterns...") rather than a dict. Kept a union rather
   * than trusting the backend's own (inaccurate) type hint - render
   * defensively on both shapes.
   */
  sustained_effects: string[] | Record<string, unknown> | null;
  limitations: string[] | null;
  /**
   * Backend types this Dict[str, int], but the real shape observed is
   * {before: Record<string, number>, after: Record<string, number>,
   * percentage_improvement: Record<string, number>} - a genuine real
   * Before/After the Therapy Detail view should show, not a flat map.
   */
  symptom_changes: { before: Record<string, number>; after: Record<string, number>; percentage_improvement?: Record<string, number> } | Record<string, number> | null;
  /**
   * Despite the name, this observed in practice as the resulting absolute
   * Big Five snapshot (matching current_personality exactly), not a delta -
   * do not render with a "+"/"-" sign implying directional change.
   */
  personality_changes: Record<string, number> | null;
  /** What was proposed for this intervention. Trait movement is gated (see intervention_trait_gate_open) - this is the proposal, not necessarily what was applied; personality_changes reflects what was actually applied. */
  state_implications: Record<string, StateTraitImplication> | null;
  trait_implications: Record<string, StateTraitImplication> | null;
  coping_skills_gained: string[];
  created_at: string;
}

export interface TimelineEvent {
  type: 'experience' | 'intervention';
  age: number;
  sequence_number: number;
  sequence_index?: number;
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
  async createPersona(data: {
    name: string;
    baseline_age: number;
    baseline_gender: string;
    baseline_background: string;
  }): Promise<Persona> {
    const headers = await getAuthHeaders();
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
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas`, { headers });
    if (!response.ok) throw new Error('Failed to fetch personas');
    return response.json();
  }

  async getPersona(id: string): Promise<Persona> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${id}`, { headers });
    if (!response.ok) throw new Error('Failed to fetch persona');
    return response.json();
  }

  async updatePersona(id: string, data: {
    name?: string;
    baseline_background?: string;
  }): Promise<Persona> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${id}`, {
      method: 'PUT', headers, body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update persona');
    return response.json();
  }

  async addExperience(personaId: string, data: {
    user_description: string;
    age_at_event: number;
  }): Promise<Experience> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/experiences`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to add experience');
    return response.json();
  }

  async addExperiencesBatch(personaId: string, experiences: Array<{
    description: string;
    age_at_event: number;
  }>): Promise<{
    results: Array<{ input_index: number; status: 'processed' | 'failed'; result?: Experience; error?: string }>;
    processed_count: number;
    failed_count: number;
  }> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/experiences/batch`, {
      method: 'POST', headers, body: JSON.stringify({ experiences }),
    });
    if (!response.ok) throw new Error('Failed to add experience batch');
    return response.json();
  }

  /**
   * Edit an experience and deterministically replay the persona's derived
   * trajectory forward from it. Returns the whole rebuilt Persona (not the
   * single experience) - that's what the real PATCH endpoint returns.
   */
  async updateExperience(personaId: string, experienceId: string, data: {
    user_description?: string;
    age_at_event?: number;
    sequence_index?: number;
  }): Promise<Persona> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/experiences/${experienceId}`, {
      method: 'PATCH', headers, body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`Failed to update experience (${response.status})`);
    return response.json();
  }

  /** Delete an experience and rebuild the persona's trajectory from what remains. */
  async deleteExperience(personaId: string, experienceId: string): Promise<Persona> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/experiences/${experienceId}`, {
      method: 'DELETE', headers,
    });
    if (!response.ok) throw new Error(`Failed to delete experience (${response.status})`);
    return response.json();
  }

  async addIntervention(personaId: string, data: {
    therapy_type: string;
    duration: string;
    intensity: string;
    age_at_intervention: number;
    user_notes?: string;
  }): Promise<Intervention> {
    const headers = await getAuthHeaders();
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
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${personaId}/timeline`, { headers });
    if (!response.ok) throw new Error('Failed to fetch timeline');
    return response.json();
  }

  async deletePersona(id: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/personas/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!response.ok) throw new Error('Failed to delete persona');
  }

  async chatWithPersona(personaId: string, message: string, conversationHistory?: ChatMessage[]): Promise<ChatResponse> {
    const headers = await getAuthHeaders();
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

  async generateNarrative(personaId: string): Promise<Narrative> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/narratives/personas/${personaId}/generate`, {
      method: 'POST', headers,
    });
    if (!response.ok) throw new Error(`Failed to generate narrative (${response.status})`);
    return response.json();
  }

  async listNarratives(personaId: string, limit = 10): Promise<Narrative[]> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/narratives/personas/${personaId}?limit=${limit}`, { headers });
    if (!response.ok) throw new Error(`Failed to fetch narratives (${response.status})`);
    return response.json();
  }

  async getNarrative(narrativeId: string): Promise<Narrative> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/narratives/${narrativeId}`, { headers });
    if (!response.ok) throw new Error(`Failed to fetch narrative (${response.status})`);
    return response.json();
  }

  async deleteNarrative(narrativeId: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/narratives/${narrativeId}`, { method: 'DELETE', headers });
    if (!response.ok) throw new Error(`Failed to delete narrative (${response.status})`);
  }

  async submitFeedback(message: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/feedback`, {
      method: 'POST', headers, body: JSON.stringify({ message }),
    });
    if (!response.ok) throw new Error(`Failed to submit feedback (${response.status})`);
  }
}

/** A generated narrative (executive_summary/developmental_timeline/current_presentation/treatment_response/prognosis are separate GPT-authored sections, not free text split client-side). */
export interface Narrative {
  id: string;
  persona_id: string;
  generated_at: string;
  generation_number: number;
  persona_age_at_generation: number;
  total_experiences_count: number;
  total_interventions_count: number;
  executive_summary: string;
  developmental_timeline: string;
  current_presentation: string;
  treatment_response: string | null;
  prognosis: string;
  full_narrative: string;
  word_count: number;
  generation_time_seconds: number | null;
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
