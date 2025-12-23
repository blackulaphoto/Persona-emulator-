'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, User } from 'lucide-react'
import { api } from '@/lib/api'

export default function CreatePersonaPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
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
    } catch (error) {
      console.error('Failed to create persona:', error)
      alert('Failed to create persona. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-grain">
      {/* Header */}
      <header className="border-b border-charcoal/10 bg-cream/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-sage hover:text-moss transition-colors mb-4"
          >
            <ArrowLeft size={20} />
            Back to Personas
          </button>
          <h1 className="text-4xl font-serif text-charcoal">
            Create New Persona
          </h1>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-cream border-2 border-charcoal/10 rounded-2xl p-8 shadow-lg">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-moss/10 p-3 rounded-xl">
              <User className="text-moss" size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-serif text-charcoal">
                Baseline Profile
              </h2>
              <p className="text-sage text-sm">
                Define the starting point for this persona's journey
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-charcoal mb-2">
                Name
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border-2 border-charcoal/10 bg-cream focus:border-moss focus:outline-none transition-colors"
                placeholder="e.g., Emma, Alex, Jordan"
              />
            </div>

            {/* Age */}
            <div>
              <label className="block text-sm font-medium text-charcoal mb-2">
                Baseline Age
              </label>
              <input
                type="number"
                required
                min="0"
                max="100"
                value={formData.baseline_age}
                onChange={(e) => setFormData({ ...formData, baseline_age: parseInt(e.target.value) })}
                className="w-full px-4 py-3 rounded-lg border-2 border-charcoal/10 bg-cream focus:border-moss focus:outline-none transition-colors"
              />
              <p className="text-xs text-sage mt-1">
                The age when this persona's story begins
              </p>
            </div>

            {/* Gender */}
            <div>
              <label className="block text-sm font-medium text-charcoal mb-2">
                Gender
              </label>
              <select
                value={formData.baseline_gender}
                onChange={(e) => setFormData({ ...formData, baseline_gender: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border-2 border-charcoal/10 bg-cream focus:border-moss focus:outline-none transition-colors"
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="non-binary">Non-binary</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Background */}
            <div>
              <label className="block text-sm font-medium text-charcoal mb-2">
                Background Story
              </label>
              <textarea
                required
                value={formData.baseline_background}
                onChange={(e) => setFormData({ ...formData, baseline_background: e.target.value })}
                rows={4}
                className="w-full px-4 py-3 rounded-lg border-2 border-charcoal/10 bg-cream focus:border-moss focus:outline-none transition-colors resize-none"
                placeholder="Describe their childhood, family, environment, and early experiences..."
              />
              <p className="text-xs text-sage mt-1">
                This context helps the AI analyze how experiences affect development
              </p>
              <p className="text-xs text-sage mt-2">
                Early environment sets the emotional foundation, not the outcome.
                Psychological traits start slightly biased, but experiences shape who someone becomes.
              </p>
            </div>

            {/* Submit */}
            <div className="pt-4 flex gap-4">
              <button
                type="button"
                onClick={() => router.push('/')}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Persona'}
              </button>
            </div>
          </form>
        </div>

        {/* Info Card */}
        <div className="mt-8 bg-sage/10 border-2 border-sage/20 rounded-xl p-6">
          <h3 className="font-serif text-lg text-charcoal mb-2">
            What happens next?
          </h3>
          <ul className="text-sm text-sage space-y-2">
            <li>• Add life experiences to see how they shape personality</li>
            <li>• Apply therapeutic interventions to address symptoms</li>
            <li>• Watch the personality evolve over time with AI analysis</li>
            <li>• View the complete timeline of psychological evolution</li>
          </ul>
        </div>
      </div>
    </main>
  )
}
