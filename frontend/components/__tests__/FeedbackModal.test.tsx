import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FeedbackModal from '../FeedbackModal'

const getIdToken = jest.fn(async () => 'verified-token')

jest.mock('@/lib/firebase', () => ({
  auth: { currentUser: { getIdToken: () => getIdToken() } },
}))

beforeEach(() => {
  jest.clearAllMocks()
  global.fetch = jest.fn(async () => ({ ok: true })) as jest.Mock
})

describe('FeedbackModal', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<FeedbackModal isOpen={false} onClose={jest.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('uses the Rubicks preview copy and controls', () => {
    render(<FeedbackModal isOpen onClose={jest.fn()} />)

    expect(screen.getByRole('dialog', { name: 'You’ve reached today’s preview limit' })).toHaveClass('rubix-modal-panel')
    expect(screen.getByText('RESEARCH PREVIEW')).toBeInTheDocument()
    expect(screen.getByLabelText('WHAT STOOD OUT?')).toHaveClass('rubix-textarea')
    expect(screen.getByText('No signup or payment required.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send feedback' })).toHaveClass('rubix-btn-primary')
  })

  it('submits authenticated feedback and shows confirmation', async () => {
    render(<FeedbackModal isOpen onClose={jest.fn()} />)
    await userEvent.type(screen.getByLabelText('WHAT STOOD OUT?'), 'The trajectory view stood out.')
    await userEvent.click(screen.getByRole('button', { name: 'Send feedback' }))

    await waitFor(() => expect(screen.getByText('Thank you — your feedback was received.')).toBeInTheDocument())
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/feedback'), expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ Authorization: 'Bearer verified-token' }),
    }))
  })
})
