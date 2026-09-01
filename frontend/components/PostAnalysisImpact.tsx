'use client'

import { RubixBadge, RubixCard, RubixDelta } from '@/components/rubix'
import type { Persona, PersonalityTraits } from '@/lib/api'
import { attachmentStyleLabel, attachmentStyleTone } from '@/lib/rubix/attachmentStyle'
import { STATE_DIMENSIONS, STATE_NEUTRAL, STATE_NOTABLE_DELTA, titleCase } from '@/lib/rubix/stateDimensions'
import { comparePatternTrajectories, PATTERN_TRAJECTORY_COPY } from '@/lib/patternTrajectory'

const BIG_FIVE_LABELS: Record<keyof PersonalityTraits, string> = {
  openness: 'Openness', conscientiousness: 'Conscientiousness', extraversion: 'Extraversion',
  agreeableness: 'Agreeableness', neuroticism: 'Neuroticism',
}

interface DeltaRow {
  key: string
  label: string
  text: string
  tone: 'positive' | 'negative' | 'neutral'
}

export function PostAnalysisImpact({ before, after, failures = [] }: {
  before: Persona
  after: Persona
  failures?: { description: string; error: string }[]
}) {
  const personalityRows: DeltaRow[] = (Object.keys(before.current_personality) as (keyof PersonalityTraits)[])
    .map((key) => ({ key, delta: after.current_personality[key] - before.current_personality[key] }))
    .filter(({ delta }) => Math.abs(delta) >= 0.02)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .map(({ key, delta }) => ({
      key, label: BIG_FIVE_LABELS[key], text: `${delta > 0 ? '+' : ''}${Math.round(delta * 100)} pts`,
      tone: key === 'neuroticism' ? (delta < 0 ? 'positive' : 'negative') : 'neutral',
    }))

  const beforeState = before.current_state || {}
  const afterState = after.current_state || {}
  const stateRows: DeltaRow[] = Array.from(new Set([...Object.keys(beforeState), ...Object.keys(afterState)]))
    .filter((key) => STATE_DIMENSIONS[key])
    .map((key) => {
      const meta = STATE_DIMENSIONS[key]
      const previous = beforeState[key]
      const current = afterState[key]
      if (current === undefined) return null
      const delta = current - (previous ?? STATE_NEUTRAL)
      if (Math.abs(delta) < STATE_NOTABLE_DELTA && previous !== undefined) return null
      const isAdverse = meta.adverseWhen === 'high' ? delta > 0 : delta < 0
      return {
        key, label: meta.label,
        text: previous === undefined ? `newly ${delta > 0 ? meta.highLabel.toLowerCase() : meta.lowLabel.toLowerCase()}` : delta > 0 ? meta.highLabel : meta.lowLabel,
        tone: isAdverse ? 'negative' : 'positive',
      } as DeltaRow
    })
    .filter((row): row is DeltaRow => row !== null)

  const attachmentChanged = before.current_attachment_style !== after.current_attachment_style
  const patternChanges = comparePatternTrajectories(before.adaptation_patterns, after.adaptation_patterns)
  const newHypotheses = (after.clinical_pattern_hypotheses || []).filter(
    (hypothesis) => !(before.clinical_pattern_hypotheses || []).some((previous) => previous.pattern_key === hypothesis.pattern_key)
  )
  const hasAnyChange = personalityRows.length > 0 || stateRows.length > 0 || attachmentChanged || patternChanges.length > 0 || newHypotheses.length > 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {failures.length > 0 && (
        <RubixCard style={{ padding: 20, borderColor: 'rgba(255,150,135,0.3)' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,210,200,0.95)' }}>
            {failures.length} experience{failures.length === 1 ? '' : 's'} couldn&apos;t be processed
          </div>
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {failures.map((failure, index) => (
              <div key={`${failure.description}-${index}`} style={{ fontSize: 12.5, color: 'rgba(224,239,255,0.8)' }}>
                &ldquo;{failure.description.slice(0, 80)}{failure.description.length > 80 ? '…' : ''}&rdquo; — {failure.error}
              </div>
            ))}
          </div>
        </RubixCard>
      )}
      {personalityRows.length > 0 && <RevealStage label="PERSONALITY" headline="How they think and feel shifted"><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>{personalityRows.map((row) => <RubixDelta key={row.key} label={`${row.label} ${row.text}`} tone={row.tone} />)}</div></RevealStage>}
      {stateRows.length > 0 && <RevealStage label="RIGHT NOW" headline="What they're navigating changed"><div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>{stateRows.map((row) => <div key={row.key} style={{ fontSize: 14, color: 'rgba(224,239,255,0.85)' }}><strong>{row.label}:</strong> {row.text}</div>)}</div></RevealStage>}
      {attachmentChanged && <RevealStage label="ATTACHMENT" headline="Their attachment style moved"><div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14 }}><RubixBadge tone={attachmentStyleTone(before.current_attachment_style)}>{attachmentStyleLabel(before.current_attachment_style)}</RubixBadge><span style={{ color: 'rgba(214,235,255,0.6)' }}>→</span><RubixBadge tone={attachmentStyleTone(after.current_attachment_style)}>{attachmentStyleLabel(after.current_attachment_style)}</RubixBadge></div></RevealStage>}
      {patternChanges.map((change) => { const copy = PATTERN_TRAJECTORY_COPY[change.kind]; return <RevealStage key={`${change.kind}-${change.pattern.pattern_name}`} label={copy.label} headline={copy.headline}><RubixBadge tone={change.kind === 'emerged' || change.kind === 'strengthened' ? 'violet' : 'muted'}>{change.pattern.pattern_name}</RubixBadge></RevealStage> })}
      {newHypotheses.length > 0 && <RevealStage label="BEING CONSIDERED" headline="New patterns are being considered"><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>{newHypotheses.map((hypothesis) => <RubixBadge key={hypothesis.pattern_key} tone="muted">{titleCase(hypothesis.pattern_key)}</RubixBadge>)}</div></RevealStage>}
      {!hasAnyChange && <RubixCard style={{ padding: 24, textAlign: 'center' }}><div style={{ fontSize: 14.5, color: 'rgba(224,239,255,0.8)' }}>These experiences were recorded, but nothing crossed the threshold to show as a meaningful shift yet.</div></RubixCard>}
    </div>
  )
}

function RevealStage({ label, headline, children }: { label: string; headline: string; children: React.ReactNode }) {
  return <RubixCard style={{ padding: '22px 24px' }}><div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}><div style={{ flex: '0 0 150px', fontSize: 11.5, fontWeight: 700, letterSpacing: '0.11em', color: 'rgba(150,210,255,0.85)' }}>{label}</div><div style={{ flex: 1, minWidth: 220 }}><div style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.4 }}>{headline}</div><div style={{ marginTop: 10 }}>{children}</div></div></div></RubixCard>
}
