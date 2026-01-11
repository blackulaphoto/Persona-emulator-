'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { Plus, User, Clock, TrendingUp, FileText, Wand2 } from 'lucide-react'
import { api, type Persona } from '@/lib/api'
import { templatesAPI, type Template } from '@/lib/api/templates'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHelpBanner, EmptyStateWithHelp } from '@/components/help/PageHelpComponents'
import { Tooltip } from '@/components/help/HelpComponents'
import { SITE_HELP } from '@/lib/help/SiteWideHelpContent'

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
      <div className="min-h-screen bg-apple-bg-tertiary flex items-center justify-center">
        <div className="text-center">
          <div className="spinner-apple w-16 h-16 mx-auto mb-4 border-apple-blue-500"></div>
          <p className="text-apple-text-secondary">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <main className="min-h-screen bg-apple-bg-tertiary gradient-apple-mesh">
      {/* Glass Header */}
      <header className="glass-panel">
        <div className="container-apple py-6">
          <div className="flex items-center gap-4 mb-2 animate-fade-in-apple">
            <Image
              src="/logo.png"
              alt="LifeStream Labs"
              width={48}
              height={48}
              className="object-contain"
            />
            <h1 className="text-4xl font-serif text-apple-text-primary font-bold">
              Persona Evolution
            </h1>
          </div>
          <p className="text-apple-text-secondary mt-2 animate-fade-in-apple delay-apple-100">
            Explore psychological transformation through life experiences and therapy
          </p>
        </div>
      </header>

      <div className="container-apple py-12">
        {/* Page Help Banner */}
        <PageHelpBanner pageKey="personasList" />

        {/* Quick Start Guide */}
        {personas.length === 0 && !loading && (
          <Card variant="glass" className="mb-8 animate-scale-in">
            <h2 className="text-lg font-semibold text-apple-text-primary mb-4">How to Use</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { num: 1, title: 'Create a Persona', desc: 'Set early life context' },
                { num: 2, title: 'Add Experiences', desc: 'Shape personality over time' },
                { num: 3, title: 'Explore Timeline', desc: 'Snapshots & narrative' },
                { num: 4, title: 'Chat', desc: 'Talk to the persona as they\'ve become' }
              ].map(({ num, title, desc }) => (
                <div key={num} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-apple-blue-100 flex items-center justify-center text-apple-blue-600 font-bold text-sm">
                    {num}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-apple-text-primary">{title}</p>
                    <p className="text-xs text-apple-text-secondary mt-1">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Create New Persona & Templates */}
        <div className="mb-12 animate-fade-in-apple delay-apple-200 flex gap-4 flex-wrap items-center">
          <div className="relative inline-flex items-center">
            <Button
              onClick={() => router.push('/create')}
              variant="primary"
              icon={<Plus size={20} />}
              className="shadow-apple-lg"
            >
              Create New Persona
            </Button>
            <div className="ml-2">
              <Tooltip content={SITE_HELP.personasList.createPersona.tooltip} />
            </div>
          </div>
          {templates.length > 0 && (
            <div className="relative inline-flex items-center">
              <Button
                onClick={() => router.push('/templates')}
                variant="secondary"
                icon={<FileText size={20} />}
              >
                Browse Clinical Templates
              </Button>
              <div className="ml-2">
                <Tooltip content={SITE_HELP.personasList.useTemplate.tooltip} />
              </div>
            </div>
          )}
        </div>


        {/* Personas Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="spinner-apple w-12 h-12 mx-auto mb-4 border-apple-blue-500"></div>
            <p className="text-apple-text-secondary">Loading personas...</p>
          </div>
        ) : personas.length === 0 ? (
          <div className="text-center py-20 animate-fade-in-apple delay-apple-300">
            <EmptyStateWithHelp
              icon="👤"
              title={SITE_HELP.personasList.emptyState.title}
              description={SITE_HELP.personasList.emptyState.description}
              helpItems={SITE_HELP.personasList.emptyState.helpItems}
              actionButton={{
                text: "Create Your First Persona",
                onClick: () => router.push('/create'),
                helpKey: "personasList.createPersona"
              }}
            />
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
    <Card
      hover
      onClick={onClick}
      className="cursor-pointer animate-fade-in-up"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Name & Age */}
      <div className="mb-4">
        <h3 className="text-2xl font-serif text-apple-text-primary mb-1 font-semibold">
          {persona.name}
        </h3>
        <p className="text-apple-text-secondary text-sm flex items-center gap-1">
          <Clock size={14} />
          Age {persona.current_age}
        </p>
      </div>

      {/* Stats */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <span className="text-apple-text-secondary">Experiences</span>
            <Tooltip content={SITE_HELP.personasList.personaCard.experiences} />
          </div>
          <Badge color="blue">{persona.experiences_count}</Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <span className="text-apple-text-secondary">Age</span>
            <Tooltip content={SITE_HELP.personasList.personaCard.age} />
          </div>
          <Badge color="gray">{persona.current_age} years</Badge>
        </div>
      </div>

      {/* Personality Preview */}
      <div className="border-t border-apple-border-light pt-4">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-apple-text-secondary">Emotional Stability</span>
          <span className="text-apple-text-primary font-medium">
            {Math.round((1 - neuroticism) * 100)}%
          </span>
        </div>
        <div className="bg-apple-bg-tertiary rounded-full h-2 overflow-hidden">
          <div
            className="bg-apple-blue-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${(1 - neuroticism) * 100}%` }}
          />
        </div>
      </div>

      {/* Trauma Markers */}
      {traumaLevel > 0 && (
        <div className="mt-4 flex flex-wrap gap-1">
          {persona.current_trauma_markers.slice(0, 3).map((marker, i) => (
            <Badge key={i} color="red">
              {marker}
            </Badge>
          ))}
          {traumaLevel > 3 && (
            <Badge color="red">
              +{traumaLevel - 3} more
            </Badge>
          )}
        </div>
      )}

      {/* View Timeline Button */}
      <div className="mt-4 pt-4 border-t border-apple-border-light">
        <div className="flex items-center gap-2 text-apple-blue-500 text-sm font-medium hover:text-apple-blue-600 transition-colors">
          <TrendingUp size={16} />
          View Evolution Timeline
        </div>
      </div>
    </Card>
  )
}
