import { titleCase } from '../stateDimensions'

// Regression guard for a real bug found during manual QA: the Starting
// Conditions drawer showed "CaregiverReliability" verbatim because
// foundational_environment_signals uses camelCase keys, unlike the rest of
// the engine's snake_case vocabulary (pattern_key, adaptation_strategy, ...).
describe('titleCase', () => {
  it('title-cases snake_case keys (the engine\'s primary vocabulary)', () => {
    expect(titleCase('adaptation_strategy')).toBe('Adaptation Strategy')
    expect(titleCase('pattern_key')).toBe('Pattern Key')
  })

  it('title-cases camelCase keys (foundational_environment_signals)', () => {
    expect(titleCase('caregiverReliability')).toBe('Caregiver Reliability')
    expect(titleCase('emotionalSafety')).toBe('Emotional Safety')
    expect(titleCase('threatExposure')).toBe('Threat Exposure')
  })

  it('leaves an already-plain word alone', () => {
    expect(titleCase('stability')).toBe('Stability')
  })
})
