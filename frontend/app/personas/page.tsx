'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, User, Clock, TrendingUp, FileText, Wand2 } from 'lucide-react'
import { api, type Persona } from '@/lib/api'
import { templatesAPI, type Template } from '@/lib/api/templates'
import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const { user, loading: authLoading } = useAuth()
  const [personas, setPersonas] = useState<Persona[]>([])
  const [loading, setLoading] = useState(true)
  const [templates, setTemplates] = useState<Template[]>([])
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) {
      loadPersonas()
      loadTemplates()
    }
  }, [user])

  async function loadPersonas() {
    try {
      const data = await api.getPersonas()
      setPersonas(data)
    } catch (error) {
      console.error('Failed to load personas:', error)
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
      console.log('Templates not available (feature may be disabled):', error)
      setTemplates([])
    } finally {
      setLoadingTemplates(false)
    }
  }

  async function handleCreateFromTemplate(templateId: string) {
    try {
      const result = await templatesAPI.createPersona(templateId)
      router.push(`/persona/${result.persona_id}`)
    } catch (error) {
      console.error('Failed to create persona from template:', error)
      alert('Failed to create persona from template. Please try again.')
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-moss border-t-transparent mx-auto mb-4"></div>
          <p className="text-sage font-['Outfit']">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <main className="min-h-screen bg-grain">
      {/* Header */}
      <header className="border-b border-charcoal/10 bg-cream/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <h1 className="text-4xl font-serif text-charcoal animate-fade-in">
            Persona Evolution
          </h1>
          <p className="text-sage mt-2 animate-fade-in delay-100">
            Explore psychological transformation through life experiences and therapy
          </p>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Quick Start Guide */}
        {personas.length === 0 && !loading && (
          <div className="mb-8 animate-fade-in delay-150 bg-moss/10 rounded-xl p-6 border border-moss/20">
            <h2 className="text-lg font-semibold text-charcoal mb-4 font-['Outfit']">How to Use</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-moss/20 flex items-center justify-center text-moss font-bold">1</div>
                <div>
                  <p className="text-sm font-medium text-charcoal">Create a Persona</p>
                  <p className="text-xs text-sage mt-1">Set early life context</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-moss/20 flex items-center justify-center text-moss font-bold">2</div>
                <div>
                  <p className="text-sm font-medium text-charcoal">Add Experiences</p>
                  <p className="text-xs text-sage mt-1">Shape personality over time</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-moss/20 flex items-center justify-center text-moss font-bold">3</div>
                <div>
                  <p className="text-sm font-medium text-charcoal">Explore Timeline</p>
                  <p className="text-xs text-sage mt-1">Snapshots & narrative</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-moss/20 flex items-center justify-center text-moss font-bold">4</div>
                <div>
                  <p className="text-sm font-medium text-charcoal">Chat</p>
                  <p className="text-xs text-sage mt-1">Talk to the persona as they've become</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Create New Persona & Templates */}
        <div className="mb-12 animate-fade-in delay-200 flex gap-4 flex-wrap">
          <button
            onClick={() => router.push('/create')}
            className="btn-primary flex items-center gap-2 shadow-lg hover:shadow-xl"
          >
            <Plus size={20} />
            Create New Persona
          </button>
          {templates.length > 0 && (
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="btn-secondary flex items-center gap-2 shadow-lg hover:shadow-xl"
            >
              <FileText size={20} />
              {showTemplates ? 'Hide' : 'Browse'} Clinical Templates
            </button>
          )}
        </div>

        {/* Templates Section */}
        {showTemplates && (
          <div className="mb-12 animate-fade-in delay-300 bg-clay/20 rounded-2xl p-8 border-2 border-moss/30">
            <div className="flex items-center gap-3 mb-6">
              <Wand2 className="text-moss" size={32} />
              <div>
                <h2 className="text-2xl font-serif text-charcoal">Clinical Templates</h2>
                <p className="text-sage text-sm mt-1">
                  Create personas from evidence-based disorder development pathways
                </p>
              </div>
            </div>
            {loadingTemplates ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-moss border-t-transparent"></div>
                <p className="mt-4 text-sage">Loading templates...</p>
              </div>
            ) : templates.length === 0 ? (
              <div className="text-center py-12 text-sage">
                <p>Templates feature is disabled or no templates available.</p>
                <p className="text-xs mt-2">Enable FEATURE_CLINICAL_TEMPLATES=true in backend/.env</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="bg-cream border-2 border-charcoal/10 rounded-xl p-6 hover:border-moss/30 transition-colors cursor-pointer card-hover"
                    onClick={() => handleCreateFromTemplate(template.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-serif text-charcoal flex-1">{template.name}</h3>
                      <span className="text-xs px-2 py-1 bg-terracotta/20 text-terracotta rounded-full ml-2">
                        {template.disorder_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-sage text-sm mb-4 line-clamp-2">{template.description}</p>
                    <div className="flex gap-4 text-xs text-sage mb-4">
                      <span>{template.experience_count} experiences</span>
                      <span>{template.intervention_count} interventions</span>
                    </div>
                    <button className="btn-primary w-full text-sm">
                      Create Persona
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Personas Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-moss border-t-transparent"></div>
            <p className="mt-4 text-sage">Loading personas...</p>
          </div>
        ) : personas.length === 0 ? (
          <div className="text-center py-20 animate-fade-in delay-300">
            <div className="bg-clay/30 rounded-2xl p-12 max-w-md mx-auto">
              <User size={48} className="mx-auto text-sage mb-4" />
              <h2 className="text-2xl font-serif text-charcoal mb-2">
                No Personas Yet
              </h2>
              <p className="text-sage mb-6">
                Create your first persona to begin exploring psychological evolution
              </p>
              <button
                onClick={() => router.push('/create')}
                className="btn-primary"
              >
                Get Started
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {personas.map((persona, index) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                index={index}
                onClick={() => router.push(`/persona/${persona.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}

function PersonaCard({ persona, index, onClick }: {
  persona: Persona
  index: number
  onClick: () => void
}) {
  const traumaLevel = persona.current_trauma_markers.length
  const neuroticism = persona.current_personality.neuroticism

  return (
    <div
      onClick={onClick}
      className={`bg-cream border-2 border-charcoal/10 rounded-xl p-6 cursor-pointer card-hover animate-fade-in delay-${Math.min(index, 5) * 100}`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Name & Age */}
      <div className="mb-4">
        <h3 className="text-2xl font-serif text-charcoal mb-1">
          {persona.name}
        </h3>
        <p className="text-sage text-sm flex items-center gap-1">
          <Clock size={14} />
          Age {persona.current_age}
        </p>
      </div>

      {/* Stats */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-sage">Experiences</span>
          <span className="font-medium text-charcoal">
            {persona.experiences_count}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-sage">Interventions</span>
          <span className="font-medium text-charcoal">
            {persona.interventions_count}
          </span>
        </div>
      </div>

      {/* Personality Preview */}
      <div className="border-t border-charcoal/10 pt-4">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-sage">Emotional Stability</span>
          <span className="text-charcoal font-medium">
            {Math.round((1 - neuroticism) * 100)}%
          </span>
        </div>
        <div className="bg-clay/30 rounded-full h-2 overflow-hidden">
          <div
            className="bg-moss h-full rounded-full transition-all duration-500"
            style={{ width: `${(1 - neuroticism) * 100}%` }}
          />
        </div>
      </div>

      {/* Trauma Markers */}
      {traumaLevel > 0 && (
        <div className="mt-4 flex flex-wrap gap-1">
          {persona.current_trauma_markers.slice(0, 3).map((marker, i) => (
            <span
              key={i}
              className="text-xs bg-terracotta/20 text-terracotta px-2 py-1 rounded-full"
            >
              {marker}
            </span>
          ))}
          {traumaLevel > 3 && (
            <span className="text-xs bg-terracotta/20 text-terracotta px-2 py-1 rounded-full">
              +{traumaLevel - 3} more
            </span>
          )}
        </div>
      )}

      {/* View Timeline Button */}
      <div className="mt-4 pt-4 border-t border-charcoal/10">
        <div className="flex items-center gap-2 text-moss text-sm font-medium">
          <TrendingUp size={16} />
          View Evolution Timeline
        </div>
      </div>
    </div>
  )
}
