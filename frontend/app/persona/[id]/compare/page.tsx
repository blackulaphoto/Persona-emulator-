'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { api, type Persona, type PersonalityTraits } from '@/lib/api'
import { remixAPI, type TimelineSnapshot, type SnapshotComparison } from '@/lib/api/templates'
import { RubixShell, RubixCard, RubixBadge, RubixDelta, RubixEmptyState } from '@/components/rubix'
import { STATE_DIMENSIONS, titleCase } from '@/lib/rubix/stateDimensions'
import { attachmentStyleLabel, attachmentStyleTone } from '@/lib/rubix/attachmentStyle'

const BIG_FIVE_LABELS: Record<keyof PersonalityTraits, string> = {
  openness: 'Openness', conscientiousness: 'Conscientiousness', extraversion: 'Extraversion',
  agreeableness: 'Agreeableness', neuroticism: 'Neuroticism',
}

export default function ComparePage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()

  const [persona, setPersona] = useState<Persona | null>(null)
  const [snapshots, setSnapshots] = useState<TimelineSnapshot[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  const [idA, setIdA] = useState('')
  const [idB, setIdB] = useState('')
  const [comparison, setComparison] = useState<SnapshotComparison | null>(null)
  const [comparing, setComparing] = useState(false)
  const [compareError, setCompareError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) router.push('/login')
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, user])

  async function load() {
    setLoading(true)
    setLoadError(false)
    try {
      const [p, snaps] = await Promise.all([api.getPersona(params.id), remixAPI.listSnapshots(params.id)])
      setPersona(p)
      setSnapshots(snaps)
      if (snaps.length >= 2) {
        setIdA(snaps[snaps.length - 2].id)
        setIdB(snaps[snaps.length - 1].id)
      }
    } catch (err) {
      console.error('Failed to load compare data:', err)
      setLoadError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (idA && idB && idA !== idB) runCompare()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idA, idB])

  async function handleDeleteSnapshot(snapshotId: string) {
    if (!confirm('Delete this snapshot? This cannot be undone.')) return
    setDeletingId(snapshotId)
    try {
      await remixAPI.deleteSnapshot(snapshotId)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete snapshot')
    } finally {
      setDeletingId(null)
    }
  }

  async function runCompare() {
    setComparing(true)
    setCompareError(null)
    try {
      setComparison(await remixAPI.compareSnapshots(idA, idB))
    } catch (err) {
      setCompareError(err instanceof Error ? err.message : 'Failed to compare snapshots')
      setComparison(null)
    } finally {
      setComparing(false)
    }
  }

  const personalityRows = useMemo(() => {
    if (!comparison) return []
    return (Object.entries(comparison.personality_differences) as [keyof PersonalityTraits, typeof comparison.personality_differences[string]][])
      .filter(([, d]) => Math.abs(d.difference) >= 0.02)
      .sort((a, b) => Math.abs(b[1].difference) - Math.abs(a[1].difference))
  }, [comparison])

  const stateRows = useMemo(() => {
    if (!comparison) return []
    return Object.entries(comparison.state_differences).filter(([key]) => STATE_DIMENSIONS[key])
  }, [comparison])

  const attachmentRows = useMemo(() => {
    if (!comparison?.attachment_differences) return []
    return Object.entries(comparison.attachment_differences)
  }, [comparison])

  if (authLoading || loading) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 13.5, color: 'rgba(210,232,255,0.65)' }}>Loading…</div>
      </div>
    )
  }
  if (!user) return null

  if (loadError || !persona) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <RubixCard style={{ padding: 32, textAlign: 'center', maxWidth: 380 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>Couldn&apos;t load this life</div>
          <button type="button" className="rubix-btn-primary" style={{ marginTop: 18 }} onClick={load}>Retry</button>
        </RubixCard>
      </div>
    )
  }

  return (
    <RubixShell persona={{ id: persona.id, name: persona.name }}>
      <div style={{ maxWidth: 980 }}>
        <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.025em' }}>Compare</div>
        <div style={{ marginTop: 7, fontSize: 14, color: 'rgba(214,235,255,0.7)' }}>
          See exactly what changed between two saved moments in {persona.name}&apos;s life.
        </div>

        {snapshots.length < 2 ? (
          <RubixCard style={{ marginTop: 24 }}>
            <RubixEmptyState
              title="Not enough snapshots yet"
              description="Save at least two snapshots to compare them. You can save one from the dashboard at any point in this life."
              action={
                <Link href={`/persona/${persona.id}`} className="rubix-btn-primary">
                  Go to dashboard
                </Link>
              }
            />
          </RubixCard>
        ) : (
          <>
            <RubixCard variant="flat" style={{ marginTop: 22, padding: 18, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <SnapshotPicker label="FIRST" value={idA} onChange={setIdA} onDelete={handleDeleteSnapshot} deletingId={deletingId} snapshots={snapshots} />
              <div style={{ fontSize: 20, color: 'rgba(200,226,255,0.5)', paddingBottom: 10 }}>→</div>
              <SnapshotPicker label="SECOND" value={idB} onChange={setIdB} onDelete={handleDeleteSnapshot} deletingId={deletingId} snapshots={snapshots} />
            </RubixCard>

            {idA === idB && (
              <div style={{ marginTop: 14, fontSize: 13, color: 'rgba(214,235,255,0.6)' }}>Pick two different snapshots to compare.</div>
            )}

            {compareError && (
              <div style={{ marginTop: 14, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
                {compareError}
              </div>
            )}

            {comparing && <div style={{ marginTop: 20, fontSize: 13.5, color: 'rgba(214,235,255,0.65)' }}>Comparing…</div>}

            {comparison && !comparing && idA !== idB && (
              <div style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
                <RubixCard style={{ padding: 22 }}>
                  <div style={{ fontSize: 14, lineHeight: 1.7, color: 'rgba(226,240,255,0.9)' }}>{comparison.summary}</div>
                </RubixCard>

                <div className="rubix-grid-2up" style={{ display: 'grid', gap: 16 }}>
                  <SnapshotSideCard label={comparison.snapshot_1.label} side={comparison.snapshot_1} />
                  <SnapshotSideCard label={comparison.snapshot_2.label} side={comparison.snapshot_2} />
                </div>

                {personalityRows.length > 0 && (
                  <RubixCard style={{ padding: 22 }}>
                    <div style={{ fontSize: 15.5, fontWeight: 700 }}>Personality</div>
                    <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {personalityRows.map(([trait, d]) => (
                        <RubixDelta
                          key={trait}
                          label={`${BIG_FIVE_LABELS[trait]} ${d.difference > 0 ? '+' : ''}${Math.round(d.difference * 100)} pts`}
                          tone={trait === 'neuroticism' ? (d.difference < 0 ? 'positive' : 'negative') : 'neutral'}
                        />
                      ))}
                    </div>
                  </RubixCard>
                )}

                {stateRows.length > 0 && (
                  <RubixCard style={{ padding: 22 }}>
                    <div style={{ fontSize: 15.5, fontWeight: 700 }}>What they were navigating</div>
                    <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {stateRows.map(([key, d]) => (
                        <div key={key} style={{ fontSize: 13.5, color: 'rgba(224,239,255,0.85)' }}>
                          <strong>{STATE_DIMENSIONS[key].label}:</strong>{' '}
                          {d.change_direction === 'newly_tracked' && 'newly signaled'}
                          {d.change_direction === 'no_longer_tracked' && 'no longer notable'}
                          {(d.change_direction === 'increased' || d.change_direction === 'decreased') && d.difference != null &&
                            `${d.snapshot_1?.toFixed(2)} → ${d.snapshot_2?.toFixed(2)}`}
                          {d.change_direction === 'unchanged' && 'unchanged'}
                        </div>
                      ))}
                    </div>
                  </RubixCard>
                )}

                {attachmentRows.length > 0 && (
                  <RubixCard style={{ padding: 22 }}>
                    <div style={{ fontSize: 15.5, fontWeight: 700 }}>Attachment</div>
                    <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {attachmentRows.map(([key, d]) => (
                        <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13.5 }}>
                          <span style={{ flex: '0 0 140px', color: 'rgba(214,235,255,0.65)' }}>{titleCase(key)}</span>
                          {key === 'style' ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <RubixBadge tone={attachmentStyleTone(d.snapshot_1 as string)}>{attachmentStyleLabel(d.snapshot_1 as string)}</RubixBadge>
                              <span style={{ color: 'rgba(214,235,255,0.4)' }}>→</span>
                              <RubixBadge tone={attachmentStyleTone(d.snapshot_2 as string)}>{attachmentStyleLabel(d.snapshot_2 as string)}</RubixBadge>
                            </div>
                          ) : (
                            <span>{typeof d.snapshot_1 === 'number' ? d.snapshot_1.toFixed(2) : '—'} → {typeof d.snapshot_2 === 'number' ? d.snapshot_2.toFixed(2) : '—'}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </RubixCard>
                )}

                <PatternDiffCard title="Adaptation patterns" diff={comparison.adaptation_pattern_differences} nameKey="pattern_name" />
                <PatternDiffCard title="Patterns being considered" diff={comparison.clinical_pattern_differences} nameKey="pattern_key" />
              </div>
            )}
          </>
        )}
      </div>
    </RubixShell>
  )
}

function SnapshotPicker({ label, value, onChange, onDelete, deletingId, snapshots }: {
  label: string
  value: string
  onChange: (v: string) => void
  onDelete: (id: string) => void
  deletingId: string | null
  snapshots: TimelineSnapshot[]
}) {
  const isDeleting = deletingId === value
  return (
    <div>
      <label className="rubix-field-label" htmlFor={`snap-${label}`}>{label}</label>
      <div style={{ marginTop: 9, display: 'flex', gap: 8 }}>
        <select id={`snap-${label}`} className="rubix-input" style={{ minWidth: 220 }} value={value} onChange={(e) => onChange(e.target.value)}>
          {snapshots.map((s) => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
        {value && (
          <button
            type="button"
            className="rubix-btn-danger"
            style={{ padding: '0 16px', fontSize: 12.5 }}
            onClick={() => onDelete(value)}
            disabled={deletingId !== null}
            aria-label={`Delete snapshot ${snapshots.find((s) => s.id === value)?.label ?? ''}`}
          >
            {isDeleting ? 'Deleting…' : 'Delete'}
          </button>
        )}
      </div>
    </div>
  )
}

function SnapshotSideCard({ label, side }: { label: string; side: SnapshotComparison['snapshot_1'] }) {
  return (
    <RubixCard style={{ padding: 20 }}>
      <div style={{ fontSize: 14.5, fontWeight: 700 }}>{label}</div>
      {side.attachment_style && (
        <div style={{ marginTop: 8 }}>
          <RubixBadge tone={attachmentStyleTone(side.attachment_style)}>{attachmentStyleLabel(side.attachment_style)}</RubixBadge>
        </div>
      )}
      <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, textAlign: 'center' }}>
        {(Object.entries(side.personality) as [string, number][]).map(([trait, value]) => (
          <div key={trait}>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{Math.round(value * 100)}</div>
            <div style={{ fontSize: 9.5, color: 'rgba(200,226,255,0.55)', textTransform: 'uppercase' }}>{trait.slice(0, 4)}</div>
          </div>
        ))}
      </div>
    </RubixCard>
  )
}

function PatternDiffCard({ title, diff, nameKey }: { title: string; diff: { new: any[]; resolved: any[]; changed: any[] }; nameKey: string }) {
  if (diff.new.length === 0 && diff.resolved.length === 0 && diff.changed.length === 0) return null
  const label = (p: any) => titleCase(p[nameKey] || p.pattern_name || p.adaptation_strategy || p.pattern_key || 'unknown')
  return (
    <RubixCard style={{ padding: 22 }}>
      <div style={{ fontSize: 15.5, fontWeight: 700 }}>{title}</div>
      <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {diff.new.length > 0 && (
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.08em', color: 'rgba(150,230,180,0.85)' }}>NEW</div>
            <div style={{ marginTop: 7, display: 'flex', flexWrap: 'wrap', gap: 7 }}>
              {diff.new.map((p, i) => <RubixBadge key={i} tone="positive">{label(p)}</RubixBadge>)}
            </div>
          </div>
        )}
        {diff.resolved.length > 0 && (
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.08em', color: 'rgba(200,226,255,0.55)' }}>RESOLVED</div>
            <div style={{ marginTop: 7, display: 'flex', flexWrap: 'wrap', gap: 7 }}>
              {diff.resolved.map((p, i) => <RubixBadge key={i} tone="muted">{label(p)}</RubixBadge>)}
            </div>
          </div>
        )}
        {diff.changed.length > 0 && (
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.08em', color: 'rgba(255,210,150,0.85)' }}>CHANGED</div>
            <div style={{ marginTop: 7, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {diff.changed.map((c, i) => {
                // Adaptation patterns carry a status (emerging/established/...);
                // clinical pattern hypotheses don't - they only move on
                // evidence_strength. Render whichever this pair actually has
                // rather than assuming a field neither type guarantees.
                const status1 = c.snapshot_1?.status
                const status2 = c.snapshot_2?.status
                const strength1 = c.snapshot_1?.evidence_strength
                const strength2 = c.snapshot_2?.evidence_strength
                return (
                  <div key={i} style={{ fontSize: 13, color: 'rgba(224,239,255,0.85)' }}>
                    {titleCase(c[nameKey] || c.pattern_name || c.adaptation_strategy || c.pattern_key || 'unknown')}:{' '}
                    {status1 || status2
                      ? `${status1 ?? '—'} → ${status2 ?? '—'}`
                      : `${strength1 != null ? Math.round(strength1 * 100) + '%' : 'no evidence yet'} → ${strength2 != null ? Math.round(strength2 * 100) + '%' : 'no evidence yet'}`}
                    {c.evidence_strength_change != null && ` (${c.evidence_strength_change > 0 ? '+' : ''}${c.evidence_strength_change.toFixed(2)})`}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </RubixCard>
  )
}
