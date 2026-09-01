import { comparePatternTrajectories, isPatternActive } from './patternTrajectory'
import type { AdaptationPattern } from './api'

function pattern(overrides: Partial<AdaptationPattern> = {}): AdaptationPattern {
  return {
    adaptation_strategy: 'self_reliance',
    pattern_name: 'Self Reliance Response',
    status: 'emerging',
    evidence_strength: 0.2,
    confidence: 20,
    first_emerged_age: 5,
    reinforcement_history: [],
    ...overrides,
  }
}

describe('pattern trajectory comparison', () => {
  test('reports an actually active new pattern as emerged', () => {
    expect(comparePatternTrajectories([], [pattern()])[0].kind).toBe('emerged')
  })

  test('does not call a new but finally resolved pattern active', () => {
    const after = pattern({
      status: 'resolved',
      evidence_strength: 0,
      reinforcement_history: [
        { age: 5, effect: 'originated' },
        { age: 18, effect: 'weakened' },
      ],
    })
    expect(comparePatternTrajectories([], [after])[0].kind).toBe('emerged_then_resolved')
    expect(isPatternActive(after)).toBe(false)
  })

  test('reports an existing pattern resolving', () => {
    const before = pattern({ status: 'established', evidence_strength: 0.6 })
    const after = pattern({ status: 'resolved', evidence_strength: 0 })
    expect(comparePatternTrajectories([before], [after])[0].kind).toBe('resolved')
  })

  test('does not fabricate within-batch emergence without history evidence', () => {
    const after = pattern({ status: 'resolved', evidence_strength: 0, reinforcement_history: [] })
    expect(comparePatternTrajectories([], [after])[0].kind).toBe('resolved')
  })

  test('reports existing strength movement in both directions', () => {
    const before = pattern({ status: 'established', evidence_strength: 0.6 })
    expect(comparePatternTrajectories([before], [pattern({ status: 'established', evidence_strength: 0.8 })])[0].kind).toBe('strengthened')
    expect(comparePatternTrajectories([before], [pattern({ status: 'weakening', evidence_strength: 0.4 })])[0].kind).toBe('weakened')
  })
})
