import type { Persona } from '@/lib/api'
import { STATE_DIMENSIONS, STATE_NEUTRAL, STATE_NOTABLE_DELTA } from '@/lib/rubix/stateDimensions'
import { comparePatternTrajectories } from '@/lib/patternTrajectory'

export interface PostAnalysisSummary {
  personaId: string
  analyzedCount: number
  before: Persona
  after: Persona
  failures: { description: string; error: string }[]
}

const STORAGE_PREFIX = 'rubicks:post-analysis:'

export function postAnalysisStorageKey(personaId: string): string {
  return `${STORAGE_PREFIX}${personaId}`
}

export function savePostAnalysisSummary(summary: PostAnalysisSummary): void {
  try {
    window.sessionStorage.setItem(postAnalysisStorageKey(summary.personaId), JSON.stringify(summary))
  } catch {
    // The analysis result remains persisted by the API; optional insight must
    // never block navigation when browser storage is unavailable.
  }
}

export function consumePostAnalysisSummary(personaId: string): PostAnalysisSummary | null {
  const key = postAnalysisStorageKey(personaId)
  const raw = window.sessionStorage.getItem(key)
  if (!raw) return null

  window.sessionStorage.removeItem(key)
  try {
    const parsed = JSON.parse(raw) as PostAnalysisSummary
    if (parsed.personaId !== personaId || !parsed.before || !parsed.after || !Number.isInteger(parsed.analyzedCount)) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function postAnalysisChangeLabels(before: Persona, after: Persona): string[] {
  const labels: string[] = []
  const personalityShifted = Object.keys(before.current_personality).some((key) => {
    const trait = key as keyof Persona['current_personality']
    return Math.abs(after.current_personality[trait] - before.current_personality[trait]) >= 0.02
  })
  if (personalityShifted) labels.push('Personality shifted')

  const beforeState = before.current_state || {}
  const afterState = after.current_state || {}
  const stateShifted = Object.keys(afterState).some((key) => {
    if (!STATE_DIMENSIONS[key]) return false
    const previous = beforeState[key]
    return previous === undefined || Math.abs(afterState[key] - (previous ?? STATE_NEUTRAL)) >= STATE_NOTABLE_DELTA
  })
  if (stateShifted) labels.push('Current state changed')
  if (before.current_attachment_style !== after.current_attachment_style) labels.push('Attachment changed')
  if (comparePatternTrajectories(before.adaptation_patterns, after.adaptation_patterns).length > 0) labels.push('Coping patterns changed')

  const newHypothesis = (after.clinical_pattern_hypotheses || []).some(
    (hypothesis) => !(before.clinical_pattern_hypotheses || []).some((previous) => previous.pattern_key === hypothesis.pattern_key)
  )
  if (newHypothesis) labels.push('New patterns considered')
  return labels
}
