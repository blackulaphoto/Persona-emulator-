import type { Persona } from '@/lib/api'
import { consumePostAnalysisSummary, postAnalysisChangeLabels, postAnalysisStorageKey, savePostAnalysisSummary } from './postAnalysis'

function persona(overrides: Partial<Persona> = {}): Persona {
  return {
    id: 'persona-1',
    name: 'Elena',
    current_personality: { openness: 0.5, conscientiousness: 0.5, extraversion: 0.5, agreeableness: 0.5, neuroticism: 0.5 },
    current_state: { trust: 0.5 },
    current_attachment_style: 'secure',
    adaptation_patterns: [],
    clinical_pattern_hypotheses: [],
    ...overrides,
  } as Persona
}

describe('post-analysis dashboard handoff', () => {
  beforeEach(() => window.sessionStorage.clear())

  it('is persona scoped and consumed only once', () => {
    const before = persona()
    const after = persona({ current_attachment_style: 'anxious' })
    savePostAnalysisSummary({ personaId: 'persona-1', analyzedCount: 3, before, after, failures: [] })

    expect(consumePostAnalysisSummary('another-persona')).toBeNull()
    expect(consumePostAnalysisSummary('persona-1')?.analyzedCount).toBe(3)
    expect(consumePostAnalysisSummary('persona-1')).toBeNull()
  })

  it('returns no summary for a direct dashboard load', () => {
    expect(consumePostAnalysisSummary('persona-1')).toBeNull()
    expect(window.sessionStorage.getItem(postAnalysisStorageKey('persona-1'))).toBeNull()
  })

  it('derives concise labels only from existing before-and-after data', () => {
    const before = persona()
    const after = persona({
      current_personality: { ...before.current_personality, openness: 0.55 },
      current_attachment_style: 'anxious',
      clinical_pattern_hypotheses: [{ pattern_key: 'self_reliance' } as NonNullable<Persona['clinical_pattern_hypotheses']>[number]],
    })

    expect(postAnalysisChangeLabels(before, after)).toEqual([
      'Personality shifted',
      'Attachment changed',
      'New patterns considered',
    ])
  })
})
