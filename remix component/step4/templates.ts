/**
 * API Client for Clinical Templates & Remix
 * 
 * Handles all communication with backend for:
 * - Template browsing and details
 * - Persona creation from templates
 * - Experience/intervention application
 * - Timeline snapshots and comparisons
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Error handling helper
class APIError extends Error {
  constructor(message: string, public status: number, public data?: any) {
    super(message);
    this.name = 'APIError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(
      error.detail || `HTTP ${response.status}`,
      response.status,
      error
    );
  }
  return response.json();
}

// ============================================================================
// TEMPLATE API
// ============================================================================

export interface Template {
  id: string;
  name: string;
  disorder_type: string;
  description: string;
  baseline_age: number;
  experience_count: number;
  intervention_count: number;
  remix_suggestion_count: number;
}

export interface TemplateDetails extends Template {
  clinical_rationale: string;
  baseline_gender?: string;
  baseline_background: string;
  baseline_personality: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
  };
  baseline_attachment_style: string;
  predefined_experiences: Array<{
    age: number;
    category: string;
    valence: string;
    intensity: string;
    description: string;
    clinical_note?: string;
  }>;
  predefined_interventions?: Array<{
    age: number;
    therapy_type: string;
    duration: string;
    intensity: string;
    rationale: string;
  }>;
  expected_outcomes: Record<string, any>;
  citations?: string[];
  remix_suggestions?: Array<{
    title: string;
    changes: string[];
    hypothesis: string;
  }>;
  created_at: string;
  updated_at: string;
}

export const templatesAPI = {
  /**
   * List all available templates
   */
  async list(disorderType?: string): Promise<Template[]> {
    const params = disorderType ? `?disorder_type=${disorderType}` : '';
    const response = await fetch(`${API_BASE_URL}/api/v1/templates${params}`);
    return handleResponse<Template[]>(response);
  },

  /**
   * Get template details by ID
   */
  async get(templateId: string): Promise<TemplateDetails> {
    const response = await fetch(`${API_BASE_URL}/api/v1/templates/${templateId}`);
    return handleResponse<TemplateDetails>(response);
  },

  /**
   * Get list of disorder types
   */
  async getDisorderTypes(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/templates/meta/disorder-types`);
    return handleResponse<string[]>(response);
  },

  /**
   * Create persona from template
   */
  async createPersona(templateId: string, customName?: string): Promise<{
    persona_id: string;
    template_id: string;
    template_name: string;
    persona_name: string;
    baseline_age: number;
    baseline_personality: Record<string, number>;
    predefined_experiences_available: number;
    suggested_interventions_available: number;
    message: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/templates/create-persona`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        template_id: templateId,
        custom_name: customName,
      }),
    });
    return handleResponse(response);
  },

  /**
   * Apply predefined experiences from template
   */
  async applyExperiences(
    personaId: string,
    templateId: string,
    experienceIndices?: number[]
  ): Promise<{
    persona_id: string;
    experiences_applied: number;
    experience_ids: string[];
    personality_before: Record<string, number>;
    personality_after: Record<string, number>;
    symptoms_developed: string[];
    current_age: number;
  }> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/templates/personas/${personaId}/apply-experiences`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: templateId,
          experience_indices: experienceIndices,
        }),
      }
    );
    return handleResponse(response);
  },
};

// ============================================================================
// REMIX API
// ============================================================================

export interface TimelineSnapshot {
  id: string;
  persona_id: string;
  template_id?: string;
  label: string;
  description?: string;
  modified_experiences: Array<any>;
  modified_interventions?: Array<any>;
  personality_snapshot: Record<string, number>;
  trauma_markers_snapshot?: string[];
  symptom_severity_snapshot?: Record<string, number>;
  personality_difference?: Record<string, number>;
  symptom_difference?: Record<string, number>;
  created_at: string;
}

export interface SnapshotComparison {
  snapshot_1: {
    id: string;
    label: string;
    personality: Record<string, number>;
    symptoms: string[];
    symptom_severity: Record<string, number>;
  };
  snapshot_2: {
    id: string;
    label: string;
    personality: Record<string, number>;
    symptoms: string[];
    symptom_severity: Record<string, number>;
  };
  personality_differences: Record<string, {
    snapshot_1: number;
    snapshot_2: number;
    difference: number;
    change_direction: string;
  }>;
  symptom_differences: {
    only_in_snapshot_1: string[];
    only_in_snapshot_2: string[];
    in_both: string[];
  };
  symptom_severity_differences: Record<string, {
    snapshot_1: number;
    snapshot_2: number;
    difference: number;
  }>;
  summary: string;
}

export const remixAPI = {
  /**
   * Create timeline snapshot
   */
  async createSnapshot(
    personaId: string,
    label: string,
    description?: string,
    templateId?: string
  ): Promise<TimelineSnapshot> {
    const response = await fetch(`${API_BASE_URL}/api/v1/remix/snapshots`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona_id: personaId,
        label,
        description,
        template_id: templateId,
        modifications: [],
      }),
    });
    return handleResponse<TimelineSnapshot>(response);
  },

  /**
   * List snapshots for persona
   */
  async listSnapshots(personaId: string): Promise<TimelineSnapshot[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/remix/personas/${personaId}/snapshots`
    );
    return handleResponse<TimelineSnapshot[]>(response);
  },

  /**
   * Get snapshot details
   */
  async getSnapshot(snapshotId: string): Promise<TimelineSnapshot> {
    const response = await fetch(`${API_BASE_URL}/api/v1/remix/snapshots/${snapshotId}`);
    return handleResponse<TimelineSnapshot>(response);
  },

  /**
   * Compare two snapshots
   */
  async compareSnapshots(
    snapshotId1: string,
    snapshotId2: string
  ): Promise<SnapshotComparison> {
    const response = await fetch(`${API_BASE_URL}/api/v1/remix/snapshots/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        snapshot_id_1: snapshotId1,
        snapshot_id_2: snapshotId2,
      }),
    });
    return handleResponse<SnapshotComparison>(response);
  },

  /**
   * Get intervention impact analysis
   */
  async getInterventionImpact(personaId: string, baselineSnapshotId: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/remix/personas/${personaId}/intervention-impact?baseline_snapshot_id=${baselineSnapshotId}`
    );
    return handleResponse(response);
  },

  /**
   * Get remix suggestions
   */
  async getSuggestions(personaId: string, templateId?: string): Promise<{
    suggestions: Array<{
      title: string;
      changes: string[];
      hypothesis: string;
    }>;
  }> {
    const params = templateId ? `?template_id=${templateId}` : '';
    const response = await fetch(
      `${API_BASE_URL}/api/v1/remix/personas/${personaId}/suggestions${params}`
    );
    return handleResponse(response);
  },

  /**
   * Delete snapshot
   */
  async deleteSnapshot(snapshotId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/remix/snapshots/${snapshotId}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

// Export error type for error handling in components
export { APIError };
