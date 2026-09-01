'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import { RubixShell, RubixPageHeader, RubixCard } from '@/components/rubix'
import FeedbackModal from '@/components/FeedbackModal'

const TOTAL_STEPS = 5
const BACKGROUND_LIMIT = 1000

const ATTACHMENT_CHOICES: { key: string; label: string }[] = [
  { key: 'secure', label: 'Secure' },
  { key: 'anxious', label: 'Anxious' },
  { key: 'avoidant', label: 'Avoidant' },
  { key: 'fearful-avoidant', label: 'Fearful-avoidant' },
  { key: 'disorganized', label: 'Disorganized' },
]

export default function CreateStartingPersonPage() {
  const router = useRouter()
  useAuth() // route guard is enforced by RubixShell's own pages; kept for parity, no redirect needed here

  const [step, setStep] = useState(1)
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState('')
  const [home, setHome] = useState('')
  const [caregivers, setCaregivers] = useState('')
  const [temperament, setTemperament] = useState('')
  const [attachment, setAttachment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)

  const ageNum = parseInt(age, 10)
  const step1Valid = name.trim().length > 0 && gender.trim().length > 0 && !isNaN(ageNum) && ageNum >= 0 && ageNum <= 120

  const background = useMemo(
    () =>
      [home, caregivers, temperament]
        .map((t) => t.trim())
        .filter(Boolean)
        .join('\n\n'),
    [home, caregivers, temperament]
  )
  const step5Valid = background.length > 0 && background.length <= BACKGROUND_LIMIT

  const isFinalStep = step === TOTAL_STEPS
  const currentStepValid = step === 1 ? step1Valid : step === TOTAL_STEPS ? step5Valid : true

  function goBack() {
    if (step <= 1) {
      router.push('/personas')
      return
    }
    setStep((s) => s - 1)
  }

  async function goNext() {
    if (!currentStepValid) return
    if (!isFinalStep) {
      setStep((s) => s + 1)
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      const persona = await api.createPersona({
        name: name.trim(),
        baseline_age: ageNum,
        baseline_gender: gender.trim(),
        baseline_background: background,
        ...(attachment ? { baseline_attachment_style: attachment } : {}),
      })
      // Continue directly into the life-building workflow.
      router.push(`/persona/${persona.id}/build`)
    } catch (err: any) {
      console.error('Failed to create persona:', err)
      if (err?.message?.includes('403')) {
        setShowFeedbackModal(true)
      } else {
        setError('Something went wrong creating this person. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <RubixShell>
      <RubixPageHeader title="Create the starting person" />

      <div style={{ maxWidth: 640, margin: '4vh auto 0' }}>
        <RubixCard variant="hero" style={{ padding: '30px 32px 26px' }}>
          <div style={{ display: 'flex', gap: 7 }} role="progressbar" aria-valuenow={step} aria-valuemin={1} aria-valuemax={TOTAL_STEPS} aria-label="Create starting person progress">
            {Array.from({ length: TOTAL_STEPS }, (_, i) => i + 1).map((n) => (
              <div key={n} className="rubix-meter-track" style={{ flex: 1, height: 6 }}>
                <div
                  className="rubix-meter-fill"
                  style={{
                    width: n <= step ? '100%' : '0%',
                    background: 'linear-gradient(90deg, rgba(120,220,255,0.85), rgba(90,150,255,0.95))',
                    boxShadow: n <= step ? '0 0 10px rgba(110,190,255,0.55)' : 'none',
                  }}
                />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, fontSize: 11.5, fontWeight: 600, letterSpacing: '0.12em', color: 'rgba(200,226,255,0.62)' }}>
            STEP {step} OF {TOTAL_STEPS}
          </div>

          {step === 1 && (
            <div>
              <StepTitle>Who are they, to start?</StepTitle>
              <StepSubtitle>The name and the age Rubicks begins tracking their life from.</StepSubtitle>
              <div style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label className="rubix-field-label" htmlFor="create-name">NAME</label>
                  <input
                    id="create-name"
                    className="rubix-input"
                    style={{ marginTop: 9, width: '100%' }}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Maren"
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div>
                    <label className="rubix-field-label" htmlFor="create-age">STARTING AGE</label>
                    <input
                      id="create-age"
                      type="number"
                      min={0}
                      max={120}
                      className="rubix-input"
                      style={{ marginTop: 9, width: '100%' }}
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      placeholder="e.g. 6"
                    />
                  </div>
                  <div>
                    <label className="rubix-field-label" htmlFor="create-gender">GENDER</label>
                    <input
                      id="create-gender"
                      className="rubix-input"
                      style={{ marginTop: 9, width: '100%' }}
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      placeholder="e.g. female"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <StepTitle>What was home like?</StepTitle>
              <StepSubtitle>Free text. Stable, chaotic, affectionate, strict, absent — whatever&apos;s true.</StepSubtitle>
              <textarea
                className="rubix-textarea"
                style={{ marginTop: 18, width: '100%', minHeight: 150 }}
                value={home}
                onChange={(e) => setHome(e.target.value)}
                placeholder="Describe the home this person grew up in…"
                aria-label="Home environment"
              />
            </div>
          )}

          {step === 3 && (
            <div>
              <StepTitle>Who raised them?</StepTitle>
              <StepSubtitle>Parents, a single caregiver, extended family — however it was, and what they were like.</StepSubtitle>
              <textarea
                className="rubix-textarea"
                style={{ marginTop: 18, width: '100%', minHeight: 150 }}
                value={caregivers}
                onChange={(e) => setCaregivers(e.target.value)}
                placeholder="e.g. Raised mostly by her mother. Warm but overwhelmed; father present but distant."
                aria-label="Caregivers"
              />
            </div>
          )}

          {step === 4 && (
            <div>
              <StepTitle>What were they like, even then?</StepTitle>
              <StepSubtitle>Temperament before life started acting on it — curious, cautious, loud, watchful, easygoing.</StepSubtitle>
              <textarea
                className="rubix-textarea"
                style={{ marginTop: 18, width: '100%', minHeight: 150 }}
                value={temperament}
                onChange={(e) => setTemperament(e.target.value)}
                placeholder="e.g. Watchful even as a small child. Quick to laugh, slower to trust."
                aria-label="Temperament"
              />
              <div style={{ marginTop: 12, fontSize: 12, color: background.length > BACKGROUND_LIMIT ? '#ffb3a6' : 'rgba(205,230,255,0.55)' }}>
                {background.length} / {BACKGROUND_LIMIT} characters across these three answers
              </div>
            </div>
          )}

          {step === 5 && (
            <div>
              <StepTitle>Where does trust start?</StepTitle>
              <StepSubtitle>Optional. Leave this unset and Rubicks starts them secure, then lets their life shape it from here.</StepSubtitle>
              <div style={{ marginTop: 18, display: 'flex', gap: 8, flexWrap: 'wrap' }} role="group" aria-label="Starting attachment style">
                {ATTACHMENT_CHOICES.map((c) => (
                  <button
                    key={c.key}
                    type="button"
                    className="rubix-chip"
                    data-active={attachment === c.key ? 'true' : 'false'}
                    aria-pressed={attachment === c.key}
                    onClick={() => setAttachment((cur) => (cur === c.key ? '' : c.key))}
                  >
                    {c.label}
                  </button>
                ))}
              </div>

              <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid rgba(170,210,255,0.18)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.1em', color: 'rgba(200,226,255,0.6)' }}>STARTING POINT</div>
                <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <ReviewRow label="Name" value={name.trim() || '—'} />
                  <ReviewRow label="Starting age" value={age || '—'} />
                  <ReviewRow label="Gender" value={gender.trim() || '—'} />
                </div>
                <div style={{ marginTop: 14, fontSize: 12.5, lineHeight: 1.6, color: 'rgba(205,230,255,0.6)' }}>
                  Personality isn&apos;t set by hand — Rubicks reads what you&apos;ve shared and infers a starting Big Five baseline from it.
                </div>
              </div>
            </div>
          )}

          {error && (
            <div style={{ marginTop: 18, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
              {error}
            </div>
          )}

          <div style={{ marginTop: 28, paddingTop: 22, borderTop: '1px solid rgba(170,210,255,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}>
            <button type="button" className="rubix-btn-ghost" onClick={goBack} disabled={submitting}>
              ← {step === 1 ? 'Cancel' : 'Back'}
            </button>
            <button
              type="button"
              className="rubix-btn-primary"
              onClick={goNext}
              disabled={!currentStepValid || submitting}
              aria-disabled={!currentStepValid || submitting}
            >
              {submitting ? 'Creating…' : isFinalStep ? 'Begin building their life →' : 'Continue →'}
            </button>
          </div>
        </RubixCard>
      </div>

      <FeedbackModal isOpen={showFeedbackModal} onClose={() => setShowFeedbackModal(false)} />
    </RubixShell>
  )
}

function StepTitle({ children }: { children: React.ReactNode }) {
  return <div style={{ marginTop: 12, fontSize: 25, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.3 }}>{children}</div>
}

function StepSubtitle({ children }: { children: React.ReactNode }) {
  return <div style={{ marginTop: 10, fontSize: 14, lineHeight: 1.6, color: 'rgba(224,239,255,0.8)' }}>{children}</div>
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 13.5 }}>
      <div style={{ color: 'rgba(210,232,255,0.65)' }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  )
}
