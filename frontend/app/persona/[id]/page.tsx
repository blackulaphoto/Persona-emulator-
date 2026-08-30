'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Plus, TrendingDown, TrendingUp, AlertCircle, Camera, Wand2, Trash2, Pencil } from 'lucide-react'
import { api, type Timeline } from '@/lib/api'
import { remixAPI, templatesAPI, type Template, type TemplateDetails } from '@/lib/api/templates'
import { useAuth } from '@/contexts/AuthContext'
import { Tooltip, HelpText } from '@/components/help/HelpComponents'
import { SITE_HELP } from '@/lib/help/SiteWideHelpContent'
import { RubixShell, RubixCard, RubixBadge, RubixMetric, RubixModal, RubixDrawer, RubixDrawerSection, RubixDelta } from '@/components/rubix'
import { attachmentStyleLabel, attachmentStyleTone } from '@/lib/rubix/attachmentStyle'
import type { AdaptationPattern, ClinicalPatternHypothesis } from '@/lib/api'

type DetailDrawerState =
  | { type: 'attachment' }
  | { type: 'starting' }
  | { type: 'pattern'; data: AdaptationPattern }
  | { type: 'hypothesis'; data: ClinicalPatternHypothesis }
  | null

export default function PersonaPage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [timeline, setTimeline] = useState<Timeline | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddExperience, setShowAddExperience] = useState(false)
  const [showAddSupport, setShowAddSupport] = useState(false)
  const [showCreateSnapshot, setShowCreateSnapshot] = useState(false)
  const [showTemplateRemix, setShowTemplateRemix] = useState(false)
  const [templates, setTemplates] = useState<Template[]>([])
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetails | null>(null)
  const [loadingTemplateDetails, setLoadingTemplateDetails] = useState(false)
  const [selectedExperienceIndices, setSelectedExperienceIndices] = useState<Set<number>>(new Set())
  const [applyingExperiences, setApplyingExperiences] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [showEditPersona, setShowEditPersona] = useState(false)
  const [detailDrawer, setDetailDrawer] = useState<DetailDrawerState>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) {
      loadTimeline()
      loadTemplates()
    }
  }, [params.id, user])

  async function handleDeletePersona() {
    if (!confirm(`Are you sure you want to delete "${persona.name}"? This action cannot be undone.`)) {
      return
    }

    setDeleting(true)
    try {
      await api.deletePersona(params.id)
      router.push('/personas')
    } catch (error) {
      console.error('Failed to delete persona:', error)
      alert('Failed to delete persona. Please try again.')
    } finally {
      setDeleting(false)
    }
  }

  async function loadTimeline() {
    try {
      const data = await api.getTimeline(params.id)
      setTimeline(data)
    } catch (error) {
      console.error('Failed to load timeline:', error)
    } finally {
      setLoading(false)
    }
  }

  async function loadTemplates() {
    setLoadingTemplates(true)
    try {
      const data = await templatesAPI.list()
      setTemplates(data)
    } catch (error) {
      // Feature may be disabled, fail silently
      console.log('Templates not available:', error)
      setTemplates([])
    } finally {
      setLoadingTemplates(false)
    }
  }

  async function handleSelectTemplate(templateId: string) {
    setLoadingTemplateDetails(true)
    try {
      const template = await templatesAPI.get(templateId)
      setSelectedTemplate(template)
      // Pre-select all experiences by default
      const allIndices = new Set(template.predefined_experiences.map((_, idx) => idx))
      setSelectedExperienceIndices(allIndices)
    } catch (error) {
      console.error('Failed to load template details:', error)
      alert('Failed to load template details')
    } finally {
      setLoadingTemplateDetails(false)
    }
  }

  async function handleApplyTemplateExperiences() {
    if (!selectedTemplate) return

    setApplyingExperiences(true)
    try {
      const indices = Array.from(selectedExperienceIndices).sort((a, b) => a - b)
      await templatesAPI.applyExperiences(params.id, selectedTemplate.id, indices)
      
      // Reload timeline to show new experiences
      await loadTimeline()

      // Close remix modal and reset state
      setShowTemplateRemix(false)
      setSelectedTemplate(null)
      setSelectedExperienceIndices(new Set())
      
      alert(`✓ Applied ${indices.length} experience${indices.length !== 1 ? 's' : ''} from template!`)
    } catch (error) {
      console.error('Failed to apply experiences:', error)
      alert('Failed to apply template experiences. Please try again.')
    } finally {
      setApplyingExperiences(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 13.5, color: 'rgba(210,232,255,0.65)' }}>Loading…</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  if (!timeline) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <RubixCard style={{ padding: 32, textAlign: 'center', maxWidth: 380 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>Persona not found</div>
          <button type="button" className="rubix-btn-primary" style={{ marginTop: 18 }} onClick={() => router.push('/personas')}>
            Back to Lives
          </button>
        </RubixCard>
      </div>
    )
  }

  const { persona } = timeline

  return (
    <RubixShell persona={{ id: persona.id, name: persona.name }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, marginBottom: 22, flexWrap: 'wrap' }}>
        <Link href="/personas" style={{ fontSize: 13, color: 'rgba(205,228,255,0.62)' }}>
          ← Lives
        </Link>
        <button
          type="button"
          onClick={handleDeletePersona}
          disabled={deleting}
          className="rubix-btn-danger"
          style={{ fontSize: 12.5 }}
        >
          {deleting ? 'Deleting…' : 'Delete this life'}
        </button>
      </div>

      <div style={{ maxWidth: 1420, display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* PERSON / NOW */}
        <RubixCard variant="hero" style={{ padding: 26 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div className="rubix-avatar" style={{ width: 58, height: 58, flex: '0 0 58px', fontSize: 20 }} aria-hidden="true">
                {persona.name.trim().charAt(0).toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em' }}>{persona.name}</div>
                <div style={{ marginTop: 4, fontSize: 13, color: 'rgba(214,235,255,0.7)' }}>
                  Age {persona.current_age} · {persona.experiences_count} experience{persona.experiences_count === 1 ? '' : 's'} · {persona.interventions_count} moment{persona.interventions_count === 1 ? '' : 's'} of support
                </div>
                <div style={{ marginTop: 6, display: 'flex', gap: 14 }}>
                  <button
                    type="button"
                    onClick={() => setShowEditPersona(true)}
                    style={{ fontSize: 12.5, color: 'rgba(205,228,255,0.65)', background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
                  >
                    Edit name and background
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailDrawer({ type: 'starting' })}
                    style={{ fontSize: 12.5, color: 'rgba(205,228,255,0.65)', background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
                  >
                    Starting conditions →
                  </button>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setDetailDrawer({ type: 'attachment' })}
              style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
              aria-label="Attachment detail"
            >
              <RubixBadge tone={attachmentStyleTone(persona.current_attachment_style)}>
                {attachmentStyleLabel(persona.current_attachment_style)}
              </RubixBadge>
            </button>
          </div>

          <div style={{ marginTop: 22, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button type="button" className="rubix-btn-primary" onClick={() => setShowAddExperience(true)}>
              + Add experience
            </button>
            <button type="button" className="rubix-btn-ghost" onClick={() => setShowAddSupport(true)}>
              + Add therapy
            </button>
            <button type="button" className="rubix-btn-ghost" onClick={() => setShowCreateSnapshot(true)}>
              Save snapshot
            </button>
            {templates.length > 0 && (
              <button type="button" className="rubix-btn-ghost" onClick={() => setShowTemplateRemix(true)}>
                Remix with template
              </button>
            )}
          </div>
        </RubixCard>

        {/* Personality Overview */}
        <PersonalityOverview persona={persona} />

        {/* Adaptations and evolving pattern hypotheses - each panel hides
            itself until the engine actually has something to show. */}
        {((persona.adaptation_patterns?.length ?? 0) > 0 ||
          (persona.clinical_pattern_hypotheses?.length ?? 0) > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AdaptationPatternsPanel patterns={persona.adaptation_patterns || []} onSelect={(p) => setDetailDrawer({ type: 'pattern', data: p })} />
            <PatternHypothesesPanel hypotheses={persona.clinical_pattern_hypotheses || []} onSelect={(h) => setDetailDrawer({ type: 'hypothesis', data: h })} />
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddExperience && (
        <AddExperienceModal
          personaId={params.id}
          currentAge={persona.current_age}
          onClose={() => setShowAddExperience(false)}
          onSuccess={() => {
            setShowAddExperience(false)
            loadTimeline()
          }}
        />
      )}
      {showAddSupport && (
        <AddInterventionModal
          personaId={params.id}
          currentAge={persona.current_age}
          onClose={() => setShowAddSupport(false)}
          onSuccess={() => {
            setShowAddSupport(false)
            loadTimeline()
          }}
        />
      )}

      {/* Template Remix Modal */}
      {showTemplateRemix && (
        <TemplateRemixModal
          personaId={params.id}
          templates={templates}
          selectedTemplate={selectedTemplate}
          loadingTemplateDetails={loadingTemplateDetails}
          selectedExperienceIndices={selectedExperienceIndices}
          applyingExperiences={applyingExperiences}
          onSelectTemplate={handleSelectTemplate}
          onToggleExperience={(index) => {
            const newSet = new Set(selectedExperienceIndices)
            if (newSet.has(index)) {
              newSet.delete(index)
            } else {
              newSet.add(index)
            }
            setSelectedExperienceIndices(newSet)
          }}
          onResetTemplate={() => {
            setSelectedTemplate(null)
            setSelectedExperienceIndices(new Set())
          }}
          onApply={handleApplyTemplateExperiences}
          onClose={() => {
            setShowTemplateRemix(false)
            setSelectedTemplate(null)
            setSelectedExperienceIndices(new Set())
          }}
          onSuccess={() => loadTimeline()}
        />
      )}

      {/* Snapshot creation modal - viewing/comparing saved snapshots now lives
          on the dedicated Compare route. */}
      {showCreateSnapshot && (
        <CreateSnapshotModal
          personaId={params.id}
          onClose={() => setShowCreateSnapshot(false)}
          onSuccess={() => setShowCreateSnapshot(false)}
        />
      )}

      {showEditPersona && (
        <EditPersonaModal
          persona={persona}
          onClose={() => setShowEditPersona(false)}
          onSuccess={async () => {
            setShowEditPersona(false)
            await loadTimeline()
          }}
        />
      )}

      <RubixDrawer
        open={detailDrawer !== null}
        onClose={() => setDetailDrawer(null)}
        kind={detailDrawer ? DETAIL_KIND_LABEL[detailDrawer.type] : ''}
        kindColor={detailDrawer ? DETAIL_KIND_COLOR[detailDrawer.type] : undefined}
        title={detailDrawer ? detailDrawerTitle(detailDrawer, persona) : ''}
      >
        {detailDrawer?.type === 'attachment' && <AttachmentDetail persona={persona} />}
        {detailDrawer?.type === 'starting' && <StartingConditionsDetail persona={persona} />}
        {detailDrawer?.type === 'pattern' && <PatternDetail pattern={detailDrawer.data} />}
        {detailDrawer?.type === 'hypothesis' && <HypothesisDetail hypothesis={detailDrawer.data} />}
      </RubixDrawer>
    </RubixShell>
  )
}

function EditPersonaModal({ persona, onClose, onSuccess }: {
  persona: Timeline['persona']
  onClose: () => void
  onSuccess: () => void
}) {
  const [name, setName] = useState(persona.name)
  const [background, setBackground] = useState(persona.baseline_background)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    try {
      await api.updatePersona(persona.id, { name: name.trim(), baseline_background: background.trim() })
      onSuccess()
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to update persona')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-background/50 flex items-center justify-center p-4 z-50">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-8 max-w-xl w-full space-y-5">
        <h2 className="text-2xl font-display">Edit Persona</h2>
        <input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)}
          className="w-full px-4 py-3 rounded-lg border-2 border-border" aria-label="Persona name" />
        <textarea required maxLength={1000} rows={6} value={background}
          onChange={(event) => setBackground(event.target.value)}
          className="w-full px-4 py-3 rounded-lg border-2 border-border resize-none"
          aria-label="Persona background" />
        <div className="flex gap-3">
          <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button type="submit" disabled={saving} className="btn-primary flex-1">
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  )
}

// Template Remix Modal Component
function TemplateRemixModal({
  personaId,
  templates,
  selectedTemplate,
  loadingTemplateDetails,
  selectedExperienceIndices,
  applyingExperiences,
  onSelectTemplate,
  onToggleExperience,
  onResetTemplate,
  onApply,
  onClose,
  onSuccess,
}: {
  personaId: string
  templates: Template[]
  selectedTemplate: TemplateDetails | null
  loadingTemplateDetails: boolean
  selectedExperienceIndices: Set<number>
  applyingExperiences: boolean
  onSelectTemplate: (templateId: string) => void
  onToggleExperience: (index: number) => void
  onResetTemplate: () => void
  onApply: () => void
  onClose: () => void
  onSuccess: () => void
}) {
  return (
    <div className="fixed inset-0 bg-background/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div className="p-6 border-b border-border flex items-center justify-between sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-2xl font-display text-foreground">Remix with Template Experiences</h2>
            <p className="text-muted-foreground text-sm mt-1">Select a template and choose which experiences to apply</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-2xl">
            ×
          </button>
        </div>

        <div className="p-6">
          {!selectedTemplate ? (
            <div>
              <h3 className="text-xl font-display text-foreground mb-4">Choose a Story Pattern</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="border-2 border-border rounded-xl p-4 hover:border-lavender transition-colors cursor-pointer"
                    onClick={() => onSelectTemplate(template.id)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-lg font-display text-foreground">{template.name}</h4>
                      <span className="text-xs px-2 py-1 bg-red-500/20 text-red-500 rounded-full">
                        {template.disorder_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-muted-foreground text-sm mb-3">{template.description}</p>
                    <div className="flex gap-4 text-xs text-muted-foreground">
                      <span>{template.experience_count} experiences</span>
                      <span>{template.intervention_count} moments of support</span>
                    </div>
                  </div>
                ))}
              </div>
              {templates.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  No templates available. Enable FEATURE_CLINICAL_TEMPLATES=true to use templates.
                </div>
              )}
            </div>
          ) : loadingTemplateDetails ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-deep-purple mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading template details...</p>
            </div>
          ) : (
            <div>
              <div className="mb-6">
                <button
                  onClick={onResetTemplate}
                  className="text-muted-foreground hover:text-foreground mb-4"
                >
                  ← Back to template selection
                </button>
                <h3 className="text-xl font-display text-foreground mb-2">{selectedTemplate.name}</h3>
                <p className="text-muted-foreground text-sm">{selectedTemplate.description}</p>
              </div>

              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-display text-foreground">Select Experiences to Apply</h4>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        selectedTemplate.predefined_experiences.forEach((_, idx) => {
                          if (!selectedExperienceIndices.has(idx)) {
                            onToggleExperience(idx)
                          }
                        })
                      }}
                      className="text-xs btn-secondary"
                    >
                      Select All
                    </button>
                    <button
                      onClick={() => {
                        selectedExperienceIndices.forEach(idx => onToggleExperience(idx))
                      }}
                      className="text-xs btn-secondary"
                    >
                      Deselect All
                    </button>
                  </div>
                </div>

                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {selectedTemplate.predefined_experiences.map((exp, idx) => (
                    <div
                      key={idx}
                      className={`border-2 rounded-xl p-4 cursor-pointer transition-colors ${
                        selectedExperienceIndices.has(idx)
                          ? 'border-deep-purple bg-deep-purple/10'
                          : 'border-border hover:border-border/30'
                      }`}
                      onClick={() => onToggleExperience(idx)}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={selectedExperienceIndices.has(idx)}
                          onChange={() => onToggleExperience(idx)}
                          className="mt-1"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <span className="text-sm font-medium text-foreground">Age {exp.age}</span>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              exp.valence === 'negative' ? 'bg-red-500/20 text-red-500' :
                              exp.valence === 'positive' ? 'bg-deep-purple/20 text-deep-purple' :
                              'bg-lavender/20/20 text-muted-foreground'
                            }`}>
                              {exp.valence}
                            </span>
                            <span className="text-xs px-2 py-1 bg-muted/20 text-foreground rounded-full">
                              {exp.intensity}
                            </span>
                            {exp.category && (
                              <span className="text-xs px-2 py-1 bg-background/10 text-foreground rounded-full">
                                {exp.category.replace(/_/g, ' ')}
                              </span>
                            )}
                          </div>
                          <p className="text-foreground text-sm mb-1">{exp.description}</p>
                          {exp.clinical_note && (
                            <p className="text-muted-foreground text-xs italic mt-1 border-l-2 border-border/30 pl-2">
                              {exp.clinical_note}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={onClose}
                    className="btn-secondary flex-1"
                    disabled={applyingExperiences}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={onApply}
                    className="btn-primary flex-1"
                    disabled={applyingExperiences || selectedExperienceIndices.size === 0}
                  >
                    {applyingExperiences 
                      ? 'Applying...' 
                      : `Apply ${selectedExperienceIndices.size} Experience${selectedExperienceIndices.size !== 1 ? 's' : ''}`
                    }
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function CreateSnapshotModal({
  personaId,
  onClose,
  onSuccess,
}: {
  personaId: string
  onClose: () => void
  onSuccess: () => void
}) {
  const [label, setLabel] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!label.trim()) {
      setError('Label is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await remixAPI.createSnapshot(personaId, label.trim(), description.trim() || undefined)
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create snapshot')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-background/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="text-2xl font-display text-foreground">Create Timeline Snapshot</h2>
          <Tooltip content={SITE_HELP.snapshot.whatIs} />
        </div>
        <HelpText type="info">
          <p className="mb-2">{SITE_HELP.snapshot.whatIs}</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            {[SITE_HELP.snapshot.howToUse].map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </HelpText>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-foreground font-medium">Label *</label>
              
            </div>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="w-full px-4 py-2 border border-border rounded-lg bg-white text-foreground focus:outline-none focus:border-deep-purple"
              placeholder="e.g., Baseline State"
              required
            />
          </div>
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-foreground font-medium">Description</label>
              
            </div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 border border-border rounded-lg bg-white text-foreground focus:outline-none focus:border-deep-purple"
              rows={3}
              placeholder="Optional description..."
            />
          </div>
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 text-red-500 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Snapshot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const BIG_FIVE_ACCENT: Record<string, string> = {
  openness: '#7fb2ff',
  conscientiousness: '#6fe3ff',
  extraversion: '#b39bff',
  agreeableness: '#6fe3b0',
  neuroticism: '#ff9282',
}

function PersonalityOverview({ persona }: { persona: any }) {
  const traits = [
    { name: 'Openness', key: 'openness', value: persona.current_personality.openness },
    { name: 'Conscientiousness', key: 'conscientiousness', value: persona.current_personality.conscientiousness },
    { name: 'Extraversion', key: 'extraversion', value: persona.current_personality.extraversion },
    { name: 'Agreeableness', key: 'agreeableness', value: persona.current_personality.agreeableness },
    { name: 'Neuroticism', key: 'neuroticism', value: persona.current_personality.neuroticism },
  ] as const

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Personality Traits */}
      <RubixCard style={{ padding: 24 }}>
        <div style={{ fontSize: 15.5, fontWeight: 700 }}>How they think &amp; feel</div>
        <div style={{ marginTop: 3, fontSize: 12.5, color: 'rgba(214,235,255,0.65)' }}>Current Big Five — reflects everything that's happened so far.</div>
        <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {traits.map((trait) => {
            const score = Math.round(trait.value * 100)
            return (
              <RubixMetric
                key={trait.name}
                label={trait.name}
                valueLabel={`${score}%`}
                percent={score}
                accent={BIG_FIVE_ACCENT[trait.key]}
              />
            )
          })}
        </div>
      </RubixCard>

      {/* What They're Navigating - driven by current psychological state */}
      <CurrentStatePanel persona={persona} />
    </div>
  )
}

/**
 * "What They're Navigating" - now driven primarily by current_state (the fast
 * tier that actually reacts to events), with the evidence-gated trauma-marker
 * list shown underneath when it has something to say.
 *
 * Previously this read current_trauma_markers alone, which sits behind a
 * high evidence threshold - so a persona whose state showed trust 0.06 and
 * threat sensitivity 0.74 still rendered "All is well right now". That
 * message now appears only when the state genuinely supports it.
 */
const STATE_DIMENSIONS: Record<string, { label: string; adverseWhen: 'high' | 'low'; highLabel: string; lowLabel: string }> = {
  trust: { label: 'Trust', adverseWhen: 'low', highLabel: 'Open to trusting', lowLabel: 'Guarded about trusting' },
  threat_sensitivity: { label: 'Threat Sensitivity', adverseWhen: 'high', highLabel: 'On alert', lowLabel: 'Feels safe' },
  mood: { label: 'Mood', adverseWhen: 'low', highLabel: 'Buoyant', lowLabel: 'Low' },
  regulation: { label: 'Emotional Regulation', adverseWhen: 'low', highLabel: 'Steady', lowLabel: 'Easily overwhelmed' },
  avoidance: { label: 'Avoidance', adverseWhen: 'high', highLabel: 'Pulling away', lowLabel: 'Staying present' },
  relational_security: { label: 'Relational Security', adverseWhen: 'low', highLabel: 'Secure with others', lowLabel: 'Unsure where they stand' },
}

// Only surface dimensions that have actually moved off neutral - dumping every
// variable at 0.5 would be noise, not insight.
const STATE_NEUTRAL = 0.5
const STATE_NOTABLE_DELTA = 0.08

function CurrentStatePanel({ persona }: { persona: any }) {
  const state: Record<string, number> = persona.current_state || {}

  const dimensions = Object.entries(state)
    .filter(([key]) => STATE_DIMENSIONS[key])
    .map(([key, value]) => {
      const meta = STATE_DIMENSIONS[key]
      const delta = value - STATE_NEUTRAL
      const isAdverse = meta.adverseWhen === 'high' ? delta > 0 : delta < 0
      return { key, value, meta, delta, isAdverse, magnitude: Math.abs(delta) }
    })
    .filter((d) => d.magnitude >= STATE_NOTABLE_DELTA)
    .sort((a, b) => b.magnitude - a.magnitude)

  const markers: string[] = persona.current_trauma_markers || []
  const hasSomethingToShow = dimensions.length > 0 || markers.length > 0

  return (
    <RubixCard style={{ padding: 24 }}>
      <div style={{ fontSize: 15.5, fontWeight: 700 }}>What they&apos;re navigating</div>
      <div style={{ marginTop: 3, fontSize: 12.5, color: 'rgba(214,235,255,0.65)' }}>Fast-moving state — reacts to a single event far more readily than personality does.</div>

      {!hasSomethingToShow ? (
        <div style={{ textAlign: 'center', padding: '28px 0 8px', fontSize: 13.5, color: 'rgba(214,235,255,0.6)' }}>All is well right now</div>
      ) : (
        <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {dimensions.map((d) => (
            <RubixMetric
              key={d.key}
              label={d.meta.label}
              valueLabel={d.delta > 0 ? d.meta.highLabel : d.meta.lowLabel}
              percent={Math.round(d.value * 100)}
              accent={d.isAdverse ? '#ff9282' : '#6fe3b0'}
            />
          ))}

          {markers.length > 0 && (
            <div style={{ paddingTop: 8 }}>
              <div style={{ fontSize: 11.5, color: 'rgba(214,235,255,0.55)', marginBottom: 8 }}>
                Patterns with enough accumulated evidence to name:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {markers.map((marker: string, i: number) => (
                  <RubixBadge key={i} tone="caution">
                    {marker.replace(/_/g, ' ')}
                  </RubixBadge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </RubixCard>
  )
}

const PATTERN_STATUS_STYLES: Record<string, string> = {
  emerging: 'bg-lavender/40 text-deep-purple',
  established: 'bg-deep-purple/20 text-deep-purple',
  weakening: 'bg-muted/40 text-muted-foreground',
  resolved: 'bg-muted/30 text-muted-foreground',
}

const HYPOTHESIS_DIRECTION_LABEL: Record<string, string> = {
  strengthening: '↑ strengthening',
  weakening: '↓ weakening',
  stable: '— steady',
}

function titleCase(value: string) {
  // Handles both snake_case (adaptation_strategy) and the camelCase a few
  // fields use (foundational_environment_signals' keys, e.g. caregiverReliability).
  return value
    .replace(/_/g, ' ')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

const DETAIL_KIND_LABEL: Record<NonNullable<DetailDrawerState>['type'], string> = {
  attachment: 'ATTACHMENT',
  starting: 'STARTING CONDITIONS',
  pattern: 'ADAPTATION PATTERN',
  hypothesis: 'PATTERN BEING CONSIDERED',
}
const DETAIL_KIND_COLOR: Record<NonNullable<DetailDrawerState>['type'], string> = {
  attachment: '#b39bff',
  starting: '#7fb2ff',
  pattern: '#7fb2ff',
  hypothesis: '#b39bff',
}
function detailDrawerTitle(d: NonNullable<DetailDrawerState>, persona: any): string {
  if (d.type === 'attachment') return 'Attachment'
  if (d.type === 'starting') return 'Where they started'
  if (d.type === 'pattern') return d.data.pattern_name
  return titleCase(d.data.pattern_key)
}

const ATTACHMENT_DIMENSION_LABELS: Record<string, string> = {
  attachment_anxiety: 'Attachment anxiety',
  attachment_avoidance: 'Attachment avoidance',
  relational_security: 'Relational security',
}

/** Real baseline -> current -> delta for style and each dimension. Never fabricates a transition age unless the data genuinely supports it. */
function AttachmentDetail({ persona }: { persona: any }) {
  const baselineStyle = persona.baseline_attachment_style
  const currentStyle = persona.current_attachment_style
  const baselineDims = persona.baseline_attachment_dimensions || {}
  const currentDims = persona.current_attachment_dimensions || {}
  const delta = persona.attachment_delta || {}
  const dimKeys = Array.from(new Set([...Object.keys(baselineDims), ...Object.keys(currentDims)]))

  return (
    <>
      <RubixDrawerSection label="STYLE">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {baselineStyle && baselineStyle !== currentStyle ? (
            <>
              <RubixBadge tone={attachmentStyleTone(baselineStyle)}>{attachmentStyleLabel(baselineStyle)}</RubixBadge>
              <span style={{ color: 'rgba(214,235,255,0.4)' }}>→</span>
            </>
          ) : null}
          <RubixBadge tone={attachmentStyleTone(currentStyle)}>{attachmentStyleLabel(currentStyle)}</RubixBadge>
        </div>
      </RubixDrawerSection>

      {dimKeys.length > 0 && (
        <RubixDrawerSection label="DIMENSIONS">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {dimKeys.map((key) => (
              <RubixMetric
                key={key}
                label={ATTACHMENT_DIMENSION_LABELS[key] || titleCase(key)}
                valueLabel={currentDims[key] != null ? currentDims[key].toFixed(2) : '—'}
                percent={Math.round((currentDims[key] ?? 0) * 100)}
                markerPercent={baselineDims[key] != null ? Math.round(baselineDims[key] * 100) : undefined}
                accent="#b39bff"
              />
            ))}
          </div>
        </RubixDrawerSection>
      )}

      {Object.keys(delta).length > 0 && (
        <RubixDrawerSection label="CHANGE SINCE BASELINE">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(delta).map(([key, value]: [string, any]) => (
              <RubixDelta
                key={key}
                label={`${ATTACHMENT_DIMENSION_LABELS[key] || titleCase(key)} ${value > 0 ? '+' : ''}${value.toFixed(2)}`}
                tone={key === 'relational_security' ? (value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral') : (value < 0 ? 'positive' : value > 0 ? 'negative' : 'neutral')}
              />
            ))}
          </div>
        </RubixDrawerSection>
      )}
    </>
  )
}

/** Real baseline snapshot - not an intake form, just what was recorded before any life events were added. */
function StartingConditionsDetail({ persona }: { persona: any }) {
  const signals: Record<string, number> = persona.foundational_environment_signals || {}
  const signalEntries = Object.entries(signals).filter(([, v]) => v !== 0)

  return (
    <>
      <RubixDrawerSection label="BACKGROUND" meta={`AGE ${persona.baseline_age}`}>
        <div style={{ fontSize: 14.5, lineHeight: 1.65, color: 'rgba(230,242,255,0.92)', whiteSpace: 'pre-wrap' }}>{persona.baseline_background}</div>
      </RubixDrawerSection>

      <RubixDrawerSection label="IDENTITY">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13.5 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'rgba(214,235,255,0.6)' }}>Gender</span>
            <span>{persona.baseline_gender}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'rgba(214,235,255,0.6)' }}>Starting age</span>
            <span>{persona.baseline_age}</span>
          </div>
          {persona.baseline_attachment_style && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'rgba(214,235,255,0.6)' }}>Starting attachment</span>
              <RubixBadge tone={attachmentStyleTone(persona.baseline_attachment_style)}>{attachmentStyleLabel(persona.baseline_attachment_style)}</RubixBadge>
            </div>
          )}
        </div>
      </RubixDrawerSection>

      {persona.baseline_personality && (
        <RubixDrawerSection label="STARTING PERSONALITY">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Object.entries(persona.baseline_personality as Record<string, number>).map(([trait, value]) => (
              <RubixMetric key={trait} label={titleCase(trait)} valueLabel={`${Math.round(value * 100)}%`} percent={value * 100} accent="#7fb2ff" />
            ))}
          </div>
        </RubixDrawerSection>
      )}

      {signalEntries.length > 0 && (
        <RubixDrawerSection label="ENVIRONMENT SIGNALS (INFERRED)">
          <div style={{ fontSize: 12, color: 'rgba(200,226,255,0.55)', marginBottom: 8 }}>
            What Rubicks read out of the background text above, on a -5 to +5 scale.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {signalEntries.map(([key, value]) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: 'rgba(214,235,255,0.7)' }}>{titleCase(key)}</span>
                <RubixDelta label={value > 0 ? `+${value}` : String(value)} tone={value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'} />
              </div>
            ))}
          </div>
        </RubixDrawerSection>
      )}
    </>
  )
}

/** Real reinforcement_history - a genuine chronological record, not a fabricated line chart. */
function PatternDetail({ pattern }: { pattern: AdaptationPattern }) {
  return (
    <>
      <RubixDrawerSection label="STATUS" meta={pattern.confidence != null ? `${pattern.confidence}%` : undefined}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <RubixBadge tone={PATTERN_STATUS_TONE[pattern.status] || 'muted'}>{pattern.status}</RubixBadge>
          {pattern.adaptation_strategy && <span style={{ fontSize: 13.5, color: 'rgba(226,240,255,0.85)' }}>{titleCase(pattern.adaptation_strategy)}</span>}
        </div>
        {pattern.first_emerged_age != null && (
          <div style={{ marginTop: 8, fontSize: 12.5, color: 'rgba(200,226,255,0.6)' }}>First seen around age {pattern.first_emerged_age}</div>
        )}
      </RubixDrawerSection>

      {pattern.reinforcement_history && pattern.reinforcement_history.length > 0 && (
        <RubixDrawerSection label="HISTORY">
          <div style={{ position: 'relative', paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ position: 'absolute', left: 6, top: 10, bottom: 10, width: 2, borderRadius: 2, background: 'linear-gradient(180deg, rgba(200,232,255,0.7), rgba(150,205,255,0.15))' }} />
            {pattern.reinforcement_history.map((h, i) => (
              <div key={i} style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 11, flexWrap: 'wrap' }}>
                <div style={{ position: 'absolute', left: -18, width: 10, height: 10, borderRadius: 999, background: '#7fb2ff', boxShadow: '0 0 10px #7fb2ff' }} />
                <div style={{ fontSize: 13, fontWeight: 700 }}>{h.age != null ? `Age ${h.age}` : '—'}</div>
                <RubixBadge tone={h.effect === 'weakened' ? 'caution' : 'muted'}>{String(h.effect || 'noted')}</RubixBadge>
              </div>
            ))}
          </div>
        </RubixDrawerSection>
      )}
    </>
  )
}

/** Equal visual weight for supporting and contradicting evidence - never framed as diagnosis. */
function HypothesisDetail({ hypothesis }: { hypothesis: ClinicalPatternHypothesis }) {
  return (
    <>
      <RubixDrawerSection label="STATUS" meta={hypothesis.confidence != null ? `${hypothesis.confidence}%` : undefined}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <RubixBadge tone="muted">{hypothesis.status}</RubixBadge>
          {hypothesis.direction && <span style={{ fontSize: 13, color: 'rgba(214,235,255,0.65)' }}>{HYPOTHESIS_DIRECTION_LABEL[hypothesis.direction] || hypothesis.direction}</span>}
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: 'rgba(200,226,255,0.55)' }}>
          A working hypothesis based on this person&apos;s history so far — not a diagnosis. It moves up and down as more of their life is added.
        </div>
        {hypothesis.opened_at_age != null && (
          <div style={{ marginTop: 8, fontSize: 12.5, color: 'rgba(200,226,255,0.6)' }}>First considered around age {hypothesis.opened_at_age}</div>
        )}
      </RubixDrawerSection>

      <RubixDrawerSection label="SUPPORTING EVIDENCE" meta={String(hypothesis.supporting_evidence?.length ?? 0)}>
        {hypothesis.supporting_evidence && hypothesis.supporting_evidence.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {hypothesis.supporting_evidence.map((e, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 8, height: 8, borderRadius: 3, marginTop: 6, flex: '0 0 8px', background: '#6fe3b0', boxShadow: '0 0 9px #6fe3b0' }} />
                <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'rgba(226,240,255,0.88)' }}>{e.description || 'Evidence recorded'}{e.age != null ? ` (age ${e.age})` : ''}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: 13, color: 'rgba(200,226,255,0.5)' }}>None yet.</div>
        )}
      </RubixDrawerSection>

      <RubixDrawerSection label="CONTRADICTING EVIDENCE" meta={String(hypothesis.contradicting_evidence?.length ?? 0)}>
        {hypothesis.contradicting_evidence && hypothesis.contradicting_evidence.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {hypothesis.contradicting_evidence.map((e, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 8, height: 8, borderRadius: 3, marginTop: 6, flex: '0 0 8px', background: '#ff9282', boxShadow: '0 0 9px #ff9282' }} />
                <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'rgba(226,240,255,0.88)' }}>{e.description || 'Evidence recorded'}{e.age != null ? ` (age ${e.age})` : ''}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: 13, color: 'rgba(200,226,255,0.5)' }}>None yet.</div>
        )}
      </RubixDrawerSection>

      {hypothesis.developmental_precursors && hypothesis.developmental_precursors.length > 0 && (
        <RubixDrawerSection label="DEVELOPMENTAL PRECURSORS">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {hypothesis.developmental_precursors.map((p, i) => <RubixBadge key={i} tone="muted">{titleCase(p)}</RubixBadge>)}
          </div>
        </RubixDrawerSection>
      )}
    </>
  )
}

/**
 * How the persona has learned to cope, and how established each adaptation has
 * become. This is the layer that shows continuity across different kinds of
 * events - several unrelated experiences can reinforce one adaptation.
 */
const PATTERN_STATUS_TONE: Record<string, 'violet' | 'positive' | 'caution' | 'muted'> = {
  emerging: 'violet',
  established: 'positive',
  weakening: 'caution',
  resolved: 'muted',
}

function AdaptationPatternsPanel({ patterns, onSelect }: { patterns: any[]; onSelect: (p: any) => void }) {
  if (!patterns || patterns.length === 0) return null

  return (
    <RubixCard style={{ padding: 24 }}>
      <div style={{ fontSize: 15.5, fontWeight: 700 }}>How they&apos;ve learned to cope</div>
      <div style={{ marginTop: 3, fontSize: 12.5, color: 'rgba(214,235,255,0.65)', lineHeight: 1.5 }}>
        Adaptations developed in response to what happened to them. These strengthen as related experiences reinforce them.
      </div>
      <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {patterns.map((pattern, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onSelect(pattern)}
            style={{ display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: 'inherit' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 7 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                <span style={{ fontSize: 13.5, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{pattern.pattern_name}</span>
                <RubixBadge tone={PATTERN_STATUS_TONE[pattern.status] || 'muted'}>{pattern.status}</RubixBadge>
              </div>
              {pattern.confidence !== null && pattern.confidence !== undefined && (
                <span style={{ fontSize: 12, color: 'rgba(214,235,255,0.6)', whiteSpace: 'nowrap' }}>{pattern.confidence}%</span>
              )}
            </div>
            <div className="rubix-meter-track">
              <div className="rubix-meter-fill" style={{ width: `${pattern.confidence ?? 5}%`, background: 'linear-gradient(90deg, rgba(255,255,255,0.35), #7fb2ff)', boxShadow: '0 0 10px #7fb2ff' }} />
            </div>
            {pattern.adaptation_strategy && (
              <p style={{ marginTop: 5, fontSize: 12, color: 'rgba(214,235,255,0.6)' }}>
                {titleCase(pattern.adaptation_strategy)}
                {pattern.first_emerged_age !== null && pattern.first_emerged_age !== undefined
                  ? ` · first seen around age ${pattern.first_emerged_age}`
                  : ''}
              </p>
            )}
          </button>
        ))}
      </div>
    </RubixCard>
  )
}

/**
 * Evolving pattern-match hypotheses. Deliberately shows low-confidence
 * hypotheses too - watching the engine consider and revise a pattern is the
 * point. Copy here must never imply diagnosis.
 */
function PatternHypothesesPanel({ hypotheses, onSelect }: { hypotheses: any[]; onSelect: (h: any) => void }) {
  if (!hypotheses || hypotheses.length === 0) return null

  return (
    <RubixCard style={{ padding: 24 }}>
      <div style={{ fontSize: 15.5, fontWeight: 700 }}>Patterns being considered</div>
      <div style={{ marginTop: 3, fontSize: 12.5, color: 'rgba(214,235,255,0.65)', lineHeight: 1.5 }}>
        How closely this person&apos;s history so far resembles known psychological patterns. Working hypotheses, not diagnoses — they shift as more of their life is added.
      </div>
      <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {hypotheses.map((h, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onSelect(h)}
            style={{ display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: 'inherit' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 7 }}>
              <span style={{ fontSize: 13.5, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{titleCase(h.pattern_key)}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
                {h.direction && (
                  <span style={{ fontSize: 11.5, color: 'rgba(214,235,255,0.6)' }}>{HYPOTHESIS_DIRECTION_LABEL[h.direction] || ''}</span>
                )}
                {h.confidence !== null && h.confidence !== undefined && (
                  <span style={{ fontSize: 12, color: 'rgba(214,235,255,0.6)' }}>{h.confidence}%</span>
                )}
              </div>
            </div>
            <div className="rubix-meter-track">
              <div className="rubix-meter-fill" style={{ width: `${h.confidence ?? 5}%`, background: 'linear-gradient(90deg, rgba(255,255,255,0.35), #b39bff)', boxShadow: '0 0 10px #b39bff' }} />
            </div>
          </button>
        ))}
      </div>
    </RubixCard>
  )
}

// Add modals for Experience and Support (simplified versions for now)
function AddExperienceModal({ personaId, currentAge, onClose, onSuccess }: any) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    user_description: '',
    age_at_event: currentAge,
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.addExperience(personaId, formData)
      onSuccess()
    } catch (error) {
      alert('Failed to add experience')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-background/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="text-3xl font-display text-foreground">Add a Moment That Matters</h2>
          <Tooltip content={SITE_HELP.experience.pageHelp.content} />
        </div>
        <HelpText type="info">{SITE_HELP.experience.whatIs}</HelpText>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-foreground">
                Age at Event
              </label>
              <Tooltip content={SITE_HELP.experience.age.tooltip} />
            </div>
            <input
              type="number"
              required
              min={0}
              max={120}
              value={formData.age_at_event}
              onChange={(e) => setFormData({ ...formData, age_at_event: parseInt(e.target.value) })}
              className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Add experiences at any age (0-120) to build complete life history
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-foreground">
                What happened?
              </label>
              <Tooltip content={SITE_HELP.experience.description.tooltip} />
            </div>
            <textarea
              required
              rows={6}
              value={formData.user_description}
              onChange={(e) => setFormData({ ...formData, user_description: e.target.value })}
              className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none resize-none"
              placeholder="Describe the experience in detail..."
            />
            <p className="text-xs text-muted-foreground mt-2">
              AI will analyze the psychological impact based on trauma research and developmental psychology
            </p>
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? 'Considering how this helps...' : 'Add Experience'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const THERAPY_TYPES = [
  { value: 'CBT', label: 'CBT (Cognitive Behavioral Therapy)' },
  { value: 'ACT', label: 'ACT (Acceptance & Commitment Therapy)' },
  { value: 'EMDR', label: 'EMDR (Eye Movement Desensitization)' },
  { value: 'IFS', label: 'IFS (Internal Family Systems)' },
  { value: 'DBT', label: 'DBT (Dialectical Behavior Therapy)' },
  { value: 'Psychodynamic', label: 'Psychodynamic Therapy' },
  { value: 'Somatic_Experiencing', label: 'Somatic Experiencing' },
  { value: 'ERP', label: 'ERP (Exposure & Response Prevention)' },
]
const DURATIONS = [
  { value: '3_months', label: '3 months' },
  { value: '6_months', label: '6 months' },
  { value: '1_year', label: '1 year' },
  { value: '2_years', label: '2 years' },
]
const INTENSITIES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'twice_weekly', label: 'Twice weekly' },
]

function AddInterventionModal({ personaId, currentAge, onClose, onSuccess }: any) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    therapy_type: 'CBT',
    duration: '6_months',
    intensity: 'weekly',
    age_at_intervention: currentAge,
    user_notes: '',
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await api.addIntervention(personaId, formData)
      onSuccess()
    } catch (err) {
      console.error('Support error:', err)
      setError(err instanceof Error ? err.message : 'Failed to add support')
    } finally {
      setLoading(false)
    }
  }

  return (
    <RubixModal
      open
      onClose={onClose}
      eyebrow="ADD THERAPY / SUPPORT"
      title="Apply support to their life"
      subtitle="Support is another force acting on their trajectory. It applies from the age you choose forward."
      width={520}
    >
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div>
            <label className="rubix-field-label" htmlFor="iv-age">AGE</label>
            <input
              id="iv-age"
              type="number"
              required
              min={0}
              max={120}
              className="rubix-input"
              style={{ marginTop: 9, width: '100%' }}
              value={formData.age_at_intervention}
              onChange={(e) => setFormData({ ...formData, age_at_intervention: parseInt(e.target.value, 10) })}
            />
          </div>
          <div>
            <label className="rubix-field-label" htmlFor="iv-type">TYPE</label>
            <select
              id="iv-type"
              className="rubix-input"
              style={{ marginTop: 9, width: '100%' }}
              value={formData.therapy_type}
              onChange={(e) => setFormData({ ...formData, therapy_type: e.target.value })}
            >
              {THERAPY_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="rubix-field-label" htmlFor="iv-duration">DURATION</label>
            <select
              id="iv-duration"
              className="rubix-input"
              style={{ marginTop: 9, width: '100%' }}
              value={formData.duration}
              onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
            >
              {DURATIONS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          </div>
          <div>
            <div className="rubix-field-label">INTENSITY</div>
            <div style={{ marginTop: 9, display: 'flex', gap: 7 }}>
              {INTENSITIES.map((i) => {
                const active = formData.intensity === i.value
                return (
                  <button
                    key={i.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, intensity: i.value })}
                    aria-pressed={active}
                    style={{
                      flex: 1, padding: '12px 0', borderRadius: 12, textAlign: 'center', cursor: 'pointer', fontSize: 12.5, fontWeight: active ? 700 : 500,
                      color: active ? '#04281c' : 'rgba(214,235,255,0.75)',
                      background: active ? 'linear-gradient(160deg,#9df0c8,#4fd39c)' : 'rgba(255,255,255,0.07)',
                      border: `1px solid ${active ? 'transparent' : 'rgba(175,212,255,0.18)'}`,
                    }}
                  >
                    {i.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div style={{ marginTop: 14 }}>
          <label className="rubix-field-label" htmlFor="iv-notes">NOTES</label>
          <textarea
            id="iv-notes"
            className="rubix-textarea"
            style={{ marginTop: 9, width: '100%', minHeight: 76 }}
            value={formData.user_notes}
            onChange={(e) => setFormData({ ...formData, user_notes: e.target.value })}
            placeholder="Optional — what the support focused on."
          />
        </div>

        {error && (
          <div style={{ marginTop: 14, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
            {error}
          </div>
        )}

        <div style={{ marginTop: 22, display: 'flex', alignItems: 'center', gap: 11, justifyContent: 'flex-end' }}>
          <button type="button" className="rubix-btn-ghost" onClick={onClose} disabled={loading}>Cancel</button>
          <button type="submit" className="rubix-btn-primary" disabled={loading}>
            {loading ? 'Considering how this helps…' : 'Apply support'}
          </button>
        </div>
      </form>
    </RubixModal>
  )
}
