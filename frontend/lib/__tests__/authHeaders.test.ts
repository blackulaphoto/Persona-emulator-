let mockAuth: { currentUser: any } | null = null
let mockHasConfig = true
let mockDevBypassEnabled = false

jest.mock('@/lib/firebase', () => ({
  get auth() {
    return mockAuth
  },
  get hasConfig() {
    return mockHasConfig
  },
  get devBypassEnabled() {
    return mockDevBypassEnabled
  },
}))

import { getAuthHeaders } from '../authHeaders'

beforeEach(() => {
  mockAuth = null
  mockHasConfig = true
  mockDevBypassEnabled = false
})

describe('getAuthHeaders', () => {
  it('sends a real Firebase ID token as a Bearer header for a signed-in user', async () => {
    mockAuth = { currentUser: { getIdToken: jest.fn().mockResolvedValue('real-id-token-abc') } }
    const headers = await getAuthHeaders() as Record<string, string>
    expect(headers.Authorization).toBe('Bearer real-id-token-abc')
  })

  it('works identically for an anonymous Firebase user - getIdToken() is the same call either way', async () => {
    mockAuth = { currentUser: { isAnonymous: true, getIdToken: jest.fn().mockResolvedValue('anon-id-token-xyz') } }
    const headers = await getAuthHeaders() as Record<string, string>
    expect(headers.Authorization).toBe('Bearer anon-id-token-xyz')
  })

  it('throws "Not authenticated" when Firebase is configured but nobody is signed in', async () => {
    mockAuth = { currentUser: null }
    await expect(getAuthHeaders()).rejects.toThrow('Not authenticated')
  })

  it('throws a configuration error when Firebase is not configured and the dev bypass is off', async () => {
    mockHasConfig = false
    mockAuth = null
    mockDevBypassEnabled = false
    await expect(getAuthHeaders()).rejects.toThrow('not configured')
  })

  it('returns the local-dev-bypass header only when devBypassEnabled is explicitly true', async () => {
    mockDevBypassEnabled = true
    mockHasConfig = false
    mockAuth = null
    const headers = await getAuthHeaders() as Record<string, string>
    expect(headers.Authorization).toBe('Bearer dev-local-bypass')
  })
})
