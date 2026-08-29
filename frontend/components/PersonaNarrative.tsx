/**
 * Persona Narrative Component
 * 
 * Displays AI-generated comprehensive narratives about a persona's psychological journey.
 * Styled with custom cream/moss/sage design system.
 */
'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { getAuthHeaders } from '@/lib/authHeaders';
import { RubixCard } from '@/components/rubix';

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>{personaName}&apos;s story</div>
          <div style={{ marginTop: 5, fontSize: 13.5, color: 'rgba(214,235,255,0.68)' }}>
            The whole picture, woven together from everything you&apos;ve built.
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {narrativeHistory.length > 0 && (
            <button type="button" className="rubix-btn-ghost" onClick={() => setShowHistory(!showHistory)}>
              {showHistory ? 'Hide' : 'Show'} history ({narrativeHistory.length})
            </button>
          )}
          <button type="button" className="rubix-btn-primary" onClick={generateNarrative} disabled={generating} aria-busy={generating || undefined}>
            {generating ? 'Weaving their story…' : narrative ? 'Generate new version' : 'See how their story unfolds'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 15px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
          {error}
        </div>
      )}

      {showHistory && narrativeHistory.length > 0 && (
        <RubixCard variant="flat" style={{ padding: 18 }}>
          <div style={{ fontSize: 14, fontWeight: 600 }}>Narrative history</div>
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {narrativeHistory.map((n) => {
              const active = narrative?.id === n.id
              return (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => setNarrative(n)}
                  style={{
                    width: '100%', textAlign: 'left', padding: '11px 14px', borderRadius: 12, cursor: 'pointer',
                    background: active ? 'linear-gradient(160deg, rgba(150,200,255,0.22), rgba(90,140,255,0.14))' : 'rgba(255,255,255,0.05)',
                    border: `1px solid ${active ? 'rgba(200,230,255,0.4)' : 'rgba(170,210,255,0.16)'}`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 600 }}>Generation #{n.generation_number}</div>
                      <div style={{ marginTop: 2, fontSize: 12, color: 'rgba(214,235,255,0.65)' }}>
                        Age {n.persona_age_at_generation} · {n.total_experiences_count} experiences
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: 'rgba(200,226,255,0.5)', whiteSpace: 'nowrap' }}>{formatDate(n.generated_at)}</div>
                  </div>
                </button>
              )
            })}
          </div>
        </RubixCard>
      )}

      {narrative ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
          <RubixCard variant="flat" style={{ padding: 18 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, textAlign: 'center' }}>
              <MetaStat value={narrative.persona_age_at_generation} label="years old" />
              <MetaStat value={narrative.total_experiences_count} label="life moments" />
              <MetaStat value={Math.ceil(narrative.word_count / 200)} label="min read" />
              <MetaStat value={`#${narrative.generation_number}`} label="version" />
            </div>
          </RubixCard>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <NarrativeSection title="The whole picture" content={narrative.executive_summary} />
            <NarrativeSection title="How they got here" content={narrative.developmental_timeline} />
            <NarrativeSection title="Where they are now" content={narrative.current_presentation} />
            {narrative.treatment_response && (
              <NarrativeSection title="How support has helped" content={narrative.treatment_response} />
            )}
            <NarrativeSection title="Looking ahead" content={narrative.prognosis} />
          </div>

          <div>
            <button type="button" className="rubix-btn-ghost" onClick={exportNarrative}>Export markdown</button>
          </div>
        </div>
      ) : (
        !generating && (
          <RubixCard style={{ padding: '48px 24px', textAlign: 'center' }}>
            <div style={{ width: 44, height: 44, margin: '0 auto 16px' }}>
              <div className="rubix-diamond" style={{ width: 44, height: 44 }} />
            </div>
            <div style={{ fontSize: 15.5, fontWeight: 600 }}>Their story awaits</div>
            <div style={{ marginTop: 8, fontSize: 13.5, lineHeight: 1.6, color: 'rgba(214,235,255,0.65)', maxWidth: 420, marginLeft: 'auto', marginRight: 'auto' }}>
              Generate a narrative to weave together everything you know about this person into one cohesive story.
            </div>
          </RubixCard>
        )
      )}

      {generating && (
        <RubixCard style={{ padding: '48px 24px', textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: 30, height: 30, margin: '0 auto', borderRadius: 999, border: '3px solid rgba(150,205,255,0.25)', borderTopColor: '#7fb2ff' }} />
          <div style={{ marginTop: 16, fontSize: 15.5, fontWeight: 600 }}>Weaving their story…</div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'rgba(214,235,255,0.65)' }}>
            Looking at their whole journey — the moments that shaped them, where they are now (15-30 seconds).
          </div>
        </RubixCard>
      )}
    </div>
  );
}

function MetaStat({ value, label }: { value: string | number; label: string }) {
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
      <div style={{ marginTop: 2, fontSize: 11, color: 'rgba(214,235,255,0.6)' }}>{label}</div>
    </div>
  );
}

interface NarrativeSectionProps {
  title: string;
  content: string;
}

function NarrativeSection({ title, content }: NarrativeSectionProps) {
  return (
    <RubixCard style={{ padding: 24 }}>
      <div style={{ fontSize: 16.5, fontWeight: 700, marginBottom: 12 }}>{title}</div>
      {content && content.trim().length > 0 ? (
        <div style={{ fontSize: 14, lineHeight: 1.7, color: 'rgba(226,240,255,0.88)' }}>
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      ) : (
        <div style={{ fontSize: 13.5, fontStyle: 'italic', color: 'rgba(200,226,255,0.5)' }}>No content available for this section</div>
      )}
    </RubixCard>
  );
}
