'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { api, type Timeline, type Experience, type Intervention } from '@/lib/api'
import { RubixShell, RubixCard, RubixBadge, RubixDrawer, RubixDrawerSection, RubixDelta } from '@/components/rubix'
import { titleCase } from '@/lib/rubix/stateDimensions'

type Row =
  | { kind: 'experience'; age: number; sortKey: number; data: Experience }
  | { kind: 'intervention'; age: number; sortKey: number; data: Intervention }

type FilterKey = 'all' | 'experience' | 'intervention'

export default function FullLifePage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()

  const [timeline, setTimeline] = useState<Timeline | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set())
  const [detail, setDetail] = useState<Row | null>(null)

  useEffect(() => {
    if (!authLoading && !user) router.push('/login')
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) loadTimeline()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, user])

  async function loadTimeline() {
    setLoading(true)
    setLoadError(false)
    try {
      const data = await api.getTimeline(params.id)
      setTimeline(data)
    } catch (err) {
      console.error('Failed to load timeline:', err)
      setLoadError(true)
    } finally {
      setLoading(false)
    }
  }

  const persona = timeline?.persona

  const rows: Row[] = useMemo(() => {
    if (!timeline) return []
    const expRows: Row[] = timeline.experiences.map((e) => ({ kind: 'experience', age: e.age_at_event, sortKey: e.sequence_index, data: e }))
    const interventionRows: Row[] = timeline.interventions.map((i) => ({ kind: 'intervention', age: i.age_at_intervention, sortKey: 0, data: i }))
    return [...expRows, ...interventionRows].sort((a, b) => (a.age - b.age) || (a.sortKey - b.sortKey))
  }, [timeline])

  const filteredRows = useMemo(() => (filter === 'all' ? rows : rows.filter((r) => r.kind === filter)), [rows, filter])

  const decadeGroups = useMemo(() => {
    const groups = new Map<number, Row[]>()
    for (const r of filteredRows) {
      const d = Math.floor(r.age / 10) * 10
      if (!groups.has(d)) groups.set(d, [])
      groups.get(d)!.push(r)
    }
    return Array.from(groups.entries()).sort((a, b) => a[0] - b[0])
  }, [filteredRows])

  function toggleDecade(d: number) {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(d)) next.delete(d)
      else next.add(d)
      return next
    })
  }

  function rowKey(r: Row) {
    return r.kind === 'experience' ? `e-${r.data.id}` : `i-${r.data.id}`
  }

  if (authLoading || loading) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 13.5, color: 'rgba(210,232,255,0.65)' }}>Loading…</div>
      </div>
    )
  }
  if (!user) return null

  if (loadError || !timeline || !persona) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <RubixCard style={{ padding: 32, textAlign: 'center', maxWidth: 380 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>Couldn&apos;t load this life</div>
          <button type="button" className="rubix-btn-primary" style={{ marginTop: 18 }} onClick={loadTimeline}>Retry</button>
        </RubixCard>
      </div>
    )
  }

  const ages = rows.map((r) => r.age)
  const minAge = ages.length ? Math.min(...ages) : persona.baseline_age
  const maxAge = ages.length ? Math.max(...ages) : persona.current_age

  return (
    <RubixShell persona={{ id: persona.id, name: persona.name }}>
      <div style={{ maxWidth: 1080 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.025em' }}>{persona.name}&apos;s full life</div>
            <div style={{ marginTop: 7, fontSize: 14, color: 'rgba(214,235,255,0.7)' }}>
              {rows.length === 0
                ? 'Nothing recorded yet.'
                : `${rows.length} moment${rows.length === 1 ? '' : 's'}, ages ${minAge} to ${maxAge}. Grouped by decade — open one to read it.`}
            </div>
          </div>
          <Link href={`/persona/${persona.id}/build`} className="rubix-btn-ghost">
            + Add more life
          </Link>
        </div>

        <RubixCard variant="flat" style={{ marginTop: 20, padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {([
            { key: 'all', label: 'All' },
            { key: 'experience', label: 'Experiences' },
            { key: 'intervention', label: 'Therapy' },
          ] as const).map((f) => (
            <button key={f.key} type="button" className="rubix-chip" data-active={filter === f.key ? 'true' : 'false'} aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}>
              {f.label}
            </button>
          ))}
        </RubixCard>

        <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {decadeGroups.length === 0 && (
            <RubixCard style={{ padding: 32, textAlign: 'center' }}>
              <div style={{ fontSize: 15, fontWeight: 600 }}>Nothing here yet</div>
              <div style={{ marginTop: 8, fontSize: 13.5, color: 'rgba(216,236,255,0.7)' }}>
                <Link href={`/persona/${persona.id}/build`} style={{ color: 'inherit', textDecoration: 'underline' }}>Build their life</Link> to start filling this in.
              </div>
            </RubixCard>
          )}
          {decadeGroups.map(([decade, decadeRows]) => {
            const isOpen = !collapsed.has(decade)
            return (
              <RubixCard key={decade} style={{ padding: 0, overflow: 'hidden' }}>
                <button
                  type="button"
                  onClick={() => toggleDecade(decade)}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: '17px 20px', cursor: 'pointer', background: 'transparent', border: 'none', textAlign: 'left' }}
                >
                  <span style={{ fontSize: 13, width: 14, color: 'rgba(210,232,255,0.7)' }}>{isOpen ? '▾' : '▸'}</span>
                  <span style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.01em', color: 'var(--rubix-text)' }}>{decade}s</span>
                  <span style={{ marginLeft: 'auto', fontSize: 12.5, color: 'rgba(210,232,255,0.66)' }}>
                    {decadeRows.length} moment{decadeRows.length === 1 ? '' : 's'}
                  </span>
                </button>
                {isOpen && (
                  <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 7 }}>
                    {decadeRows.map((r) => {
                      const key = rowKey(r)
                      const isExperience = r.kind === 'experience'
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => setDetail(r)}
                          style={{
                            width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: '13px 16px', borderRadius: 14, cursor: 'pointer', textAlign: 'left',
                            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(170,210,255,0.16)',
                          }}
                        >
                          <span style={{ flex: '0 0 34px', fontSize: 14.5, fontWeight: 700 }}>{r.age}</span>
                          <span style={{ width: 8, height: 8, borderRadius: 999, flex: '0 0 8px', background: isExperience ? '#7fe3ff' : '#b39bff', boxShadow: `0 0 8px ${isExperience ? '#7fe3ff' : '#b39bff'}` }} />
                          <span style={{ flex: 1, minWidth: 0, fontSize: 14, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {isExperience ? r.data.user_description : `${r.data.therapy_type} · ${r.data.duration.replace(/_/g, ' ')}, ${r.data.intensity.replace(/_/g, ' ')}`}
                          </span>
                          <RubixBadge tone={isExperience ? 'neutral' : 'violet'}>{isExperience ? 'Experience' : 'Therapy'}</RubixBadge>
                        </button>
                      )
                    })}
                  </div>
                )}
              </RubixCard>
            )
          })}
        </div>
      </div>

      <RubixDrawer
        open={detail !== null}
        onClose={() => setDetail(null)}
        kind={detail?.kind === 'experience' ? 'EXPERIENCE' : 'THERAPY'}
        kindColor={detail?.kind === 'experience' ? '#7fe3ff' : '#b39bff'}
        title={detail ? `Age ${detail.age}` : ''}
        subtitle={detail?.kind === 'experience' ? (detail.data as Experience).user_description : undefined}
      >
        {detail?.kind === 'experience' && <ExperienceDetail exp={detail.data as Experience} />}
        {detail?.kind === 'intervention' && <InterventionDetail iv={detail.data as Intervention} />}
      </RubixDrawer>
    </RubixShell>
  )
}

function ExperienceDetail({ exp }: { exp: Experience }) {
  return (
    <>
      {exp.interpretation?.belief_statement && (
        <RubixDrawerSection label="BELIEF FORMED">
          <div style={{ fontSize: 14.5, lineHeight: 1.65, color: 'rgba(230,242,255,0.92)' }}>{exp.interpretation.belief_statement}</div>
        </RubixDrawerSection>
      )}
      {exp.interpretation?.adaptation_strategy && (
        <RubixDrawerSection label="ADAPTATION">
          <div style={{ fontSize: 14.5, lineHeight: 1.65, color: 'rgba(230,242,255,0.92)' }}>{titleCase(exp.interpretation.adaptation_strategy)}</div>
          {exp.interpretation.reasoning && (
            <div style={{ marginTop: 8, fontSize: 13, lineHeight: 1.6, color: 'rgba(200,226,255,0.65)' }}>{exp.interpretation.reasoning}</div>
          )}
        </RubixDrawerSection>
      )}
      {exp.pattern_connections.length > 0 && (
        <RubixDrawerSection label="CONNECTED PATTERNS">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {exp.pattern_connections.map((p) => (
              <RubixBadge key={p.pattern_id} tone="muted">{p.pattern_name} · {p.effect}</RubixBadge>
            ))}
          </div>
        </RubixDrawerSection>
      )}
      {exp.hypothesis_connections.length > 0 && (
        <RubixDrawerSection label="HYPOTHESIS EVIDENCE">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {exp.hypothesis_connections.map((h) => (
              <div key={h.hypothesis_id} style={{ fontSize: 13, color: 'rgba(224,239,255,0.85)' }}>
                {titleCase(h.pattern_key)} — <span style={{ color: h.evidence_role === 'supporting' ? '#a8f2cf' : '#ffb3a6' }}>{h.evidence_role}</span>
              </div>
            ))}
          </div>
        </RubixDrawerSection>
      )}
      {exp.protective_factors.length > 0 && (
        <RubixDrawerSection label="PROTECTIVE FACTORS">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {exp.protective_factors.map((p) => (
              <RubixBadge key={p.id} tone="positive">{titleCase(p.factor_type)}</RubixBadge>
            ))}
          </div>
        </RubixDrawerSection>
      )}
      {!exp.interpretation && exp.pattern_connections.length === 0 && exp.hypothesis_connections.length === 0 && (
        <RubixDrawerSection label="STATUS">
          <div style={{ fontSize: 13.5, color: 'rgba(214,235,255,0.65)' }}>Not yet analyzed.</div>
        </RubixDrawerSection>
      )}
    </>
  )
}

function InterventionDetail({ iv }: { iv: Intervention }) {
  // symptom_changes carries the real Before/Intervention/After: {before, after,
  // percentage_improvement}. Guard defensively since the backend's own type
  // hint (Dict[str, int]) doesn't actually match what the route returns.
  const sc = iv.symptom_changes
  const hasBeforeAfter = !!sc && typeof sc === 'object' && 'before' in sc && 'after' in sc
  const beforeAfterRows = hasBeforeAfter
    ? Object.keys((sc as any).before).map((metric) => ({
        metric,
        before: (sc as any).before[metric],
        after: (sc as any).after[metric],
        improvement: (sc as any).percentage_improvement?.[metric],
      }))
    : []

  const sustained = Array.isArray(iv.sustained_effects)
    ? iv.sustained_effects
    : iv.sustained_effects
    ? Object.values(iv.sustained_effects).map((v) => String(v))
    : []

  return (
    <>
      <RubixDrawerSection label="SUPPORT">
        <div style={{ fontSize: 14.5, lineHeight: 1.65, color: 'rgba(230,242,255,0.92)' }}>
          {iv.therapy_type} — {iv.duration.replace(/_/g, ' ')}, {iv.intensity.replace(/_/g, ' ')}
        </div>
        {iv.user_notes && <div style={{ marginTop: 8, fontSize: 13, color: 'rgba(200,226,255,0.65)' }}>{iv.user_notes}</div>}
      </RubixDrawerSection>

      {beforeAfterRows.length > 0 && (
        <RubixDrawerSection label="BEFORE → AFTER">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {beforeAfterRows.map((r) => (
              <div key={r.metric} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                <div style={{ flex: '0 0 150px', color: 'rgba(214,235,255,0.65)' }}>{titleCase(r.metric)}</div>
                <div style={{ color: 'rgba(230,242,255,0.9)' }}>{r.before} → {r.after}</div>
                {r.improvement != null && (
                  <RubixDelta label={`${r.improvement > 0 ? '−' : '+'}${Math.abs(Math.round(r.improvement))}%`} tone={r.improvement > 0 ? 'positive' : 'negative'} />
                )}
              </div>
            ))}
          </div>
        </RubixDrawerSection>
      )}

      {sustained.length > 0 && (
        <RubixDrawerSection label="WHAT IMPROVED">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {sustained.map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 8, height: 8, borderRadius: 3, marginTop: 6, flex: '0 0 8px', background: '#6fe3b0', boxShadow: '0 0 9px #6fe3b0' }} />
                <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'rgba(226,240,255,0.88)' }}>{s}</div>
              </div>
            ))}
          </div>
        </RubixDrawerSection>
      )}

      {iv.coping_skills_gained.length > 0 && (
        <RubixDrawerSection label="COPING SKILLS GAINED">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {iv.coping_skills_gained.map((s, i) => <RubixBadge key={i} tone="positive">{s}</RubixBadge>)}
          </div>
        </RubixDrawerSection>
      )}

      {iv.limitations && iv.limitations.length > 0 && (
        <RubixDrawerSection label="WHAT PERSISTED">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {iv.limitations.map((l, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 8, height: 8, borderRadius: 3, marginTop: 6, flex: '0 0 8px', background: '#ff9282', boxShadow: '0 0 9px #ff9282' }} />
                <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'rgba(226,240,255,0.88)' }}>{l}</div>
              </div>
            ))}
          </div>
        </RubixDrawerSection>
      )}
    </>
  )
}
