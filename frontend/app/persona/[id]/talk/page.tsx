'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { api, type Persona, type ChatMessage } from '@/lib/api'
import { RubixShell, RubixCard, RubixBadge } from '@/components/rubix'
import { attachmentStyleLabel, attachmentStyleTone } from '@/lib/rubix/attachmentStyle'

export default function TalkPage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()

  const [persona, setPersona] = useState<Persona | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!authLoading && !user) router.push('/login')
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, user])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

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

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending || !persona) return

    const userMessage: ChatMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setSending(true)
    try {
      const response = await api.chatWithPersona(persona.id, text, messages)
      setMessages((prev) => [...prev, { role: 'assistant', content: response.message }])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err instanceof Error ? `Error: ${err.message}` : 'Sorry, I had trouble responding. Please try again.' }])
    } finally {
      setSending(false)
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

  const contextParts = [
    attachmentStyleLabel(persona.current_attachment_style),
    ...topStateSignals(persona.current_state || {}),
  ]

  return (
    <RubixShell persona={{ id: persona.id, name: persona.name }}>
      <div style={{ maxWidth: 1000, margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
        <RubixCard variant="flat" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0, flexWrap: 'wrap' }}>
          <div className="rubix-avatar" style={{ width: 50, height: 50, flex: '0 0 50px', fontSize: 18 }} aria-hidden="true">
            {persona.name.trim().charAt(0).toUpperCase()}
          </div>
          <div style={{ flex: '1 1 200px', minWidth: 0 }}>
            <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.015em' }}>Speaking with {persona.name}, {persona.current_age}</div>
            <div style={{ marginTop: 4, fontSize: 12.5, color: 'rgba(216,236,255,0.72)' }}>
              {contextParts.join(' · ')} — their answers come from the life you built
            </div>
          </div>
          <RubixBadge tone={attachmentStyleTone(persona.current_attachment_style)}>IN CHARACTER</RubixBadge>
        </RubixCard>

        <div style={{ flex: 1, overflowY: 'auto', marginTop: 16, padding: '6px 4px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', padding: '40px 20px', fontSize: 13.5, color: 'rgba(214,235,255,0.6)' }}>
              Ask {persona.name} something about their life. Their answers reflect their current personality, state, and everything that&apos;s happened to them.
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div
                style={{
                  maxWidth: '76%', padding: '15px 18px', borderRadius: 20, fontSize: 14.5, lineHeight: 1.6, whiteSpace: 'pre-wrap',
                  color: m.role === 'user' ? '#03204d' : 'rgba(232,243,255,0.94)',
                  background: m.role === 'user' ? 'linear-gradient(160deg,#a8dcff,#5b9dff 50%,#3b78f4)' : 'linear-gradient(165deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04))',
                  border: m.role === 'user' ? 'none' : '1px solid rgba(170,210,255,0.2)',
                }}
              >
                {m.content}
              </div>
            </div>
          ))}
          {sending && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ padding: '15px 18px', borderRadius: 20, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(170,210,255,0.2)', fontSize: 14.5, color: 'rgba(214,235,255,0.6)' }}>
                …
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form onSubmit={handleSend} style={{ marginTop: 14, display: 'flex', gap: 10, flexShrink: 0 }}>
          <input
            className="rubix-input"
            style={{ flex: 1, padding: '16px 18px', fontSize: 15 }}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask ${persona.name} something about their life…`}
            disabled={sending}
            aria-label="Message"
          />
          <button type="submit" className="rubix-btn-primary" style={{ padding: '16px 26px', fontSize: 15 }} disabled={sending || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </RubixShell>
  )
}

function topStateSignals(state: Record<string, number>): string[] {
  return Object.entries(state)
    .map(([key, value]) => ({ key, delta: Math.abs(value - 0.5) }))
    .filter((d) => d.delta >= 0.08)
    .sort((a, b) => b.delta - a.delta)
    .slice(0, 2)
    .map((d) => d.key.replace(/_/g, ' '))
}
