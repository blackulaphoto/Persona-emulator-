'use client'

import { useState } from 'react'
import { RubixModal } from '@/components/rubix/RubixModal'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)

  if (!isOpen) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!message.trim()) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
      const apiRoot = apiBase ? `${apiBase}/api/v1` : '/api/v1';
      const response = await fetch(`${apiRoot}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: JSON.stringify({ message: message.trim() })
      })

      if (!response.ok) {
        throw new Error('Failed to submit feedback')
      }

      setSubmitted(true)
      setMessage('')
    } catch (err) {
      console.error('Failed to submit feedback:', err)
      setError('Unable to send feedback. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function getAuthToken(): Promise<string> {
    const { auth } = await import('@/lib/firebase')
    if (!auth) throw new Error('Firebase auth not initialized')
    const user = auth.currentUser
    if (!user) throw new Error('Not authenticated')
    return await user.getIdToken()
  }

  function handleClose() {
    // Reset state when closing
    setTimeout(() => {
      setMessage('')
      setError(null)
      setSubmitted(false)
    }, 300)
    onClose()
  }

  return (
    <RubixModal
      open={isOpen}
      onClose={handleClose}
      eyebrow="RESEARCH PREVIEW"
      eyebrowColor="#7fe3ff"
      title="You’ve reached today’s preview limit"
      width={650}
    >
      {!submitted ? (
        <>
          <div style={{ fontSize: 14.5, lineHeight: 1.65, color: 'rgba(226,240,255,0.82)' }}>
            <p>Rubicks is still in active development, and preview access is limited while we learn how people use it.</p>
            <p style={{ marginTop: 14 }}>If something surprised you, felt unclear, or made you think, we’d love to hear it.</p>
          </div>

          <form onSubmit={handleSubmit} style={{ marginTop: 24 }}>
            <label className="rubix-field-label" htmlFor="preview-feedback">WHAT STOOD OUT?</label>
            <textarea
              id="preview-feedback"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Share a thought, question, or reaction..."
              className="rubix-textarea"
              style={{ width: '100%', height: 150, marginTop: 9, resize: 'vertical' }}
              disabled={loading}
            />

            {error && <div role="alert" style={{ marginTop: 10, fontSize: 12.5, color: 'rgba(255,190,180,0.95)' }}>{error}</div>}

            <div style={{ marginTop: 12, fontSize: 12.5, color: 'rgba(205,228,255,0.58)' }}>No signup or payment required.</div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24, flexWrap: 'wrap' }}>
              <button type="button" onClick={handleClose} className="rubix-btn-ghost" disabled={loading}>Close</button>
              <button type="submit" className="rubix-btn-primary" disabled={loading || !message.trim()}>
                {loading ? 'Sending…' : 'Send feedback'}
              </button>
            </div>
          </form>
        </>
      ) : (
        <div>
          <div style={{ fontSize: 14.5, lineHeight: 1.65, color: 'rgba(226,240,255,0.82)' }}>Thank you — your feedback was received.</div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24 }}>
            <button type="button" onClick={handleClose} className="rubix-btn-primary">Close</button>
          </div>
        </div>
      )}
    </RubixModal>
  )
}
