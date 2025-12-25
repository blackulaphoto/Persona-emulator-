'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/feedback`, {
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
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-cream max-w-2xl w-full rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="relative border-b border-charcoal/10 p-8">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-sage hover:text-charcoal transition-colors"
            aria-label="Close"
          >
            <X size={24} />
          </button>
          <h2 className="text-3xl font-serif text-charcoal">
            Thank you for exploring this
          </h2>
        </div>

        {/* Body */}
        <div className="p-8">
          {!submitted ? (
            <>
              <p className="text-lg text-charcoal mb-6 leading-relaxed">
                You've reached the current limit for this research preview.
              </p>
              <p className="text-base text-sage mb-8 leading-relaxed">
                Your time and curiosity genuinely matter — this project is still forming, and early feedback helps shape what it becomes.
              </p>
              <p className="text-base text-sage mb-8 leading-relaxed">
                If anything felt unclear, surprising, useful, or frustrating, I'd really like to know.
              </p>

              <form onSubmit={handleSubmit}>
                <label className="block mb-3 text-sm font-medium text-charcoal">
                  What stood out to you?
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Share a thought, question, or reaction…"
                  className="w-full h-40 px-4 py-3 rounded-lg border-2 border-clay/30 focus:border-moss focus:outline-none resize-none text-charcoal placeholder-sage/50 font-['Outfit']"
                  disabled={loading}
                />

                {error && (
                  <p className="mt-3 text-sm text-terracotta">
                    {error}
                  </p>
                )}

                <p className="mt-4 text-xs text-sage/70 italic">
                  This isn't a signup or a paywall — just a pause while the project evolves.
                </p>

                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="btn-secondary flex-1"
                    disabled={loading}
                  >
                    Close
                  </button>
                  <button
                    type="submit"
                    className="btn-primary flex-1"
                    disabled={loading || !message.trim()}
                  >
                    {loading ? 'Sending...' : 'Send Feedback'}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <>
              <p className="text-lg text-charcoal mb-8 leading-relaxed">
                Thank you — your feedback was received.
              </p>

              <div className="flex justify-end">
                <button
                  onClick={handleClose}
                  className="btn-primary px-8"
                >
                  Close
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
