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
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container-apple py-6">
          <div className="flex items-center gap-4 mb-2 animate-fade-in">
            <Image
              src="/logo.png"
              alt="LifeStream Labs"
              width={48}
              height={48}
              className="object-contain"
            />
            <h1 className="text-4xl font-bold text-foreground" style={{ fontFamily: 'var(--font-display)' }}>
              Persona Evolution
            </h1>
          </div>
          <p className="text-muted-foreground mt-2 animate-fade-in delay-100">
            Explore how life experiences shape who we become
          </p>
        </div>
      </header>

      <div className="container-apple py-12">
        {/* Page Help Banner */}
        <PageHelpBanner pageKey="personasList" />

        {/* Quick Start Guide */}
        {personas.length === 0 && !loading && (
          <div className="mb-8 bg-card border border-border rounded-lg p-6 animate-fade-in-up">
            <h2 className="text-lg font-semibold text-foreground mb-4" style={{ fontFamily: 'var(--font-display)' }}>
              How This Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { num: 1, title: 'Create a Person', desc: 'Start with their early life story' },
                { num: 2, title: 'Add Experiences', desc: 'Build their journey moment by moment' },
                { num: 3, title: 'Explore Their Timeline', desc: 'See how they evolved over time' },
                { num: 4, title: 'Understand the Pattern', desc: 'Watch how it all connects' }
              ].map(({ num, title, desc }) => (
                <div key={num} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm" style={{ background: 'var(--lavender)', color: 'var(--deep-purple)' }}>
                    {num}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{title}</p>
                    <p className="text-xs text-muted-foreground mt-1">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Create New Persona & Templates */}
        <div className="mb-12 animate-fade-in delay-200 flex gap-4 flex-wrap items-center">
          <div className="relative inline-flex items-center">
            <Button
              onClick={() => router.push('/create')}
              variant="primary"
              icon={<Plus size={20} />}
            >
              Start a New Person
            </Button>
            <div className="ml-2">
              <Tooltip content={"Start creating a new person to explore"} />
            </div>
          </div>
          {templates.length > 0 && (
            <div className="relative inline-flex items-center">
              <Button
                onClick={() => router.push('/templates')}
                variant="secondary"
                icon={<FileText size={20} />}
              >
                Explore Story Templates
              </Button>
              <div className="ml-2">
                <Tooltip content={"Use a pre-built story template"} />
              </div>
            </div>
          )}
        </div>


        {/* Personas Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 mx-auto mb-4 border-b-2" style={{ borderColor: 'var(--deep-purple)' }}></div>
            <p className="text-muted-foreground">Finding their stories...</p>
          </div>
        ) : personas.length === 0 ? (
          <div className="text-center py-20 animate-fade-in delay-300">
            <EmptyStateWithHelp
              icon="👤"
              title={SITE_HELP.personasList.emptyState.title}
              description={SITE_HELP.personasList.emptyState.subtitle}
              helpItems={SITE_HELP.personasList.emptyState.steps.map(s => s.description)}
              actionButton={{
                text: "Start Your First Story",
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
        <h3 className="text-2xl text-foreground mb-1 font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
          {persona.name}
        </h3>
        <p className="text-muted-foreground text-sm flex items-center gap-1">
          <Clock size={14} />
          Age {persona.current_age}
        </p>
      </div>

      {/* Stats */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">Life Moments</span>
            <Tooltip content={SITE_HELP.personasList.personaCard.experiences} />
          </div>
          <Badge color="purple">{persona.experiences_count}</Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">Current Age</span>
            <Tooltip content={SITE_HELP.personasList.personaCard.age} />
          </div>
          <Badge color="gray">{persona.current_age} years</Badge>
        </div>
      </div>

      {/* Personality Preview */}
      <div className="border-t border-border pt-4">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-muted-foreground">How They Feel</span>
          <span className="text-foreground font-medium">
            {Math.round((1 - neuroticism) * 100)}%
          </span>
        </div>
        <div className="bg-muted rounded-full h-2 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${(1 - neuroticism) * 100}%`,
              background: 'linear-gradient(to right, var(--lavender), var(--deep-purple))'
            }}
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
      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex items-center gap-2 text-sm font-medium transition-colors" style={{ color: 'var(--deep-purple)' }}>
          <TrendingUp size={16} />
          See Their Journey
        </div>
      </div>
    </Card>
  )
}
