import { useState } from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../AuthContext'

// Small in-memory fake of the bits of the Firebase Auth SDK AuthContext
// calls, wired so signInAnonymously/linkWithCredential/etc. actually flip
// mockAuthObj.currentUser and fire the stored onAuthStateChanged callback -
// exactly like the real SDK does - rather than mocking each function in
// isolation with no shared state between them.
let mockAuthStateCallback: ((user: any) => void) | null = null
const mockAuthObj: { currentUser: any } = { currentUser: null }

function emit(user: any) {
  mockAuthObj.currentUser = user
  mockAuthStateCallback?.(user)
}

jest.mock('firebase/auth', () => ({
  onAuthStateChanged: jest.fn((_auth: any, cb: (user: any) => void) => {
    mockAuthStateCallback = cb
    cb(mockAuthObj.currentUser)
    return jest.fn()
  }),
  signInAnonymously: jest.fn(async () => {
    const user = { uid: 'anon-uid-1', isAnonymous: true, email: null, displayName: null }
    emit(user)
    return { user }
  }),
  createUserWithEmailAndPassword: jest.fn(async (_auth: any, email: string) => {
    const user = { uid: 'new-registered-uid', isAnonymous: false, email, displayName: null }
    emit(user)
    return { user }
  }),
  signInWithEmailAndPassword: jest.fn(async (_auth: any, email: string) => {
    const user = { uid: 'existing-registered-uid', isAnonymous: false, email, displayName: null }
    emit(user)
    return { user }
  }),
  signOut: jest.fn(async () => {
    emit(null)
  }),
  sendPasswordResetEmail: jest.fn(async () => {}),
  signInWithPopup: jest.fn(async () => {
    const user = { uid: 'google-uid', isAnonymous: false, email: 'g@example.com', displayName: 'G' }
    emit(user)
    return { user }
  }),
  linkWithCredential: jest.fn(async (currentUser: any) => {
    // Real linkWithCredential keeps the SAME uid - only providerData/email changes.
    const linked = { ...currentUser, isAnonymous: false, email: 'linked@example.com' }
    emit(linked)
    return { user: linked }
  }),
  linkWithPopup: jest.fn(async (currentUser: any) => {
    const linked = { ...currentUser, isAnonymous: false, email: 'linked-google@example.com', displayName: 'Linked Google' }
    emit(linked)
    return { user: linked }
  }),
  GoogleAuthProvider: jest.fn().mockImplementation(() => ({})),
  EmailAuthProvider: { credential: jest.fn((email: string, password: string) => ({ email, password, providerId: 'password' })) },
}))

jest.mock('@/lib/firebase', () => ({
  get auth() {
    return mockAuthObj
  },
  devBypassEnabled: false,
}))

const { signInAnonymously, linkWithCredential, linkWithPopup, signOut } = jest.requireMock('firebase/auth')

function Probe() {
  const ctx = useAuth()
  const [error, setError] = useState('')

  function run(action: () => Promise<void>) {
    return async () => {
      setError('')
      try {
        await action()
      } catch (err: any) {
        setError(err?.code || err?.message || 'error')
      }
    }
  }

  return (
    <div>
      <div data-testid="uid">{ctx.user?.uid ?? 'none'}</div>
      <div data-testid="anonymous">{String(ctx.isAnonymous)}</div>
      <div data-testid="loading">{String(ctx.loading)}</div>
      <div data-testid="error">{error}</div>
      <button onClick={run(ctx.startDemo)}>startDemo</button>
      <button onClick={run(() => ctx.convertAnonymousWithEmail('a@b.com', 'password123'))}>convertEmail</button>
      <button onClick={run(ctx.convertAnonymousWithGoogle)}>convertGoogle</button>
      <button onClick={run(ctx.logout)}>logout</button>
    </div>
  )
}

beforeEach(() => {
  mockAuthStateCallback = null
  mockAuthObj.currentUser = null
  jest.clearAllMocks()
})

describe('AuthContext - startDemo', () => {
  it('signs in anonymously with a real, unique uid when nobody is signed in', async () => {
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))

    await act(async () => {
      await userEvent.click(screen.getByText('startDemo'))
    })

    expect(signInAnonymously).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('uid').textContent).toBe('anon-uid-1')
    expect(screen.getByTestId('anonymous').textContent).toBe('true')
  })

  it('does not start a new anonymous session for an already-authenticated user', async () => {
    mockAuthObj.currentUser = { uid: 'already-here', isAnonymous: false, email: 'x@y.com' }
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('already-here'))

    await act(async () => {
      await userEvent.click(screen.getByText('startDemo'))
    })

    expect(signInAnonymously).not.toHaveBeenCalled()
    expect(screen.getByTestId('uid').textContent).toBe('already-here')
  })

  it('does not start a second anonymous session for an existing demo session', async () => {
    mockAuthObj.currentUser = { uid: 'already-anon', isAnonymous: true, email: null }
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('already-anon'))

    await act(async () => {
      await userEvent.click(screen.getByText('startDemo'))
    })

    expect(signInAnonymously).not.toHaveBeenCalled()
  })
})

describe('AuthContext - linking (save your work)', () => {
  it('convertAnonymousWithEmail keeps the SAME uid after linking', async () => {
    mockAuthObj.currentUser = { uid: 'anon-uid-keep-me', isAnonymous: true, email: null }
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('anon-uid-keep-me'))

    await act(async () => {
      await userEvent.click(screen.getByText('convertEmail'))
    })

    expect(linkWithCredential).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('uid').textContent).toBe('anon-uid-keep-me')
    expect(screen.getByTestId('anonymous').textContent).toBe('false')
  })

  it('convertAnonymousWithGoogle keeps the SAME uid after linking', async () => {
    mockAuthObj.currentUser = { uid: 'anon-uid-keep-me-2', isAnonymous: true, email: null }
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('anon-uid-keep-me-2'))

    await act(async () => {
      await userEvent.click(screen.getByText('convertGoogle'))
    })

    expect(linkWithPopup).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('uid').textContent).toBe('anon-uid-keep-me-2')
  })

  it('rejects convertAnonymousWithEmail when there is no anonymous session to save', async () => {
    mockAuthObj.currentUser = { uid: 'already-registered', isAnonymous: false, email: 'x@y.com' }
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('already-registered'))

    await act(async () => {
      await userEvent.click(screen.getByText('convertEmail'))
    })

    expect(linkWithCredential).not.toHaveBeenCalled()
  })

  it('surfaces the raw Firebase error code on collision so the UI can detect it', async () => {
    mockAuthObj.currentUser = { uid: 'anon-collision', isAnonymous: true, email: null }
    linkWithCredential.mockRejectedValueOnce(Object.assign(new Error('Firebase: Error (auth/email-already-in-use).'), { code: 'auth/email-already-in-use' }))
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('anon-collision'))

    await act(async () => {
      await userEvent.click(screen.getByText('convertEmail'))
    })

    expect(linkWithCredential).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('error').textContent).toBe('auth/email-already-in-use')
    // Session must not have been silently upgraded/lost on failure.
    expect(screen.getByTestId('uid').textContent).toBe('anon-collision')
    expect(screen.getByTestId('anonymous').textContent).toBe('true')
  })
})

describe('AuthContext - logout', () => {
  it('clears the user on logout', async () => {
    mockAuthObj.currentUser = { uid: 'someone', isAnonymous: false, email: 'x@y.com' }
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('uid').textContent).toBe('someone'))

    await act(async () => {
      await userEvent.click(screen.getByText('logout'))
    })

    expect(signOut).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('uid').textContent).toBe('none')
  })
})

describe('AuthContext - loading state', () => {
  it('resolves out of the loading state once the initial auth state is known (children are withheld from the tree until then)', async () => {
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))
  })
})
