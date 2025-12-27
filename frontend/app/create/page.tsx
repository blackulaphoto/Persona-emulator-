'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, User } from 'lucide-react'
import { api } from '@/lib/api'
import FeedbackModal from '@/components/FeedbackModal'
import { Button } from '@/components/ui/Button'
import { Input, Textarea } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'

export default function CreatePersonaPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    baseline_age: 10,
    baseline_gender: 'female',
    baseline_background: '',
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)

    try {
      const persona = await api.createPersona(formData)
      router.push(`/persona/${persona.id}`)
    } catch (error: any) {
      console.error('Failed to create persona:', error)

      // Check if this is a persona limit error (403)
      if (error.message && error.message.includes('403')) {
        setShowFeedbackModal(true)
      } else {
        alert('Failed to create persona. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-apple-bg-tertiary gradient-apple-mesh">
      {/* Glass Header */}
      <header className="glass-panel">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-apple-text-secondary hover:text-apple-blue-500 transition-colors mb-4 font-medium"
          >
            <ArrowLeft size={20} />
            Back to Personas
          </button>
          <h1 className="text-4xl font-serif text-apple-text-primary font-bold animate-fade-in-apple">
            Create New Persona
          </h1>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-12">
        <Card className="animate-scale-in">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-apple-blue-100 p-3 rounded-apple-lg">
              <User className="text-apple-blue-600" size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-serif text-apple-text-primary font-bold">
                Baseline Profile
              </h2>
              <p className="text-apple-text-secondary text-sm">
                Define the starting point for this persona's journey
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <Input
              label="Name"
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Emma, Alex, Jordan"
            />

            {/* Age */}
            <div>
              <Input
                label="Baseline Age"
                type="number"
                required
                min={0}
                max={100}
                value={formData.baseline_age}
                onChange={(e) => setFormData({ ...formData, baseline_age: parseInt(e.target.value) })}
              />
              <p className="text-xs text-apple-text-tertiary mt-1.5">
                The age when this persona's story begins
              </p>
            </div>

            {/* Gender */}
            <div>
              <label className="label-apple">Gender</label>
              <select
                value={formData.baseline_gender}
                onChange={(e) => setFormData({ ...formData, baseline_gender: e.target.value })}
                className="input-apple"
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="non-binary">Non-binary</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Background */}
            <div>
              <Textarea
                label="Background Story"
                required
                value={formData.baseline_background}
                onChange={(e) => setFormData({ ...formData, baseline_background: e.target.value })}
                rows={4}
                placeholder="Describe their childhood, family, environment, and early experiences..."
              />
              <p className="text-xs text-apple-text-tertiary mt-1.5">
                This context helps the AI analyze how experiences affect development
              </p>
              <p className="text-xs text-apple-text-tertiary mt-2">
                Early environment sets the emotional foundation, not the outcome.
                Psychological traits start slightly biased, but experiences shape who someone becomes.
              </p>
            </div>

            {/* Submit */}
            <div className="pt-4 flex gap-4">
              <Button
                type="button"
                variant="secondary"
                onClick={() => router.push('/')}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={loading}
                loading={loading}
                className="flex-1"
              >
                {loading ? 'Creating...' : 'Create Persona'}
              </Button>
            </div>
          </form>
        </Card>

        {/* Info Card */}
        <Card variant="glass" className="mt-8 animate-fade-in-apple delay-apple-200">
          <h3 className="font-serif text-lg text-apple-text-primary mb-3 font-semibold">
            What happens next?
          </h3>
          <ul className="text-sm text-apple-text-secondary space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-apple-blue-500 mt-0.5">•</span>
              <span>Add life experiences to see how they shape personality</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-apple-blue-500 mt-0.5">•</span>
              <span>Apply therapeutic interventions to address symptoms</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-apple-blue-500 mt-0.5">•</span>
              <span>Watch the personality evolve over time with AI analysis</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-apple-blue-500 mt-0.5">•</span>
              <span>View the complete timeline of psychological evolution</span>
            </li>
          </ul>
        </Card>
      </div>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
      />
    </main>
  )
}
