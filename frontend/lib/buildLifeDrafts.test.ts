import { agesForDecade, draftStorageKey, LIFESPAN_DECADES, parseStoredDrafts, retainUnprocessedDrafts, sortLifeDrafts } from './buildLifeDrafts'

describe('Build Their Life workflow helpers', () => {
  it('always exposes the full lifespan and only age 120 in the final group', () => {
    expect(LIFESPAN_DECADES).toEqual([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120])
    expect(agesForDecade(0)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    expect(agesForDecade(120)).toEqual([120])
  })

  it('sorts queued drafts chronologically and deterministically within an age', () => {
    const drafts = [
      { localId: 'b', age: 42, description: 'Second at 42' },
      { localId: 'c', age: 8, description: 'Childhood' },
      { localId: 'a', age: 42, description: 'First at 42' },
    ]
    expect(sortLifeDrafts(drafts).map((draft) => draft.localId)).toEqual(['c', 'a', 'b'])
    expect(drafts.map((draft) => draft.localId)).toEqual(['b', 'c', 'a'])
  })

  it('uses persona-scoped storage and ignores malformed persisted data', () => {
    expect(draftStorageKey('persona-1')).toBe('rubicks:life-drafts:persona-1')
    expect(parseStoredDrafts('not json')).toEqual([])
    expect(parseStoredDrafts(JSON.stringify([
      { localId: 'valid', age: 19, description: 'Moved away' },
      { localId: 'too-old', age: 121, description: 'Invalid' },
      { localId: 'blank', age: 20, description: '   ' },
    ]))).toEqual([{ localId: 'valid', age: 19, description: 'Moved away' }])
  })

  it('removes only processed drafts and retains failed and omitted inputs', () => {
    const drafts = [
      { localId: 'processed', age: 10, description: 'Processed' },
      { localId: 'failed', age: 20, description: 'Failed' },
      { localId: 'unattempted', age: 30, description: 'Not returned by the stopped batch' },
    ]
    const results = [
      { input_index: 0, status: 'processed' },
      { input_index: 1, status: 'failed' },
    ]

    expect(retainUnprocessedDrafts(drafts, results).map((draft) => draft.localId)).toEqual(['failed', 'unattempted'])
  })
})
