/**
 * Persona Narrative Component
 * 
 * Displays AI-generated comprehensive narratives about a persona's psychological journey.
 * Styled with custom cream/moss/sage design system.
 */
'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { auth } from '@/lib/firebase';

interface NarrativeData {
  id: string;
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

interface PersonaNarrativeProps {
  personaId: string;
  personaName: string;
}

export default function PersonaNarrative({ personaId, personaName }: PersonaNarrativeProps) {
  const [narrative, setNarrative] = useState<NarrativeData | null>(null);
  const [narrativeHistory, setNarrativeHistory] = useState<NarrativeData[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  // Load narrative history on mount
  useEffect(() => {
    loadNarrativeHistory();
  }, [personaId]);

  async function getAuthHeaders() {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');

    const user = auth.currentUser;
    if (!user) throw new Error('Not authenticated');
    const token = await user.getIdToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async function generateNarrative() {
    setGenerating(true);
    setError(null);

    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
      const apiRoot = apiBase ? `${apiBase}/api/v1` : '/api/v1';

      const headers = await getAuthHeaders();
      const response = await fetch(
        `${apiRoot}/narratives/personas/${personaId}/generate`,
        {
          method: 'POST',
          headers
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setNarrative(data);

      // Reload history
      await loadNarrativeHistory();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate narrative');
    } finally {
      setGenerating(false);
    }
  }

  async function loadNarrativeHistory() {
    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
      const apiRoot = apiBase ? `${apiBase}/api/v1` : '/api/v1';

      const headers = await getAuthHeaders();
      const response = await fetch(
        `${apiRoot}/narratives/personas/${personaId}`,
        { headers }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Loaded narratives:', data.length);
        if (data.length > 0) {
          console.log('📝 First narrative sections:', {
            exec: data[0].executive_summary?.length || 0,
            dev: data[0].developmental_timeline?.length || 0,
            curr: data[0].current_presentation?.length || 0,
            prog: data[0].prognosis?.length || 0
          });
        }
        setNarrativeHistory(data);

        // Set most recent as current if none selected
        if (!narrative && data.length > 0) {
          setNarrative(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load narrative history:', err);
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function exportNarrative() {
    if (!narrative) return;

    const blob = new Blob([narrative.full_narrative], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${personaName}-narrative-${narrative.generation_number}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      {/* Header with generate button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-apple-text-primary font-['Crimson_Pro']">
            Persona Narrative
          </h2>
          <p className="text-sm text-apple-text-secondary font-['Outfit']">
            AI-generated comprehensive psychological summary
          </p>
        </div>

        <div className="flex gap-3">
          {narrativeHistory.length > 0 && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-4 py-2 text-apple-text-secondary hover:text-apple-text-primary font-['Outfit']"
            >
              {showHistory ? 'Hide' : 'Show'} History ({narrativeHistory.length})
            </button>
          )}
          
          <button
            onClick={generateNarrative}
            disabled={generating}
            className="btn-primary"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Generating...
              </span>
            ) : (
              '✨ Generate Narrative'
            )}
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <p className="text-red-500 font-['Outfit']">{error}</p>
        </div>
      )}

      {/* History sidebar */}
      {showHistory && narrativeHistory.length > 0 && (
        <div className="bg-apple-bg-tertiary/20 border border-apple-border-light rounded-xl p-4">
          <h3 className="text-lg font-semibold text-apple-text-primary mb-3 font-['Crimson_Pro']">
            Narrative History
          </h3>
          <div className="space-y-2">
            {narrativeHistory.map((n) => (
              <button
                key={n.id}
                onClick={() => setNarrative(n)}
                className={`w-full text-left p-3 rounded-lg transition-colors font-['Outfit'] ${
                  narrative?.id === n.id
                    ? 'bg-apple-blue-600/20 border border-apple-blue-200'
                    : 'bg-white hover:bg-apple-bg-tertiary/30 border border-apple-border-light'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-apple-text-primary">
                      Generation #{n.generation_number}
                    </div>
                    <div className="text-sm text-apple-text-secondary">
                      Age {n.persona_age_at_generation} • {n.total_experiences_count} experiences
                    </div>
                  </div>
                  <div className="text-xs text-apple-text-secondary">
                    {formatDate(n.generated_at)}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Narrative display */}
      {narrative ? (
        <div className="space-y-6">
          {/* Metadata bar */}
          <div className="bg-apple-blue-100/20 border border-apple-border/30 rounded-xl p-4">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-apple-text-primary font-['Crimson_Pro']">
                  #{narrative.generation_number}
                </div>
                <div className="text-xs text-apple-text-secondary font-['Outfit']">Generation</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-apple-text-primary font-['Crimson_Pro']">
                  {narrative.persona_age_at_generation}
                </div>
                <div className="text-xs text-apple-text-secondary font-['Outfit']">Age</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-apple-text-primary font-['Crimson_Pro']">
                  {narrative.word_count}
                </div>
                <div className="text-xs text-apple-text-secondary font-['Outfit']">Words</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-apple-text-primary font-['Crimson_Pro']">
                  {narrative.generation_time_seconds || '–'}s
                </div>
                <div className="text-xs text-apple-text-secondary font-['Outfit']">Generated</div>
              </div>
            </div>
          </div>

          {/* Narrative sections */}
          <div className="space-y-6">
            {/* Executive Summary */}
            <NarrativeSection
              title="📖 Executive Summary"
              content={narrative.executive_summary}
              icon="summary"
            />

            {/* Developmental Timeline */}
            <NarrativeSection
              title="🌱 Developmental Timeline"
              content={narrative.developmental_timeline}
              icon="timeline"
            />

            {/* Current Presentation */}
            <NarrativeSection
              title="🧭 Current Presentation"
              content={narrative.current_presentation}
              icon="presentation"
            />

            {/* Treatment Response (if exists) */}
            {narrative.treatment_response && (
              <NarrativeSection
                title="💊 Treatment Response"
                content={narrative.treatment_response}
                icon="treatment"
              />
            )}

            {/* Prognosis */}
            <NarrativeSection
              title="🔮 Prognosis & Recommendations"
              content={narrative.prognosis}
              icon="prognosis"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={exportNarrative}
              className="btn-secondary"
            >
              Export Markdown
            </button>
          </div>
        </div>
      ) : (
        !generating && (
          <div className="text-center py-12 bg-white border border-apple-border-light rounded-xl">
            <div className="text-6xl mb-4">📖</div>
            <h3 className="text-lg font-semibold text-apple-text-primary mb-2 font-['Crimson_Pro']">
              No Narrative Generated Yet
            </h3>
            <p className="text-apple-text-secondary mb-4 font-['Outfit']">
              Click "Generate Narrative" to create a comprehensive AI-powered summary
            </p>
          </div>
        )
      )}

      {/* Generating state */}
      {generating && (
        <div className="text-center py-12 bg-apple-blue-100/10 border border-apple-border/30 rounded-xl">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-apple-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-semibold text-apple-blue-600 mb-2 font-['Crimson_Pro']">
            Generating Narrative...
          </h3>
          <p className="text-apple-text-secondary font-['Outfit']">
            Analyzing timeline and crafting comprehensive summary (15-30 seconds)
          </p>
        </div>
      )}
    </div>
  );
}

// Section component
interface NarrativeSectionProps {
  title: string;
  content: string;
  icon: string;
}

function NarrativeSection({ title, content, icon }: NarrativeSectionProps) {
  // Debug: log content
  console.log(`${title}:`, content ? `${content.substring(0, 100)}...` : 'EMPTY');

  return (
    <div className="bg-white border border-apple-border-light rounded-xl p-6">
      <h3 className="text-xl font-bold text-apple-text-primary mb-4 font-['Crimson_Pro']">
        {title}
      </h3>
      {content && content.trim().length > 0 ? (
        <div className="prose prose-sm max-w-none font-['Outfit'] text-apple-text-primary whitespace-pre-wrap">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      ) : (
        <div className="text-apple-text-secondary italic">No content available for this section</div>
      )}
    </div>
  );
}
