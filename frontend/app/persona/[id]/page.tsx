'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Sparkles, Pill, TrendingDown, TrendingUp, AlertCircle, Camera, GitCompare, Wand2, Trash2 } from 'lucide-react'
import { api, type Timeline, type TimelineEvent } from '@/lib/api'
import { remixAPI, templatesAPI, type TimelineSnapshot, type Template, type TemplateDetails } from '@/lib/api/templates'
import { useAuth } from '@/contexts/AuthContext'
import { PageHelpBanner, QuickTip, TraitHelp, EmptyStateWithHelp } from '@/components/help/PageHelpComponents'
import { Tooltip, HelpText } from '@/components/help/HelpComponents'
import { SITE_HELP } from '@/lib/help/SiteWideHelpContent'
import ChatBox from './ChatBox'
import SnapshotComparisonView from '@/components/templates/SnapshotComparison'
import PersonaNarrative from '@/components/PersonaNarrative'

export default function PersonaPage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [timeline, setTimeline] = useState<Timeline | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'timeline' | 'narrative'>('timeline')
  const [showAddExperience, setShowAddExperience] = useState(false)
  const [showAddSupport, setShowAddSupport] = useState(false)
  const [snapshots, setSnapshots] = useState<TimelineSnapshot[]>([])
  const [loadingSnapshots, setLoadingSnapshots] = useState(false)
  const [showCreateSnapshot, setShowCreateSnapshot] = useState(false)
  const [showSnapshotComparison, setShowSnapshotComparison] = useState(false)
  const [comparisonSnapshot1, setComparisonSnapshot1] = useState<string | null>(null)
  const [comparisonSnapshot2, setComparisonSnapshot2] = useState<string | null>(null)
  const [showTemplateRemix, setShowTemplateRemix] = useState(false)
  const [templates, setTemplates] = useState<Template[]>([])
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetails | null>(null)
  const [loadingTemplateDetails, setLoadingTemplateDetails] = useState(false)
  const [selectedExperienceIndices, setSelectedExperienceIndices] = useState<Set<number>>(new Set())
  const [applyingExperiences, setApplyingExperiences] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) {
      loadTimeline()
      loadSnapshots()
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

  async function loadSnapshots() {
    setLoadingSnapshots(true)
    try {
      const data = await remixAPI.listSnapshots(params.id)
      setSnapshots(data)
    } catch (error) {
      // Feature may be disabled, fail silently
      console.log('Snapshots not available (feature may be disabled):', error)
      setSnapshots([])
    } finally {
      setLoadingSnapshots(false)
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
      await loadSnapshots()
      
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

  if (authLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-deep-purple border-t-transparent mx-auto mb-4"></div>
          <p className="text-muted-foreground font-['Outfit']">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-muted gradient-apple-mesh flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-deep-purple border-t-transparent"></div>
          <p className="mt-4 text-muted-foreground">Loading persona...</p>
        </div>
      </div>
    )
  }

  if (!timeline) {
    return (
      <div className="min-h-screen bg-muted gradient-apple-mesh flex items-center justify-center">
        <div className="text-center">
          <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
          <h2 className="text-2xl font-display text-foreground mb-2">Persona Not Found</h2>
          <button onClick={() => router.push('/')} className="btn-primary mt-4">
            Return Home
          </button>
        </div>
      </div>
    )
  }

  const { persona } = timeline

  return (
    <main className="min-h-screen bg-muted gradient-apple-mesh">
      {/* Header */}
      <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => router.push('/personas')}
              className="flex items-center gap-2 text-muted-foreground hover:text-deep-purple transition-colors"
            >
              <ArrowLeft size={20} />
              Back to Personas
            </button>
            <button
              onClick={handleDeletePersona}
              disabled={deleting}
              className="flex items-center gap-2 text-red-500 hover:text-red-500/80 transition-colors text-sm"
              title="Delete this persona"
            >
              <Trash2 size={16} />
              {deleting ? 'Deleting...' : 'Delete Persona'}
            </button>
          </div>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-display text-foreground mb-2">
                {persona.name}
              </h1>
              <div className="flex items-center gap-4 text-muted-foreground text-sm">
                <span>Age {persona.current_age}</span>
                <span>•</span>
                <span>{persona.experiences_count} experiences</span>
                <span>•</span>
                <span>{persona.interventions_count} moments of support</span>
              </div>
            </div>
            <div className="flex gap-2 md:gap-3 flex-wrap items-center">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setShowAddExperience(true)}
                  className="btn-secondary flex items-center gap-2 text-sm md:text-base"
                >
                  <Plus size={18} />
                  <span className="hidden xs:inline">Add</span> Experience
                </button>
                <Tooltip content={SITE_HELP.experience.tooltip} position="bottom" />
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setShowAddSupport(true)}
                  className="btn-primary flex items-center gap-2 text-sm md:text-base"
                >
                  <Pill size={18} />
                  <span className="hidden xs:inline">Add</span> Therapy
                </button>
                <Tooltip content={SITE_HELP.intervention.tooltip} position="bottom" />
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setShowCreateSnapshot(true)}
                  className="btn-secondary flex items-center gap-2 text-sm md:text-base"
                  title="Create timeline snapshot"
                >
                  <Camera size={18} />
                  <span className="hidden sm:inline">Save</span> Snapshot
                </button>
                <Tooltip content={SITE_HELP.snapshot.tooltip} position="bottom" />
              </div>
              {templates.length > 0 && (
                <button
                  onClick={() => setShowTemplateRemix(true)}
                  className="btn-secondary flex items-center gap-2 text-sm md:text-base"
                  title="Remix persona with template experiences"
                >
                  <Wand2 size={18} />
                  <span className="hidden sm:inline">Remix</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-12">
        <PageHelpBanner pageKey="personaDetail" />
        <div className="mb-6">
          <QuickTip tip="Hover the ? icons to see what each section means." />
        </div>
        {/* Personality Overview */}
        <PersonalityOverview persona={persona} />

        {/* Tab Navigation */}
        <div className="mt-12 border-b border-border">
          <nav className="flex space-x-4 md:space-x-8 overflow-x-auto">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`pb-4 px-2 font-medium transition-colors whitespace-nowrap text-sm md:text-base ${
                activeTab === 'timeline'
                  ? 'border-b-2 border-deep-purple text-deep-purple'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <span className="hidden sm:inline">Timeline & Snapshots</span>
              <span className="sm:hidden">Timeline</span>
            </button>
            <button
              onClick={() => setActiveTab('narrative')}
              className={`pb-4 px-2 font-medium transition-colors whitespace-nowrap text-sm md:text-base ${
                activeTab === 'narrative'
                  ? 'border-b-2 border-deep-purple text-deep-purple'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              📖 Narrative
            </button>
          </nav>
        </div>

        {/* Timeline Tab Content */}
        {activeTab === 'timeline' && (
          <>
            {/* Snapshots Section */}
            <div className="mt-12">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h2 className="text-3xl font-display text-foreground">Moments in Time</h2>
                  <Tooltip content={SITE_HELP.snapshot.whatIs} />
                </div>
                {snapshots.length >= 2 && (
                  <button
                    onClick={() => {
                      setComparisonSnapshot1(snapshots[0].id)
                      setComparisonSnapshot2(snapshots[1].id)
                      setShowSnapshotComparison(true)
                    }}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <GitCompare size={18} />
                    Compare Snapshots
                  </button>
                )}
              </div>
              <HelpText type="info">
                <p className="mb-2">{SITE_HELP.snapshot.whatIs}</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>{SITE_HELP.snapshot.howToUse}</li>
                </ul>
              </HelpText>
              {snapshots.length === 0 ? (
                <EmptyStateWithHelp
                  icon="📸"
                  title="No snapshots yet"
                  description="Capture key moments to track how therapy and experiences change the persona."
                  actionButton={{
                    text: 'Create Snapshot',
                    onClick: () => setShowCreateSnapshot(true),
                    helpKey: 'snapshot'
                  }}
                  helpItems={[SITE_HELP.snapshot.howToUse]}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                  {snapshots.map((snapshot) => (
                    <div
                      key={snapshot.id}
                      className="bg-white border-2 border-border rounded-xl p-4 hover:border-lavender transition-colors"
                    >
                      <h3 className="text-xl font-display text-foreground mb-2">{snapshot.label}</h3>
                      {snapshot.description && (
                        <p className="text-muted-foreground text-sm mb-3">{snapshot.description}</p>
                      )}
                      <div className="text-xs text-muted-foreground">
                        Created: {new Date(snapshot.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex gap-2 mt-3">
                        {snapshots.length >= 2 && snapshot.id !== snapshots[0].id && (
                          <button
                            onClick={() => {
                              setComparisonSnapshot1(snapshots[0].id)
                              setComparisonSnapshot2(snapshot.id)
                              setShowSnapshotComparison(true)
                            }}
                            className="text-xs btn-secondary py-1 px-2"
                          >
                            Compare
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

        {/* Timeline */}
        <div className="mt-12">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-3xl font-display text-foreground">Their Journey</h2>
            <Tooltip content={SITE_HELP.personaDetail.timeline.tooltip} />
          </div>
          <HelpText type="info">
            {SITE_HELP.personaDetail.timeline.whatIs}
          </HelpText>
          {timeline.timeline_events.length === 0 ? (
            <div className="text-center py-20 bg-muted/20 rounded-2xl">
              <Sparkles size={48} className="mx-auto text-muted-foreground mb-4" />
              <h3 className="text-2xl font-display text-foreground mb-2">
                Now Build Their Story
              </h3>
              <p className="text-muted-foreground mb-6">
                You set their starting point. Now add specific life events, one at a time —
                each one gets its own analysis and shifts who they become.
              </p>
              <div className="flex gap-3 justify-center flex-wrap">
                <button
                  onClick={() => setShowAddExperience(true)}
                  className="btn-secondary"
                >
                  Add First Experience
                </button>
                <button
                  onClick={() => setShowAddSupport(true)}
                  className="btn-primary"
                >
                  Add Support
                </button>
              </div>
            </div>
          ) : (
            <TimelineVisualization events={timeline.timeline_events} />
          )}
        </div>
          </>
        )}

        {/* Narrative Tab Content */}
        {activeTab === 'narrative' && (
          <div className="mt-12">
            <PersonaNarrative personaId={params.id} personaName={persona.name} />
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
          onSuccess={() => {
            loadTimeline()
            loadSnapshots()
          }}
        />
      )}

      {/* Snapshot Modals */}
      {showCreateSnapshot && (
        <CreateSnapshotModal
          personaId={params.id}
          onClose={() => setShowCreateSnapshot(false)}
          onSuccess={() => {
            setShowCreateSnapshot(false)
            loadSnapshots()
          }}
        />
      )}

      {showSnapshotComparison && comparisonSnapshot1 && comparisonSnapshot2 && (
        <div className="fixed inset-0 bg-background/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-2xl font-display text-foreground">Snapshot Comparison</h2>
              <button
                onClick={() => {
                  setShowSnapshotComparison(false)
                  setComparisonSnapshot1(null)
                  setComparisonSnapshot2(null)
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <SnapshotComparisonView
                snapshotId1={comparisonSnapshot1}
                snapshotId2={comparisonSnapshot2}
                onClose={() => {
                  setShowSnapshotComparison(false)
                  setComparisonSnapshot1(null)
                  setComparisonSnapshot2(null)
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Chat Box */}
      <ChatBox personaId={params.id} personaName={persona.name} />
    </main>
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

function PersonalityOverview({ persona }: { persona: any }) {
  const traits = [
    { name: 'Openness', key: 'openness', value: persona.current_personality.openness, color: 'bg-periwinkle' },
    { name: 'Conscientiousness', key: 'conscientiousness', value: persona.current_personality.conscientiousness, color: 'bg-deep-purple' },
    { name: 'Extraversion', key: 'extraversion', value: persona.current_personality.extraversion, color: 'bg-soft-purple' },
    { name: 'Agreeableness', key: 'agreeableness', value: persona.current_personality.agreeableness, color: 'bg-lavender' },
    { name: 'Neuroticism', key: 'neuroticism', value: persona.current_personality.neuroticism, color: 'bg-muted-coral' },
  ] as const

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Personality Traits */}
      <div className="bg-white border-2 border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-xl font-display text-foreground">How They Think & Feel</h3>
          <Tooltip content={SITE_HELP.personaDetail.bigFive.tooltip} />
        </div>
        <HelpText type="info">{SITE_HELP.personaDetail.bigFive.whatIs}</HelpText>
        <div className="space-y-4 mt-4">
          {traits.map((trait) => {
            const score = Math.round(trait.value * 100)
            return (
              <div key={trait.name}>
                <div className="flex justify-between text-sm mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-foreground font-medium">{trait.name}</span>
                    <TraitHelp trait={trait.key} score={score} />
                  </div>
                  <span className="text-muted-foreground">{score}%</span>
                </div>
                <div className="bg-muted/30 rounded-full h-3 overflow-hidden">
                  <div
                    className={`${trait.color} h-full rounded-full transition-all duration-700`}
                    style={{ width: `${trait.value * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Trauma Markers */}
      <div className="bg-white border-2 border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-xl font-display text-foreground">What They're Navigating</h3>
          <Tooltip content={SITE_HELP.personaDetail.symptoms.tooltip} />
        </div>
        <HelpText type="info">{SITE_HELP.personaDetail.symptoms.whatIs}</HelpText>
        {persona.current_trauma_markers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <TrendingUp size={32} className="mx-auto mb-2" />
            <p>All is well right now</p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {persona.current_trauma_markers.map((marker: string, i: number) => (
              <span
                key={i}
                className="bg-red-500/20 text-red-500 px-4 py-2 rounded-full text-sm font-medium"
              >
                {marker.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function TimelineVisualization({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="space-y-6">
      {events.map((event, index) => (
        <TimelineEventCard key={index} event={event} index={index} />
      ))}
    </div>
  )
}

function TimelineEventCard({ event, index }: { event: TimelineEvent; index: number }) {
  const isExperience = event.type === 'experience'

  return (
    <div
      className="bg-white border-2 border-border rounded-xl p-6 animate-fade-in"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`p-3 rounded-xl ${isExperience ? 'bg-red-500/20' : 'bg-deep-purple/20'} flex-shrink-0`}>
          {isExperience ? (
            <Sparkles className="text-red-500" size={24} />
          ) : (
            <Pill className="text-deep-purple" size={24} />
          )}
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="flex items-center gap-3">
                <span className="text-xl font-display text-foreground">
                  Age {event.age}
                </span>
                <span className={`text-xs px-2 py-1 rounded-full ${isExperience ? 'bg-red-500/20 text-red-500' : 'bg-deep-purple/20 text-deep-purple'}`}>
                  {isExperience ? 'Experience' : event.therapy_type}
                </span>
              </div>
              <p className="text-muted-foreground text-sm mt-1">
                Event #{event.sequence_number}
              </p>
            </div>
          </div>

          {/* Description */}
          <p className="text-foreground mb-4">
            {event.description || `Therapeutic support: ${event.therapy_type}`}
          </p>

          {/* Personality Snapshot */}
          {event.personality_snapshot && (
            <div className="bg-muted/20 rounded-lg p-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground block mb-1">Neuroticism</span>
                  <span className="text-foreground font-medium">
                    {Math.round(event.personality_snapshot.personality_profile.neuroticism * 100)}%
                  </span>
                </div>
                {(() => {
                  const symptomSev = event.personality_snapshot.symptom_severity || {};
                  // Handle both formats: direct {symptom: severity} or nested {before: {...}, after: {...}}
                  const symptoms = symptomSev.after || symptomSev;
                  const symptomKeys = typeof symptoms === 'object' && symptoms !== null ? Object.keys(symptoms) : [];
                  
                  return symptomKeys.length > 0 && (
                    <div className="col-span-2">
                      <span className="text-muted-foreground block mb-1">Symptoms</span>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(symptoms).map(([symptom, severity]) => {
                          // Ensure severity is a number
                          const severityValue = typeof severity === 'number' ? severity : 0;
                          
                          return (
                            <span key={symptom} className="text-xs bg-red-500/10 text-red-500 px-2 py-1 rounded">
                              {String(symptom).replace(/_/g, ' ')}: {severityValue}/10
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
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

function AddInterventionModal({ personaId, currentAge, onClose, onSuccess }: any) {
  const [loading, setLoading] = useState(false)
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
    try {
      await api.addIntervention(personaId, formData)
      
      // Show success feedback
      alert('✓ Support added successfully! Timeline updating...')
      
      onSuccess()
    } catch (error) {
      console.error('Support error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to add support'
      alert(`Error: ${errorMessage}\n\nCheck the browser console (F12) for details.`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-background/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="text-3xl font-display text-foreground">Add Support or Healing</h2>
          <Tooltip content={SITE_HELP.intervention.pageHelp.content} />
        </div>
        <HelpText type="info">{SITE_HELP.intervention.whatIs}</HelpText>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-foreground">
                Age at Support
              </label>
              <Tooltip content={SITE_HELP.intervention.age.tooltip} />
            </div>
            <input
              type="number"
              required
              min={0}
              max={120}
              value={formData.age_at_intervention}
              onChange={(e) => setFormData({ ...formData, age_at_intervention: parseInt(e.target.value) })}
              className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Add moments of support at any age (0-120) to build complete therapy history
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-foreground">
                Therapy Type
              </label>
              <Tooltip content={SITE_HELP.intervention.modalityPicker.tooltip} />
            </div>
            <select
              value={formData.therapy_type}
              onChange={(e) => setFormData({ ...formData, therapy_type: e.target.value })}
              className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none"
            >
              <option value="CBT">CBT (Cognitive Behavioral Therapy)</option>
              <option value="ACT">ACT (Acceptance & Commitment Therapy)</option>
              <option value="EMDR">EMDR (Eye Movement Desensitization)</option>
              <option value="IFS">IFS (Internal Family Systems)</option>
              <option value="DBT">DBT (Dialectical Behavior Therapy)</option>
              <option value="Psychodynamic">Psychodynamic Therapy</option>
              <option value="Somatic_Experiencing">Somatic Experiencing</option>
              <option value="ERP">ERP (Exposure & Response Prevention)</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-foreground">
                  Duration
                </label>
                <Tooltip content={"How long the support continues"} />
              </div>
              <select
                value={formData.duration}
                onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none"
              >
                <option value="3_months">3 months</option>
                <option value="6_months">6 months</option>
                <option value="1_year">1 year</option>
                <option value="2_years">2 years</option>
              </select>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-foreground">
                  Intensity
                </label>
                <Tooltip content={"How intensive the support is"} />
              </div>
              <select
                value={formData.intensity}
                onChange={(e) => setFormData({ ...formData, intensity: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none"
              >
                <option value="monthly">Monthly</option>
                <option value="weekly">Weekly</option>
                <option value="twice_weekly">Twice Weekly</option>
              </select>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-foreground">
                Notes (Optional)
              </label>
              <Tooltip content={"Additional notes about the support"} />
            </div>
            <textarea
              rows={3}
              value={formData.user_notes}
              onChange={(e) => setFormData({ ...formData, user_notes: e.target.value })}
              className="w-full px-4 py-3 rounded-lg border-2 border-border bg-white focus:border-deep-purple focus:outline-none resize-none"
              placeholder="Additional context about the therapy..."
            />
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? 'Considering how this helps...' : 'Add Support'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
