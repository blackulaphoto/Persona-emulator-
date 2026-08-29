'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, type Persona } from '@/lib/api'
import { templatesAPI, type Template } from '@/lib/api/templates'
import { useAuth } from '@/contexts/AuthContext'
import { RubixShell, RubixPageHeader, RubixCard, RubixBadge, RubixEmptyState } from '@/components/rubix'
import { attachmentStyleLabel, attachmentStyleTone } from '@/lib/rubix/attachmentStyle'

export default function LivesPage() {
  const { user, loading: authLoading } = useAuth()
  const [personas, setPersonas] = useState<Persona[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [templates, setTemplates] = useState<Template[]>([])
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
    setLoading(true)
    setLoadError(false)
    try {
      const data = await api.getPersonas()
      setPersonas(data)
    } catch (error) {
      console.error('Failed to load personas:', error)
      setLoadError(true)
    } finally {
      setLoading(false)
    }
  }

  async function loadTemplates() {
    try {
      const data = await templatesAPI.list()
      setTemplates(data)
    } catch (error) {
      // Feature may be disabled - fail silently, "Story templates" link just won't show.
      setTemplates([])
    }
  }

  if (authLoading || !user) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 13.5, color: 'rgba(210,232,255,0.65)' }}>Loading…</div>
      </div>
    )
  }

  return (
    <RubixShell>
      <RubixPageHeader
        actions={
          templates.length > 0 ? (
            <Link href="/templates" className="rubix-btn-ghost">
              Story templates
            </Link>
          ) : undefined
        }
      />

      <div style={{ maxWidth: 1420 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.025em' }}>Lives</div>
            <div style={{ marginTop: 7, fontSize: 14, color: 'rgba(214,235,255,0.7)' }}>
              Every person you&apos;ve built, and what their life produced.
            </div>
          </div>
          <Link href="/create" className="rubix-btn-primary">
            <span aria-hidden="true">+</span>
            <span>New life</span>
          </Link>
        </div>

        <div style={{ marginTop: 24 }}>
          {loading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(292px, 1fr))', gap: 18 }}>
              {[0, 1, 2].map((i) => (
                <div key={i} className="rubix-card" style={{ padding: 22, height: 168, opacity: 0.5 }} aria-hidden="true" />
              ))}
            </div>
          ) : loadError ? (
            <RubixCard>
              <RubixEmptyState
                title="Couldn't load your lives"
                description="Something went wrong reaching Rubix. Check your connection and try again."
                action={
                  <button type="button" className="rubix-btn-primary" onClick={loadPersonas}>
                    Retry
                  </button>
                }
              />
            </RubixCard>
          ) : personas.length === 0 ? (
            <RubixCard>
              <RubixEmptyState
                title="No lives yet"
                description="Start with a name, an age, and what home was like. Rubix builds a real developmental history from there."
                action={
                  <Link href="/create" className="rubix-btn-primary">
                    Start your first life
                  </Link>
                }
              />
            </RubixCard>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(292px, 1fr))', gap: 18 }}>
              {personas.map((persona) => (
                <LifeCard key={persona.id} persona={persona} />
              ))}
            </div>
          )}
        </div>
      </div>
    </RubixShell>
  )
}

function LifeCard({ persona }: { persona: Persona }) {
  const built = formatBuiltDate(persona.created_at)
  const meta = `Age ${persona.current_age} · ${persona.experiences_count} experience${persona.experiences_count === 1 ? '' : 's'}`

  return (
    <Link href={`/persona/${persona.id}`} className="rubix-card rubix-card-interactive" style={{ display: 'block', padding: 22, textDecoration: 'none', color: 'inherit' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div className="rubix-avatar" style={{ width: 52, height: 52, flex: '0 0 52px', fontSize: 17 }} aria-hidden="true">
          {persona.name.trim().charAt(0).toUpperCase()}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.015em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {persona.name}
          </div>
          <div style={{ marginTop: 4, fontSize: 12.5, color: 'rgba(216,236,255,0.7)' }}>{meta}</div>
        </div>
      </div>

      {persona.baseline_background && (
        <div
          style={{
            marginTop: 16,
            fontSize: 13.5,
            lineHeight: 1.6,
            color: 'rgba(224,239,255,0.8)',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {persona.baseline_background}
        </div>
      )}

      <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <RubixBadge tone={attachmentStyleTone(persona.current_attachment_style)}>
          {attachmentStyleLabel(persona.current_attachment_style)}
        </RubixBadge>
        {built && <div style={{ fontSize: 12, color: 'rgba(205,230,255,0.6)' }}>{built}</div>}
      </div>
    </Link>
  )
}

function formatBuiltDate(createdAt: string): string {
  try {
    const date = new Date(createdAt)
    if (Number.isNaN(date.getTime())) return ''
    return `Built ${date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`
  } catch {
    return ''
  }
}
