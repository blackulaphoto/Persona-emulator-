'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, User } from 'lucide-react'
import { api } from '@/lib/api'
import FeedbackModal from '@/components/FeedbackModal'
import { Button } from '@/components/ui/Button'
import { Input, Textarea } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'
import { Tooltip, Examples, Checklist, SidebarHelp, FAQ, HelpText } from '@/components/help/HelpComponents'
import { HELP_CONTENT } from '@/lib/help/HelpContentLibrary'

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

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Form - 3 columns */}
          <div className="lg:col-span-3">
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
                <div>
                  <div className="flex items-center gap-2">
                    <label className="label-apple">Name</label>
                    <Tooltip content={HELP_CONTENT.persona.name.tooltip} />
                  </div>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Emma, Alex, Jordan"
                    className="input-apple mt-2"
                  />
                  <Examples
                    title="See examples"
                    examples={HELP_CONTENT.persona.name.examples}
                  />
                </div>

                {/* Age */}
                <div>
                  <div className="flex items-center gap-2">
                    <label className="label-apple">Baseline Age</label>
                    <Tooltip content={HELP_CONTENT.persona.age.tooltip} />
                  </div>
                  <input
                    type="number"
                    required
                    min={0}
                    max={100}
                    value={formData.baseline_age}
                    onChange={(e) => setFormData({ ...formData, baseline_age: parseInt(e.target.value) })}
                    className="input-apple mt-2"
                  />
                  <p className="text-xs text-apple-text-tertiary mt-1.5">
                    {HELP_CONTENT.persona.age.helpText}
                  </p>
                </div>

                {/* Gender */}
                <div>
                  <div className="flex items-center gap-2">
                    <label className="label-apple">Gender</label>
                    <Tooltip content={HELP_CONTENT.persona.gender.tooltip} />
                  </div>
                  <select
                    value={formData.baseline_gender}
                    onChange={(e) => setFormData({ ...formData, baseline_gender: e.target.value })}
                    className="input-apple mt-2"
                  >
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="non-binary">Non-binary</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Background - THE BIG ONE */}
                <div>
                  <div className="flex items-center gap-2">
                    <label className="label-apple">Background Story</label>
                    <Tooltip content={HELP_CONTENT.persona.backstory.tooltip} />
                  </div>
                  <textarea
                    required
                    value={formData.baseline_background}
                    onChange={(e) => setFormData({ ...formData, baseline_background: e.target.value })}
                    rows={8}
                    placeholder="Provide comprehensive background information about childhood, family, environment, experiences, symptoms, and strengths..."
                    className="input-apple mt-2"
                  />

                  {/* Character counter */}
                  <div className="flex justify-between items-center mt-1.5">
                    <span className="text-xs text-apple-text-tertiary">
                      {formData.baseline_background.length} characters
                    </span>
                    <span className="text-xs text-apple-blue-600 font-medium">
                      More detail = Better results (aim for 200-500 words)
                    </span>
                  </div>

                  {/* What to include checklist */}
                  <Checklist
                    title="📝 What to include:"
                    items={HELP_CONTENT.persona.backstory.whatToInclude}
                  />

                  {/* Examples */}
                  <Examples
                    title="See examples"
                    examples={HELP_CONTENT.persona.backstory.examples.map(ex => ({
                      label: ex.title,
                      text: ex.text
                    }))}
                  />

                  <HelpText type="tip">
                    Think like a therapist writing a clinical intake summary. Include BOTH challenges AND strengths!
                  </HelpText>
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
          </div>

          {/* Sidebar Guide - 1 column */}
          <div className="lg:col-span-1">
            <SidebarHelp title="Quick Guide">
              <div className="bg-apple-blue-50 border-l-4 border-apple-blue-500 p-3 rounded">
                <p className="text-sm font-semibold text-apple-blue-800 mb-1">
                  Pro Tip
                </p>
                <p className="text-xs text-apple-text-secondary">
                  Think of this as writing a client intake form. Include both challenges AND strengths!
                </p>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-apple-text-primary mb-2">
                  Essential Information
                </h4>
                <ul className="space-y-2 text-xs text-apple-text-secondary">
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Family background & parenting</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Early childhood experiences</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Trauma or adversity</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Current symptoms/concerns</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Protective factors</span>
                  </li>
                </ul>
              </div>

              <div className="border-t border-apple-border pt-4">
                <h4 className="text-sm font-semibold text-apple-text-primary mb-2">
                  Common Questions
                </h4>
                <FAQ items={HELP_CONTENT.faq.general.slice(0, 3)} />
              </div>
            </SidebarHelp>
          </div>
        </div>
      </div>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
      />
    </main>
  )
}
