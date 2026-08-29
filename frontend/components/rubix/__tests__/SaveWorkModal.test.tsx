import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SaveWorkModal } from '../SaveWorkModal'

const mockConvertAnonymousWithEmail = jest.fn()
const mockConvertAnonymousWithGoogle = jest.fn()
const mockLoginWithGoogle = jest.fn()
const mockLogin = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    convertAnonymousWithEmail: mockConvertAnonymousWithEmail,
    convertAnonymousWithGoogle: mockConvertAnonymousWithGoogle,
    loginWithGoogle: mockLoginWithGoogle,
    login: mockLogin,
  }),
}))

const mockSignInWithCredential = jest.fn()
const mockCredentialFromError = jest.fn()

jest.mock('firebase/auth', () => ({
  GoogleAuthProvider: { credentialFromError: (...args: any[]) => mockCredentialFromError(...args) },
  signInWithCredential: (...args: any[]) => mockSignInWithCredential(...args),
}))

jest.mock('@/lib/firebase', () => ({ auth: {} }))

function emailCollisionError() {
  return Object.assign(new Error('Firebase: Error (auth/email-already-in-use).'), { code: 'auth/email-already-in-use' })
}

function googleCollisionError() {
  return Object.assign(new Error('Firebase: Error (auth/credential-already-in-use).'), { code: 'auth/credential-already-in-use' })
}

beforeEach(() => {
  jest.clearAllMocks()
})

describe('SaveWorkModal - default view', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<SaveWorkModal open={false} onClose={jest.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('offers both Google and email/password paths when open', () => {
    render(<SaveWorkModal open onClose={jest.fn()} />)
    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    expect(screen.getByLabelText('EMAIL')).toBeInTheDocument()
    expect(screen.getByLabelText('PASSWORD')).toBeInTheDocument()
  })
})

describe('SaveWorkModal - email save', () => {
  it('calls convertAnonymousWithEmail and closes on success', async () => {
    mockConvertAnonymousWithEmail.mockResolvedValueOnce(undefined)
    const onClose = jest.fn()
    render(<SaveWorkModal open onClose={onClose} />)

    await userEvent.type(screen.getByLabelText('EMAIL'), 'demo@example.com')
    await userEvent.type(screen.getByLabelText('PASSWORD'), 'password123')
    await userEvent.type(screen.getByLabelText('CONFIRM PASSWORD'), 'password123')
    await userEvent.click(screen.getByText('Create account'))

    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(mockConvertAnonymousWithEmail).toHaveBeenCalledWith('demo@example.com', 'password123')
  })

  it('rejects mismatched passwords locally without calling convertAnonymousWithEmail', async () => {
    render(<SaveWorkModal open onClose={jest.fn()} />)

    await userEvent.type(screen.getByLabelText('EMAIL'), 'demo@example.com')
    await userEvent.type(screen.getByLabelText('PASSWORD'), 'password123')
    await userEvent.type(screen.getByLabelText('CONFIRM PASSWORD'), 'different456')
    await userEvent.click(screen.getByText('Create account'))

    expect(await screen.findByText(/do not match/i)).toBeInTheDocument()
    expect(mockConvertAnonymousWithEmail).not.toHaveBeenCalled()
  })

  it('shows the account-already-exists case on collision, without pretending it merged', async () => {
    mockConvertAnonymousWithEmail.mockRejectedValueOnce(emailCollisionError())
    render(<SaveWorkModal open onClose={jest.fn()} />)

    await userEvent.type(screen.getByLabelText('EMAIL'), 'existing@example.com')
    await userEvent.type(screen.getByLabelText('PASSWORD'), 'password123')
    await userEvent.type(screen.getByLabelText('CONFIRM PASSWORD'), 'password123')
    await userEvent.click(screen.getByText('Create account'))

    expect(await screen.findByText('That account already exists')).toBeInTheDocument()
    expect(screen.getByText(/An account already exists for existing@example\.com/)).toBeInTheDocument()
    expect(screen.getByText(/won't bring today's demo along/i)).toBeInTheDocument()
  })

  it('lets the user sign into the existing account from the collision view, explicitly', async () => {
    mockConvertAnonymousWithEmail.mockRejectedValueOnce(emailCollisionError())
    mockLogin.mockResolvedValueOnce(undefined)
    const onClose = jest.fn()
    render(<SaveWorkModal open onClose={onClose} />)

    await userEvent.type(screen.getByLabelText('EMAIL'), 'existing@example.com')
    await userEvent.type(screen.getByLabelText('PASSWORD'), 'password123')
    await userEvent.type(screen.getByLabelText('CONFIRM PASSWORD'), 'password123')
    await userEvent.click(screen.getByText('Create account'))
    await screen.findByText('That account already exists')

    await userEvent.type(screen.getByLabelText(/PASSWORD FOR existing@example.com/i), 'their-real-password')
    await userEvent.click(screen.getByText('Sign in to that account'))

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('existing@example.com', 'their-real-password'))
    expect(onClose).toHaveBeenCalled()
  })

  it('lets the user back out and keep exploring the demo instead of switching accounts', async () => {
    mockConvertAnonymousWithEmail.mockRejectedValueOnce(emailCollisionError())
    render(<SaveWorkModal open onClose={jest.fn()} />)

    await userEvent.type(screen.getByLabelText('EMAIL'), 'existing@example.com')
    await userEvent.type(screen.getByLabelText('PASSWORD'), 'password123')
    await userEvent.type(screen.getByLabelText('CONFIRM PASSWORD'), 'password123')
    await userEvent.click(screen.getByText('Create account'))
    await screen.findByText('That account already exists')

    await userEvent.click(screen.getByText('Keep exploring the demo'))

    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    expect(mockLogin).not.toHaveBeenCalled()
  })
})

describe('SaveWorkModal - Google save', () => {
  it('calls convertAnonymousWithGoogle and closes on success', async () => {
    mockConvertAnonymousWithGoogle.mockResolvedValueOnce(undefined)
    const onClose = jest.fn()
    render(<SaveWorkModal open onClose={onClose} />)

    await userEvent.click(screen.getByText('Continue with Google'))

    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(mockConvertAnonymousWithGoogle).toHaveBeenCalledTimes(1)
  })

  it('on collision, reuses the credential from the error to sign in without a second popup', async () => {
    const err = googleCollisionError()
    mockConvertAnonymousWithGoogle.mockRejectedValueOnce(err)
    const fakeCredential = { providerId: 'google.com' }
    mockCredentialFromError.mockReturnValueOnce(fakeCredential)
    mockSignInWithCredential.mockResolvedValueOnce(undefined)
    const onClose = jest.fn()
    render(<SaveWorkModal open onClose={onClose} />)

    await userEvent.click(screen.getByText('Continue with Google'))
    await screen.findByText('That account already exists')

    await userEvent.click(screen.getByText('Sign in to that account'))

    await waitFor(() => expect(mockSignInWithCredential).toHaveBeenCalledWith(expect.anything(), fakeCredential))
    expect(mockLoginWithGoogle).not.toHaveBeenCalled()
    expect(onClose).toHaveBeenCalled()
  })

  it('falls back to a fresh Google sign-in if no reusable credential comes back with the error', async () => {
    const err = googleCollisionError()
    mockConvertAnonymousWithGoogle.mockRejectedValueOnce(err)
    mockCredentialFromError.mockReturnValueOnce(null)
    mockLoginWithGoogle.mockResolvedValueOnce(undefined)
    render(<SaveWorkModal open onClose={jest.fn()} />)

    await userEvent.click(screen.getByText('Continue with Google'))
    await screen.findByText('That account already exists')

    await userEvent.click(screen.getByText('Sign in to that account'))

    await waitFor(() => expect(mockLoginWithGoogle).toHaveBeenCalledTimes(1))
    expect(mockSignInWithCredential).not.toHaveBeenCalled()
  })
})
