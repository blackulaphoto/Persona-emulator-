export interface LifeDraft {
  localId: string
  age: number
  description: string
}

export const LIFESPAN_DECADES = Array.from({ length: 13 }, (_, index) => index * 10)

export function agesForDecade(decadeStart: number): number[] {
  if (decadeStart === 120) return [120]
  return Array.from({ length: 10 }, (_, index) => decadeStart + index)
}

export function sortLifeDrafts(drafts: LifeDraft[]): LifeDraft[] {
  return [...drafts].sort((a, b) => a.age - b.age || a.localId.localeCompare(b.localId))
}

export function retainUnprocessedDrafts(
  drafts: LifeDraft[],
  results: Array<{ input_index: number; status: string }>
): LifeDraft[] {
  const processedIndexes = new Set(
    results.filter((result) => result.status === 'processed').map((result) => result.input_index)
  )
  return drafts.filter((_, index) => !processedIndexes.has(index))
}

export function draftStorageKey(personaId: string): string {
  return `rubicks:life-drafts:${personaId}`
}

export function parseStoredDrafts(value: string | null): LifeDraft[] {
  if (!value) return []
  try {
    const parsed: unknown = JSON.parse(value)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((item): item is LifeDraft => {
      if (!item || typeof item !== 'object') return false
      const draft = item as Partial<LifeDraft>
      return typeof draft.localId === 'string'
        && Number.isInteger(draft.age)
        && draft.age! >= 0
        && draft.age! <= 120
        && typeof draft.description === 'string'
        && draft.description.trim().length > 0
    })
  } catch {
    return []
  }
}
