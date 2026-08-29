import { getAuthErrorCode, isAccountCollision, friendlyAuthErrorMessage } from '../authErrors'

describe('getAuthErrorCode', () => {
  it('reads .code off a Firebase-style error object', () => {
    expect(getAuthErrorCode({ code: 'auth/wrong-password' })).toBe('auth/wrong-password')
  })

  it('returns undefined for a plain Error with no .code', () => {
    expect(getAuthErrorCode(new Error('boom'))).toBeUndefined()
  })

  it('returns undefined for non-object values', () => {
    expect(getAuthErrorCode('just a string')).toBeUndefined()
    expect(getAuthErrorCode(null)).toBeUndefined()
    expect(getAuthErrorCode(undefined)).toBeUndefined()
  })
})

describe('isAccountCollision', () => {
  it('is true for every account-already-exists code the linking flows can throw', () => {
    expect(isAccountCollision({ code: 'auth/email-already-in-use' })).toBe(true)
    expect(isAccountCollision({ code: 'auth/credential-already-in-use' })).toBe(true)
    expect(isAccountCollision({ code: 'auth/account-exists-with-different-credential' })).toBe(true)
  })

  it('is false for unrelated auth errors', () => {
    expect(isAccountCollision({ code: 'auth/wrong-password' })).toBe(false)
    expect(isAccountCollision({ code: 'auth/network-request-failed' })).toBe(false)
  })

  it('is false for a plain Error with no code', () => {
    expect(isAccountCollision(new Error('boom'))).toBe(false)
  })
})

describe('friendlyAuthErrorMessage', () => {
  it('never leaks the raw Firebase code or "Firebase: Error (...)" message', () => {
    const message = friendlyAuthErrorMessage({ code: 'auth/email-already-in-use', message: 'Firebase: Error (auth/email-already-in-use).' })
    expect(message).not.toMatch(/auth\//)
    expect(message).not.toMatch(/Firebase/i)
  })

  it('has a distinct message for the account-collision codes', () => {
    expect(friendlyAuthErrorMessage({ code: 'auth/email-already-in-use' })).toMatch(/already exists/i)
    expect(friendlyAuthErrorMessage({ code: 'auth/credential-already-in-use' })).toMatch(/already exists/i)
  })

  it('falls back to a generic message for an unrecognized code', () => {
    expect(friendlyAuthErrorMessage({ code: 'auth/some-new-code-firebase-added-later' })).toBe('Something went wrong. Please try again.')
  })
})
