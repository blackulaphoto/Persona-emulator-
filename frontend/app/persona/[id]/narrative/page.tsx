'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { api, type Persona } from '@/lib/api'
import { RubixShell, RubixCard } from '@/components/rubix'
import PersonaNarrative from '@/components/PersonaNarrative'

export default function NarrativePage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [persona, setPersona] = useState<Persona | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) router.push('/login')
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, user])

  async function load() {
    setLoading(true)
    setLoadError(false)
    try {
      setPersona(await api.getPersona(params.id))
    } catch (err) {
      console.error('Failed to load persona:', err)
      setLoadError(true)
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 13.5, color: 'rgba(210,232,255,0.65)' }}>Loading…</div>
      </div>
    )
  }
  if (!user) return null

  if (loadError || !persona) {
    return (
      <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <RubixCard style={{ padding: 32, textAlign: 'center', maxWidth: 380 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>Couldn&apos;t load this life</div>
          <button type="button" className="rubix-btn-primary" style={{ marginTop: 18 }} onClick={load}>Retry</button>
        </RubixCard>
      </div>
    )
  }

  return (
    <RubixShell persona={{ id: persona.id, name: persona.name }}>
      <div style={{ maxWidth: 900 }}>
        <PersonaNarrative personaId={persona.id} personaName={persona.name} />
      </div>
    </RubixShell>
  )
}
