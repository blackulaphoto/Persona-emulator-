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
  })
  const [origin, setOrigin] = useState({
    home_environment: '',
    caregivers: '',
    other_notes: '',
  })

  // Composes the guided answers into the single text blob the backend expects.
  // Keeping this general (no dated events) is what keeps it distinct from Experiences.
  function buildBaselineBackground() {
    const parts = [
      origin.home_environment && `Home environment: ${origin.home_environment}`,
      origin.caregivers && `Caregivers: ${origin.caregivers}`,
      origin.other_notes && `Additional context: ${origin.other_notes}`,
    ].filter(Boolean)
    return parts.join('\n')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)

    try {
      const persona = await api.createPersona({
        ...formData,
        baseline_background: buildBaselineBackground(),
      })
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
    <main className="min-h-screen bg-muted gradient-apple-mesh">
      {/* Glass Header */}
      <header className="glass-panel">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-muted-foreground hover:text-soft-purple transition-colors mb-4 font-medium"
          >
            <ArrowLeft size={20} />
            Back to Personas
          </button>
          <h1 className="text-4xl font-display text-foreground font-bold animate-fade-in-apple">
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
                <div className="bg-lavender/20 p-3 rounded-apple-lg">
                  <User className="text-deep-purple" size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-display text-foreground font-bold">
                    Baseline Profile
                  </h2>
                  <p className="text-muted-foreground text-sm">
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

                {/* Starting Point - kept deliberately general; specific events belong to Experiences */}
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="label-apple text-base">Starting Point</h3>
                    <Tooltip content={HELP_CONTENT.persona.backstory.tooltip} />
                  </div>
                  <HelpText type="info">
                    Keep this general — the overall shape of their upbringing, not a list of events.
                    Specific moments (trauma, losses, achievements) get added next, one at a time, as{' '}
                    <strong>Experiences</strong>, after you create this persona.
                  </HelpText>

                  <div className="space-y-4 mt-4">
                    <div>
                      <label className="label-apple text-sm">Home environment growing up</label>
                      <textarea
                        required
                        value={origin.home_environment}
                        onChange={(e) => setOrigin({ ...origin, home_environment: e.target.value })}
                        rows={2}
                        placeholder="e.g., Stable and warm, but financially strained"
                        className="input-apple mt-1.5"
                      />
                    </div>

                    <div>
                      <label className="label-apple text-sm">Caregivers — who raised them, how reliable were they</label>
                      <textarea
                        required
                        value={origin.caregivers}
                        onChange={(e) => setOrigin({ ...origin, caregivers: e.target.value })}
                        rows={2}
                        placeholder="e.g., Raised mostly by mother; father present but emotionally distant"
                        className="input-apple mt-1.5"
                      />
                    </div>

                    <div>
                      <label className="label-apple text-sm">Anything else about their temperament or general environment (optional)</label>
                      <textarea
                        value={origin.other_notes}
                        onChange={(e) => setOrigin({ ...origin, other_notes: e.target.value })}
                        rows={2}
                        placeholder="e.g., Naturally curious and social as a young child"
                        className="input-apple mt-1.5"
                      />
                    </div>
                  </div>

                  {/* What to include checklist */}
                  <Checklist
                    title="What to include:"
                    items={HELP_CONTENT.persona.backstory.whatToInclude}
                  />

                  {/* What NOT to include - keeps this distinct from Experiences */}
                  <Checklist
                    title="Save for Experiences (don't add here):"
                    items={HELP_CONTENT.persona.backstory.whatNotToInclude}
                  />

                  <Examples
                    title="See examples"
                    examples={HELP_CONTENT.persona.backstory.examples.map(ex => ({
                      label: ex.title,
                      text: ex.text
                    }))}
                  />

                  <HelpText type="tip">
                    A sentence or two per question is enough — this just sets the starting point. You'll build out their actual story next.
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
              <div className="bg-apple-blue-50 border-l-4 border-soft-purple p-3 rounded">
                <p className="text-sm font-semibold text-apple-blue-800 mb-1">
                  Pro Tip
                </p>
                <p className="text-xs text-muted-foreground">
                  Keep it short and general here. Specific events belong on the next screen, as Experiences.
                </p>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2">
                  On This Page
                </h4>
                <ul className="space-y-2 text-xs text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>General home environment</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Who raised them & how reliable</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-apple-green">✓</span>
                    <span>Overall temperament</span>
                  </li>
                </ul>
              </div>

              <div className="border-t border-border pt-4">
                <h4 className="text-sm font-semibold text-foreground mb-2">
                  Comes Next
                </h4>
                <p className="text-xs text-muted-foreground">
                  Specific events — trauma, losses, achievements, relationships — get added one at a time as{' '}
                  <strong>Experiences</strong>, right after you create this persona.
                </p>
              </div>

              <div className="border-t border-border pt-4">
                <h4 className="text-sm font-semibold text-foreground mb-2">
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
