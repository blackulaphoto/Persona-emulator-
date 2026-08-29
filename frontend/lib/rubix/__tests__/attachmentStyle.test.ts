import { attachmentStyleLabel, attachmentStyleTone } from '../attachmentStyle'

describe('attachmentStyleLabel', () => {
  it('labels every real style the backend engine can produce or store', () => {
    expect(attachmentStyleLabel('secure')).toBe('Secure')
    expect(attachmentStyleLabel('anxious')).toBe('Anxious')
    expect(attachmentStyleLabel('avoidant')).toBe('Avoidant')
    expect(attachmentStyleLabel('fearful-avoidant')).toBe('Fearful-avoidant')
    expect(attachmentStyleLabel('disorganized')).toBe('Disorganized')
  })

  it('also labels the insecure-* baseline aliases used at persona creation', () => {
    expect(attachmentStyleLabel('insecure-anxious')).toBe('Anxious')
    expect(attachmentStyleLabel('insecure-avoidant')).toBe('Avoidant')
  })

  it('falls back to the raw value for an unrecognized style rather than hiding it', () => {
    expect(attachmentStyleLabel('made_up_style')).toBe('made_up_style')
  })

  it('returns Unknown for null/undefined rather than throwing', () => {
    expect(attachmentStyleLabel(null)).toBe('Unknown')
    expect(attachmentStyleLabel(undefined)).toBe('Unknown')
  })

  it('is case-insensitive since the backend lowercases these consistently but callers may not', () => {
    expect(attachmentStyleLabel('Secure')).toBe('Secure')
  })
})

describe('attachmentStyleTone', () => {
  it('maps secure to a positive tone and the anxious/avoidant styles to non-positive tones', () => {
    expect(attachmentStyleTone('secure')).toBe('positive')
    expect(attachmentStyleTone('anxious')).toBe('caution')
    expect(attachmentStyleTone('avoidant')).toBe('neutral')
    expect(attachmentStyleTone('fearful-avoidant')).toBe('violet')
  })

  it('returns muted for an unrecognized or missing style rather than throwing', () => {
    expect(attachmentStyleTone('made_up_style')).toBe('muted')
    expect(attachmentStyleTone(null)).toBe('muted')
  })
})
