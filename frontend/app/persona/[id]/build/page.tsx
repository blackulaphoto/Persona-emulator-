'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { api, type Timeline, type Experience, type Persona, type PersonalityTraits } from '@/lib/api'
import { RubixShell, RubixCard, RubixBadge, RubixDelta } from '@/components/rubix'
import { STATE_DIMENSIONS, STATE_NEUTRAL, STATE_NOTABLE_DELTA, titleCase } from '@/lib/rubix/stateDimensions'
import { attachmentStyleLabel, attachmentStyleTone } from '@/lib/rubix/attachmentStyle'
import { agesForDecade, draftStorageKey, LIFESPAN_DECADES, parseStoredDrafts, retainUnprocessedDrafts, sortLifeDrafts, type LifeDraft } from '@/lib/buildLifeDrafts'
import { comparePatternTrajectories, PATTERN_TRAJECTORY_COPY } from '@/lib/patternTrajectory'

type Draft = LifeDraft

const BIG_FIVE_LABELS: Record<keyof PersonalityTraits, string> = {
  openness: 'Openness',
  conscientiousness: 'Conscientiousness',
  extraversion: 'Extraversion',
  agreeableness: 'Agreeableness',
  neuroticism: 'Neuroticism',
}

export default function BuildTheirLifePage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()

  const [timeline, setTimeline] = useState<Timeline | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  const [decadeStart, setDecadeStart] = useState<number | null>(null)
  const [selectedAge, setSelectedAge] = useState<number | null>(null)
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [draftText, setDraftText] = useState('')
  const [draftsHydratedFor, setDraftsHydratedFor] = useState<string | null>(null)
  const [draftEditingId, setDraftEditingId] = useState<string | null>(null)
  const [draftEditText, setDraftEditText] = useState('')
  const [draftEditAge, setDraftEditAge] = useState('')

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [editAge, setEditAge] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)
  const [rowError, setRowError] = useState<string | null>(null)

  const [view, setView] = useState<'building' | 'analyzing' | 'reveal'>('building')
  const [beforePersona, setBeforePersona] = useState<Persona | null>(null)
  const [afterPersona, setAfterPersona] = useState<Persona | null>(null)
  const [batchFailures, setBatchFailures] = useState<{ description: string; error: string }[]>([])
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) router.push('/login')
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) loadTimeline()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, user])

  useEffect(() => {
    setDrafts(parseStoredDrafts(window.localStorage.getItem(draftStorageKey(params.id))))
    setDraftsHydratedFor(params.id)
  }, [params.id])

  useEffect(() => {
    if (draftsHydratedFor !== params.id) return
    window.localStorage.setItem(draftStorageKey(params.id), JSON.stringify(drafts))
  }, [drafts, draftsHydratedFor, params.id])

  async function loadTimeline() {
    setLoading(true)
    setLoadError(false)
    try {
      const data = await api.getTimeline(params.id)
      setTimeline(data)
      setSelectedAge((current) => {
        const initial = current ?? data.persona.current_age
        setDecadeStart(Math.floor(initial / 10) * 10)
        return initial
      })
    } catch (err) {
      console.error('Failed to load timeline:', err)
      setLoadError(true)
    } finally {
      setLoading(false)
    }
  }

  const persona = timeline?.persona
  const experiences = timeline?.experiences ?? []

  const decades = LIFESPAN_DECADES

  const density = useMemo(() => {
    const counts = new Map<number, number>()
    for (const e of experiences) {
      const d = Math.floor(e.age_at_event / 10) * 10
      counts.set(d, (counts.get(d) || 0) + 1)
    }
    const max = Math.max(1, ...Array.from(counts.values()))
    return decades.map((d) => ({ decade: d, count: counts.get(d) || 0, percent: Math.round(((counts.get(d) || 0) / max) * 100) }))
  }, [decades, experiences])

  const agesWithMarks = useMemo(() => {
    if (decadeStart == null) return []
    const list: { age: number; hasEvents: boolean; count: number }[] = []
    for (const a of agesForDecade(decadeStart)) {
      const count = experiences.filter((e) => e.age_at_event === a).length + drafts.filter((d) => d.age === a).length
      list.push({ age: a, hasEvents: count > 0, count })
    }
    return list
  }, [decadeStart, experiences, drafts])

  const experiencesAtAge = useMemo(
    () => (selectedAge == null ? [] : experiences.filter((e) => e.age_at_event === selectedAge).sort((a, b) => a.sequence_index - b.sequence_index)),
    [experiences, selectedAge]
  )
  const draftsAtAge = useMemo(() => (selectedAge == null ? [] : drafts.filter((d) => d.age === selectedAge)), [drafts, selectedAge])
  const sortedDrafts = useMemo(() => sortLifeDrafts(drafts), [drafts])

  function selectAge(age: number) {
    setSelectedAge(age)
    setEditingId(null)
    setRowError(null)
  }

  function addDraft() {
    const text = draftText.trim()
    if (!text || selectedAge == null) return
    setDrafts((d) => [...d, { localId: `draft-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, age: selectedAge, description: text }])
    setDraftText('')
  }

  function removeDraft(localId: string) {
    setDrafts((d) => d.filter((x) => x.localId !== localId))
  }

  function startDraftEdit(draft: Draft) {
    setDraftEditingId(draft.localId)
    setDraftEditText(draft.description)
    setDraftEditAge(String(draft.age))
  }

  function saveDraftEdit(localId: string) {
    const age = Number.parseInt(draftEditAge, 10)
    const description = draftEditText.trim()
    if (!description || !Number.isInteger(age) || age < 0 || age > 120) return
    setDrafts((current) => current.map((draft) => draft.localId === localId ? { ...draft, age, description } : draft))
    setDraftEditingId(null)
  }

  function startEdit(exp: Experience) {
    setEditingId(exp.id)
    setEditText(exp.user_description)
    setEditAge(String(exp.age_at_event))
    setRowError(null)
  }

  async function saveEdit(exp: Experience) {
    const age = parseInt(editAge, 10)
    if (!editText.trim() || isNaN(age) || age < 0 || age > 120) return
    setBusyId(exp.id)
    setRowError(null)
    try {
      const updated = await api.updateExperience(params.id, exp.id, { user_description: editText.trim(), age_at_event: age })
      setTimeline((t) => (t ? { ...t, persona: updated } : t))
      await loadTimeline()
      setEditingId(null)
    } catch (err) {
      setRowError(err instanceof Error ? err.message : 'Failed to save changes')
    } finally {
      setBusyId(null)
    }
  }

  async function deleteExp(exp: Experience) {
    if (!confirm('Delete this experience? Their timeline will be replayed forward from what remains.')) return
    setBusyId(exp.id)
    setRowError(null)
    try {
      await api.deleteExperience(params.id, exp.id)
      await loadTimeline()
    } catch (err) {
      setRowError(err instanceof Error ? err.message : 'Failed to delete experience')
    } finally {
      setBusyId(null)
    }
  }

  /**
   * Swaps two same-age experiences' sequence_index. The backend rejects a
   * sequence_index already in use at that age (see
   * _ensure_sequence_available in experiences.py), so a direct A<->B PATCH
   * pair would collide on the first call. Route the neighbor through a
   * temporary index that's guaranteed unused at this age first.
   */
  async function moveExp(exp: Experience, direction: 'up' | 'down') {
    const siblings = experiencesAtAge
    const idx = siblings.findIndex((s) => s.id === exp.id)
    const neighborIdx = direction === 'up' ? idx - 1 : idx + 1
    if (neighborIdx < 0 || neighborIdx >= siblings.length) return
    const neighbor = siblings[neighborIdx]
    const tempIndex = Math.max(...siblings.map((s) => s.sequence_index)) + 1000

    setBusyId(exp.id)
    setRowError(null)
    try {
      await api.updateExperience(params.id, neighbor.id, { sequence_index: tempIndex })
      await api.updateExperience(params.id, exp.id, { sequence_index: neighbor.sequence_index })
      await api.updateExperience(params.id, neighbor.id, { sequence_index: exp.sequence_index })
      await loadTimeline()
    } catch (err) {
      setRowError(err instanceof Error ? err.message : 'Failed to reorder experiences')
      await loadTimeline()
    } finally {
      setBusyId(null)
    }
  }

  async function analyzeLife() {
    if (!persona || drafts.length === 0) return
    setView('analyzing')
    setAnalyzeError(null)
    setBeforePersona(persona)
    try {
      const result = await api.addExperiencesBatch(
        params.id,
        drafts.map((d) => ({ description: d.description, age_at_event: d.age }))
      )
      const failures = result.results
        .filter((r) => r.status === 'failed')
        .map((r) => ({ description: drafts[r.input_index]?.description ?? '(unknown)', error: r.error ?? 'Unknown error' }))
      setBatchFailures(failures)

      const refreshed = await api.getTimeline(params.id)
      setTimeline(refreshed)
      setAfterPersona(refreshed.persona)
      setDrafts((current) => retainUnprocessedDrafts(current, result.results))
      setView('reveal')
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : 'Analysis failed. Your drafts are still queued below.')
      setView('building')
    }
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
          <button type="button" className="rubix-btn-primary" style={{ marginTop: 18 }} onClick={loadTimeline}>
            Retry
          </button>
        </RubixCard>
      </div>
    )
  }

  return (
    <RubixShell persona={{ id: persona.id, name: persona.name }}>
      {view === 'analyzing' && <AnalyzingView count={drafts.length || batchFailures.length} />}

      {view === 'reveal' && beforePersona && afterPersona && (
        <ImpactRevealView
          personaName={persona.name}
          before={beforePersona}
          after={afterPersona}
          failures={batchFailures}
          onDone={() => router.push(`/persona/${persona.id}`)}
          onKeepBuilding={() => setView('building')}
        />
      )}

      {view === 'building' && (
        <div style={{ maxWidth: 1420 }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.025em' }}>Build {persona.name}&apos;s life</div>
              <div style={{ marginTop: 7, fontSize: 14, color: 'rgba(214,235,255,0.7)' }}>Chronological. Pick an age, then say what happened.</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: '8px 14px', borderRadius: 999, fontSize: 12.5, color: 'rgba(226,240,255,0.85)', background: 'rgba(255,255,255,0.09)', border: '1px solid rgba(170,210,255,0.22)' }}>
                {drafts.length} experience{drafts.length === 1 ? '' : 's'} ready to analyze
              </div>
              <button type="button" className="rubix-btn-primary" disabled={drafts.length === 0} aria-disabled={drafts.length === 0} onClick={analyzeLife}>
                Analyze life →
              </button>
            </div>
          </div>

          {analyzeError && (
            <div style={{ marginTop: 14, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
              {analyzeError}
            </div>
          )}

          {/* decades + ages */}
          <RubixCard variant="flat" style={{ marginTop: 22, padding: 16 }}>
            <div style={{ display: 'flex', gap: 9, overflowX: 'auto', paddingBottom: 2 }}>
              {decades.map((d) => {
                const active = d === decadeStart
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDecadeStart(d)}
                    style={{
                      flex: '0 0 auto', padding: '11px 17px', borderRadius: 14, cursor: 'pointer', textAlign: 'center', minWidth: 90,
                      background: active ? 'linear-gradient(160deg,#a8dcff,#5b9dff 50%,#3b78f4)' : 'rgba(255,255,255,0.07)',
                      border: `1px solid ${active ? 'rgba(200,230,255,0.5)' : 'rgba(170,210,255,0.2)'}`,
                      color: active ? '#03204d' : 'rgba(226,240,255,0.85)', fontWeight: 600, fontSize: 14,
                    }}
                  >
                    {d === 120 ? '120' : `${d}s`}
                  </button>
                )
              })}
            </div>
            <div style={{ marginTop: 16, paddingTop: 15, borderTop: '1px solid rgba(170,210,255,0.16)', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
              <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.1em', color: 'rgba(200,226,255,0.6)' }}>AGES</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {agesWithMarks.map(({ age, hasEvents, count }) => {
                  const active = age === selectedAge
                  return (
                    <button
                      key={age}
                      type="button"
                      onClick={() => selectAge(age)}
                      title={count ? `${count} experience${count === 1 ? '' : 's'}` : undefined}
                      style={{
                        position: 'relative', width: 46, height: 46, borderRadius: 14, cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        background: active ? 'linear-gradient(160deg,#a8dcff,#5b9dff 50%,#3b78f4)' : 'rgba(255,255,255,0.06)',
                        border: `1px solid ${active ? 'rgba(200,230,255,0.5)' : 'rgba(170,210,255,0.18)'}`,
                      }}
                    >
                      <div style={{ fontSize: 14.5, fontWeight: 600, color: active ? '#03204d' : 'rgba(226,240,255,0.9)' }}>{age}</div>
                      <div style={{ marginTop: 3, width: 5, height: 5, borderRadius: 999, background: hasEvents ? (active ? '#03204d' : '#7fe3ff') : 'transparent', boxShadow: hasEvents ? '0 0 6px #7fe3ff' : 'none' }} />
                    </button>
                  )
                })}
              </div>
            </div>
          </RubixCard>

          <div className="rubix-grid-with-rail" style={{ marginTop: 20, display: 'grid', gap: 20, alignItems: 'start' }}>
            {/* age workspace */}
            <RubixCard variant="hero" style={{ padding: 26, minWidth: 0 }}>
              <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.1em', color: 'rgba(200,226,255,0.62)' }}>
                {decadeStart != null ? `${decadeStart}S` : ''}
              </div>
              <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 12 }}>
                <div style={{ fontSize: 36, fontWeight: 700, letterSpacing: '-0.03em' }}>Age {selectedAge}</div>
                <div style={{ fontSize: 14, color: 'rgba(214,235,255,0.68)' }}>
                  {experiencesAtAge.length} analyzed · {draftsAtAge.length} queued
                </div>
              </div>

              {rowError && (
                <div style={{ marginTop: 14, padding: '10px 13px', borderRadius: 12, fontSize: 12.5, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
                  {rowError}
                </div>
              )}

              <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 11 }}>
                {experiencesAtAge.map((exp, i) => (
                  <div key={exp.id} style={{ padding: 16, borderRadius: 18, background: 'linear-gradient(165deg, rgba(255,255,255,0.13), rgba(255,255,255,0.05))', border: '1px solid rgba(170,210,255,0.2)' }}>
                    {editingId === exp.id ? (
                      <div>
                        <textarea className="rubix-textarea" style={{ width: '100%', minHeight: 90 }} value={editText} onChange={(e) => setEditText(e.target.value)} />
                        <div style={{ marginTop: 10, display: 'flex', gap: 10, alignItems: 'center' }}>
                          <div>
                            <label className="rubix-field-label" htmlFor={`edit-age-${exp.id}`}>AGE</label>
                            <input id={`edit-age-${exp.id}`} type="number" min={0} max={120} className="rubix-input" style={{ width: 90, marginTop: 6 }} value={editAge} onChange={(e) => setEditAge(e.target.value)} />
                          </div>
                          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                            <button type="button" className="rubix-btn-ghost" onClick={() => setEditingId(null)} disabled={busyId === exp.id}>Cancel</button>
                            <button type="button" className="rubix-btn-primary" onClick={() => saveEdit(exp)} disabled={busyId === exp.id}>
                              {busyId === exp.id ? 'Saving…' : 'Save'}
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: 14 }}>
                        <div style={{ width: 26, height: 26, borderRadius: 9, flex: '0 0 26px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12.5, fontWeight: 700, color: '#04214c', background: 'linear-gradient(160deg,#cfe9ff,#7fb2ff)' }}>
                          {i + 1}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 14, lineHeight: 1.6, color: 'rgba(232,243,255,0.94)' }}>{exp.user_description}</div>
                          {exp.interpretation?.adaptation_strategy && (
                            <div style={{ marginTop: 6, fontSize: 12, color: 'rgba(200,226,255,0.55)' }}>{titleCase(exp.interpretation.adaptation_strategy)}</div>
                          )}
                          <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            <button type="button" className="rubix-btn-ghost" style={{ padding: '7px 13px', fontSize: 12 }} onClick={() => startEdit(exp)} disabled={busyId === exp.id}>Edit</button>
                            <button type="button" className="rubix-btn-ghost" style={{ padding: '7px 13px', fontSize: 12 }} onClick={() => moveExp(exp, 'up')} disabled={busyId === exp.id || i === 0}>Move up</button>
                            <button type="button" className="rubix-btn-ghost" style={{ padding: '7px 13px', fontSize: 12 }} onClick={() => moveExp(exp, 'down')} disabled={busyId === exp.id || i === experiencesAtAge.length - 1}>Move down</button>
                            <button type="button" className="rubix-btn-danger" style={{ padding: '7px 13px', fontSize: 12 }} onClick={() => deleteExp(exp)} disabled={busyId === exp.id}>
                              {busyId === exp.id ? 'Working…' : 'Delete'}
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {draftsAtAge.map((d) => (
                  <div key={d.localId} style={{ display: 'flex', gap: 14, padding: 16, borderRadius: 18, border: '1px dashed rgba(175,212,255,0.35)', background: 'rgba(255,255,255,0.04)' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                        <RubixBadge tone="muted">not yet analyzed</RubixBadge>
                      </div>
                      <div style={{ marginTop: 8, fontSize: 14, lineHeight: 1.6, color: 'rgba(232,243,255,0.9)' }}>{d.description}</div>
                      <div style={{ marginTop: 10 }}>
                        <button type="button" className="rubix-btn-ghost" style={{ padding: '7px 13px', fontSize: 12 }} onClick={() => removeDraft(d.localId)}>Remove</button>
                      </div>
                    </div>
                  </div>
                ))}

                {experiencesAtAge.length === 0 && draftsAtAge.length === 0 && (
                  <div style={{ padding: 26, borderRadius: 18, textAlign: 'center', border: '1px dashed rgba(175,212,255,0.35)', background: 'rgba(255,255,255,0.05)' }}>
                    <div style={{ fontSize: 15, fontWeight: 600 }}>Nothing happened here yet</div>
                    <div style={{ marginTop: 8, fontSize: 13.5, color: 'rgba(216,236,255,0.7)' }}>Add what this year did to them — or pick another age.</div>
                  </div>
                )}
              </div>

              {/* composer */}
              <div style={{ marginTop: 18, padding: 18, borderRadius: 20, background: 'linear-gradient(165deg, rgba(255,255,255,0.10), rgba(255,255,255,0.03))', border: '1px solid rgba(175,212,255,0.24)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.1em', color: 'rgba(200,226,255,0.62)' }}>STAGE AN EXPERIENCE AT AGE {selectedAge}</div>
                <div style={{ marginTop: 6, fontSize: 12.5, color: 'rgba(210,232,255,0.62)' }}>This joins the life queue and will not be analyzed until you choose Analyze life.</div>
                <div style={{ marginTop: 13, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <input
                    className="rubix-input"
                    style={{ flex: 1, minWidth: 240 }}
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') addDraft() }}
                    placeholder="e.g. Her partner betrays her trust"
                  />
                  <button type="button" className="rubix-btn-primary" onClick={addDraft} disabled={!draftText.trim()}>
                    Add to life
                  </button>
                </div>
              </div>
            </RubixCard>

            {/* right rail */}
            <div style={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
              <RubixCard style={{ padding: 22 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
                  <div style={{ fontSize: 15.5, fontWeight: 600 }}>Life queue</div>
                  <RubixBadge tone={drafts.length ? 'violet' : 'muted'}>{drafts.length} queued</RubixBadge>
                </div>
                <div style={{ marginTop: 6, fontSize: 12.5, lineHeight: 1.5, color: 'rgba(210,232,255,0.65)' }}>
                  Unprocessed experiences from across their lifespan. Analyze life processes this whole ledger chronologically.
                </div>
                {sortedDrafts.length === 0 ? (
                  <div style={{ marginTop: 16, padding: '16px 12px', textAlign: 'center', borderRadius: 14, border: '1px dashed rgba(175,212,255,0.26)', color: 'rgba(210,232,255,0.55)', fontSize: 12.5 }}>
                    No experiences waiting to be analyzed.
                  </div>
                ) : (
                  <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {sortedDrafts.map((draft) => (
                      <div key={draft.localId} style={{ padding: 12, borderRadius: 14, background: 'rgba(255,255,255,0.045)', border: '1px dashed rgba(175,212,255,0.3)' }}>
                        {draftEditingId === draft.localId ? (
                          <div>
                            <textarea className="rubix-textarea" style={{ width: '100%', minHeight: 72, fontSize: 12.5 }} value={draftEditText} onChange={(event) => setDraftEditText(event.target.value)} />
                            <div style={{ marginTop: 8, display: 'flex', alignItems: 'flex-end', gap: 8 }}>
                              <label className="rubix-field-label" htmlFor={`draft-age-${draft.localId}`}>
                                AGE
                                <input id={`draft-age-${draft.localId}`} type="number" min={0} max={120} className="rubix-input" style={{ display: 'block', width: 70, marginTop: 5 }} value={draftEditAge} onChange={(event) => setDraftEditAge(event.target.value)} />
                              </label>
                              <button type="button" className="rubix-btn-ghost" style={{ marginLeft: 'auto', padding: '7px 10px', fontSize: 11.5 }} onClick={() => setDraftEditingId(null)}>Cancel</button>
                              <button type="button" className="rubix-btn-primary" style={{ padding: '7px 10px', fontSize: 11.5 }} onClick={() => saveDraftEdit(draft.localId)}>Save</button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                              <div style={{ flex: '0 0 42px', fontSize: 11.5, fontWeight: 700, color: 'rgba(205,232,255,0.75)' }}>AGE {draft.age}</div>
                              <div style={{ minWidth: 0, fontSize: 12.5, lineHeight: 1.5, color: 'rgba(232,243,255,0.9)' }}>{draft.description}</div>
                            </div>
                            <div style={{ marginTop: 8, display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                              <button type="button" className="rubix-btn-ghost" style={{ padding: '5px 9px', fontSize: 11 }} onClick={() => startDraftEdit(draft)}>Edit</button>
                              <button type="button" className="rubix-btn-ghost" style={{ padding: '5px 9px', fontSize: 11 }} onClick={() => removeDraft(draft.localId)}>Remove</button>
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </RubixCard>
              <RubixCard style={{ padding: 22 }}>
                <div style={{ fontSize: 15.5, fontWeight: 600 }}>Life density</div>
                <div style={{ marginTop: 6, fontSize: 12.5, color: 'rgba(210,232,255,0.65)' }}>Where this life is thick and where it&apos;s thin.</div>
                <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 11 }}>
                  {density.map((d) => (
                    <div key={d.decade} style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                      <div style={{ flex: '0 0 44px', fontSize: 12.5, color: 'rgba(226,240,255,0.85)' }}>{d.decade === 120 ? '120' : `${d.decade}s`}</div>
                      <div className="rubix-meter-track" style={{ flex: 1 }}>
                        <div className="rubix-meter-fill" style={{ width: `${d.percent}%`, background: 'linear-gradient(90deg, rgba(125,225,255,0.85), rgba(95,155,255,0.95))', boxShadow: '0 0 10px rgba(110,190,255,0.5)' }} />
                      </div>
                      <div style={{ flex: '0 0 20px', textAlign: 'right', fontSize: 12, color: 'rgba(210,232,255,0.6)' }}>{d.count}</div>
                    </div>
                  ))}
                </div>
              </RubixCard>
            </div>
          </div>
        </div>
      )}
    </RubixShell>
  )
}

function AnalyzingView({ count }: { count: number }) {
  return (
    <div style={{ maxWidth: 900, margin: '6vh auto 0', textAlign: 'center' }}>
      <div style={{ position: 'relative', width: 130, height: 130, margin: '0 auto' }}>
        <div aria-hidden="true" style={{ position: 'absolute', inset: -34, filter: 'blur(30px)', opacity: 0.75, animation: 'rubixPulse 4.5s ease-in-out infinite', background: 'radial-gradient(50% 50% at 50% 50%, rgba(150,205,255,0.8) 0%, rgba(150,205,255,0) 70%)' }} />
        <div aria-hidden="true" style={{ position: 'absolute', inset: 18, borderRadius: 28, transform: 'rotate(45deg)', animation: 'rubixFloat 6s ease-in-out infinite', background: 'linear-gradient(150deg, rgba(215,242,255,0.95), rgba(110,170,255,0.92) 50%, rgba(60,105,235,0.92))', boxShadow: '0 0 50px rgba(130,200,255,0.6), inset 0 3px 0 rgba(255,255,255,0.8)' }} />
      </div>
      <div style={{ marginTop: 30, fontSize: 30, fontWeight: 700, letterSpacing: '-0.03em' }}>Analyzing their life</div>
      <div style={{ marginTop: 12, fontSize: 15.5, lineHeight: 1.6, color: 'rgba(224,240,255,0.82)' }}>
        Processing {count} experience{count === 1 ? '' : 's'} chronologically…
      </div>
      <div style={{ position: 'relative', maxWidth: 460, margin: '26px auto 0', height: 5, borderRadius: 999, overflow: 'hidden', background: 'rgba(8,28,74,0.42)' }}>
        <div aria-hidden="true" style={{ position: 'absolute', top: 0, bottom: 0, width: '38%', borderRadius: 999, background: 'linear-gradient(90deg, rgba(120,220,255,0), rgba(140,210,255,0.95), rgba(120,220,255,0))', animation: 'rubixSweep 2.4s ease-in-out infinite' }} />
      </div>
      <div role="status" aria-live="polite" style={{ marginTop: 14, fontSize: 12.5, color: 'rgba(205,230,255,0.6)' }}>
        This can take a little while — each experience is analyzed in order, since later ones depend on what came before.
      </div>
    </div>
  )
}

interface DeltaRow {
  key: string
  label: string
  text: string
  tone: 'positive' | 'negative' | 'neutral'
}

function ImpactRevealView({
  personaName, before, after, failures, onDone, onKeepBuilding,
}: {
  personaName: string
  before: Persona
  after: Persona
  failures: { description: string; error: string }[]
  onDone: () => void
  onKeepBuilding: () => void
}) {
  const personalityRows: DeltaRow[] = (Object.keys(before.current_personality) as (keyof PersonalityTraits)[])
    .map((key) => {
      const delta = after.current_personality[key] - before.current_personality[key]
      return { key, delta }
    })
    .filter((d) => Math.abs(d.delta) >= 0.02)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .map((d) => ({
      key: d.key,
      label: BIG_FIVE_LABELS[d.key],
      text: `${d.delta > 0 ? '+' : ''}${Math.round(d.delta * 100)} pts`,
      tone: d.key === 'neuroticism' ? (d.delta < 0 ? 'positive' : 'negative') : 'neutral',
    }))

  const beforeState = before.current_state || {}
  const afterState = after.current_state || {}
  const stateKeys = Array.from(new Set([...Object.keys(beforeState), ...Object.keys(afterState)])).filter((k) => STATE_DIMENSIONS[k])
  const stateRows: DeltaRow[] = stateKeys
    .map((key) => {
      const meta = STATE_DIMENSIONS[key]
      const b = beforeState[key]
      const a = afterState[key]
      if (a === undefined) return null
      const bVal = b ?? STATE_NEUTRAL
      const delta = a - bVal
      if (Math.abs(delta) < STATE_NOTABLE_DELTA && b !== undefined) return null
      const isAdverse = meta.adverseWhen === 'high' ? delta > 0 : delta < 0
      return {
        key,
        label: meta.label,
        text: b === undefined ? `newly ${delta > 0 ? meta.highLabel.toLowerCase() : meta.lowLabel.toLowerCase()}` : delta > 0 ? meta.highLabel : meta.lowLabel,
        tone: isAdverse ? 'negative' : 'positive',
      } as DeltaRow
    })
    .filter((r): r is DeltaRow => r !== null)

  const attachmentChanged = before.current_attachment_style !== after.current_attachment_style
  const patternChanges = comparePatternTrajectories(before.adaptation_patterns, after.adaptation_patterns)
  const newHypotheses = (after.clinical_pattern_hypotheses || []).filter(
    (h) => !(before.clinical_pattern_hypotheses || []).some((bh) => bh.pattern_key === h.pattern_key)
  )

  const hasAnyChange = personalityRows.length > 0 || stateRows.length > 0 || attachmentChanged || patternChanges.length > 0 || newHypotheses.length > 0

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', padding: '10px 0 6px' }}>
        <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.14em', color: 'rgba(200,226,255,0.6)' }}>IMPACT REVEAL</div>
        <div style={{ marginTop: 12, fontSize: 30, fontWeight: 700, letterSpacing: '-0.03em' }}>What these experiences did to {personaName}</div>
      </div>

      {failures.length > 0 && (
        <RubixCard style={{ marginTop: 24, padding: 20, borderColor: 'rgba(255,150,135,0.3)' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,210,200,0.95)' }}>
            {failures.length} experience{failures.length === 1 ? '' : 's'} couldn&apos;t be processed
          </div>
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {failures.map((f, i) => (
              <div key={i} style={{ fontSize: 12.5, color: 'rgba(224,239,255,0.8)' }}>
                &ldquo;{f.description.slice(0, 80)}{f.description.length > 80 ? '…' : ''}&rdquo; — {f.error}
              </div>
            ))}
          </div>
        </RubixCard>
      )}

      <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 14 }}>
        {personalityRows.length > 0 && (
          <RevealStage label="PERSONALITY" headline="How they think and feel shifted">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {personalityRows.map((r) => (
                <RubixDelta key={r.key} label={`${r.label} ${r.text}`} tone={r.tone} />
              ))}
            </div>
          </RevealStage>
        )}

        {stateRows.length > 0 && (
          <RevealStage label="RIGHT NOW" headline="What they're navigating changed">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {stateRows.map((r) => (
                <div key={r.key} style={{ fontSize: 14, color: 'rgba(224,239,255,0.85)' }}>
                  <strong>{r.label}:</strong> {r.text}
                </div>
              ))}
            </div>
          </RevealStage>
        )}

        {attachmentChanged && (
          <RevealStage label="ATTACHMENT" headline="Their attachment style moved">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14 }}>
              <RubixBadge tone={attachmentStyleTone(before.current_attachment_style)}>{attachmentStyleLabel(before.current_attachment_style)}</RubixBadge>
              <span style={{ color: 'rgba(214,235,255,0.6)' }}>→</span>
              <RubixBadge tone={attachmentStyleTone(after.current_attachment_style)}>{attachmentStyleLabel(after.current_attachment_style)}</RubixBadge>
            </div>
          </RevealStage>
        )}

        {patternChanges.map((change) => {
          const copy = PATTERN_TRAJECTORY_COPY[change.kind]
          const tone = change.kind === 'emerged' || change.kind === 'strengthened' ? 'violet' : 'muted'
          return (
            <RevealStage key={`${change.kind}-${change.pattern.pattern_name}`} label={copy.label} headline={copy.headline}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                <RubixBadge tone={tone}>{change.pattern.pattern_name}</RubixBadge>
              </div>
            </RevealStage>
          )
        })}

        {newHypotheses.length > 0 && (
          <RevealStage label="BEING CONSIDERED" headline="New patterns are being considered">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {newHypotheses.map((h) => (
                <RubixBadge key={h.pattern_key} tone="muted">{titleCase(h.pattern_key)}</RubixBadge>
              ))}
            </div>
          </RevealStage>
        )}

        {!hasAnyChange && (
          <RubixCard style={{ padding: 24, textAlign: 'center' }}>
            <div style={{ fontSize: 14.5, color: 'rgba(224,239,255,0.8)' }}>
              These experiences were recorded, but nothing crossed the threshold to show as a meaningful shift yet.
            </div>
          </RubixCard>
        )}
      </div>

      <div style={{ textAlign: 'center', marginTop: 30, display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button type="button" className="rubix-btn-ghost" onClick={onKeepBuilding}>Keep building</button>
        <button type="button" className="rubix-btn-primary" style={{ padding: '15px 34px', fontSize: 15.5 }} onClick={onDone}>
          Enter their life
        </button>
      </div>
    </div>
  )
}

function RevealStage({ label, headline, children }: { label: string; headline: string; children: React.ReactNode }) {
  return (
    <RubixCard style={{ padding: '22px 24px' }}>
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div style={{ flex: '0 0 150px', fontSize: 11.5, fontWeight: 700, letterSpacing: '0.11em', color: 'rgba(150,210,255,0.85)' }}>{label}</div>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.4 }}>{headline}</div>
          <div style={{ marginTop: 10 }}>{children}</div>
        </div>
      </div>
    </RubixCard>
  )
}
