import type { AdaptationPattern } from '@/lib/api'

export type PatternTrajectoryKind =
  | 'emerged'
  | 'strengthened'
  | 'weakened'
  | 'resolved'
  | 'emerged_then_weakened'
  | 'emerged_then_resolved'

export interface PatternTrajectoryChange {
  kind: PatternTrajectoryKind
  pattern: AdaptationPattern
  previous?: AdaptationPattern
}

function patternKey(pattern: AdaptationPattern): string {
  return pattern.adaptation_strategy || pattern.pattern_name
}

function strength(pattern: AdaptationPattern): number {
  return pattern.evidence_strength ?? 0
}

export function isPatternActive(pattern: AdaptationPattern): boolean {
  return pattern.status !== 'resolved' && pattern.status !== 'weakening' && pattern.evidence_strength !== 0
}

export function comparePatternTrajectories(
  before: AdaptationPattern[] = [],
  after: AdaptationPattern[] = []
): PatternTrajectoryChange[] {
  const beforeByKey = new Map(before.map((pattern) => [patternKey(pattern), pattern]))

  return after.flatMap((pattern): PatternTrajectoryChange[] => {
    const previous = beforeByKey.get(patternKey(pattern))

    if (!previous) {
      if (pattern.status === 'resolved' || strength(pattern) === 0) {
        const historyProvesEmergence = pattern.reinforcement_history.some((entry) =>
          entry.effect === 'originated' || entry.effect === 'created'
        )
        return [{ kind: historyProvesEmergence ? 'emerged_then_resolved' : 'resolved', pattern }]
      }
      if (pattern.status === 'weakening') {
        return [{ kind: 'emerged_then_weakened', pattern }]
      }
      return isPatternActive(pattern) ? [{ kind: 'emerged', pattern }] : []
    }

    if (pattern.status === 'resolved' && previous.status !== 'resolved') {
      return [{ kind: 'resolved', pattern, previous }]
    }
    if (
      pattern.status === 'weakening' ||
      (strength(pattern) < strength(previous) && pattern.status !== 'resolved')
    ) {
      return [{ kind: 'weakened', pattern, previous }]
    }
    if (
      strength(pattern) > strength(previous) ||
      (previous.status === 'emerging' && pattern.status === 'established')
    ) {
      return [{ kind: 'strengthened', pattern, previous }]
    }
    return []
  })
}

export const PATTERN_TRAJECTORY_COPY: Record<PatternTrajectoryKind, { label: string; headline: string }> = {
  emerged: { label: 'NEW PATTERN', headline: 'A new coping pattern emerged' },
  strengthened: { label: 'PATTERN STRENGTHENED', headline: 'A coping pattern strengthened' },
  weakened: { label: 'PATTERN WEAKENED', headline: 'A coping pattern weakened' },
  resolved: { label: 'PATTERN RESOLVED', headline: 'A coping pattern resolved' },
  emerged_then_weakened: { label: 'PATTERN TRAJECTORY', headline: 'A coping pattern emerged and was later weakened' },
  emerged_then_resolved: { label: 'PATTERN TRAJECTORY', headline: 'A coping pattern emerged and was later resolved' },
}
