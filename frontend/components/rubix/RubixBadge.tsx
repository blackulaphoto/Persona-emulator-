import { ReactNode } from 'react';

export type RubixBadgeTone = 'positive' | 'neutral' | 'caution' | 'muted' | 'violet';

interface RubixBadgeProps {
  tone?: RubixBadgeTone;
  children: ReactNode;
}

const toneStyle: Record<RubixBadgeTone, { color: string; bg: string; border: string }> = {
  positive: { color: '#04281c', bg: 'linear-gradient(160deg,#9df0c8,#4fd39c)', border: 'rgba(110,230,180,0.32)' },
  neutral: { color: '#04203f', bg: 'linear-gradient(160deg,#7fe3ff,#2f9dff)', border: 'rgba(120,200,255,0.35)' },
  caution: { color: '#3a2400', bg: 'linear-gradient(160deg,#ffe0ab,#f0b64f)', border: 'rgba(240,185,80,0.4)' },
  violet: { color: '#1c0f3d', bg: 'linear-gradient(150deg,#d3bcff,#8f6bff)', border: 'rgba(180,155,255,0.4)' },
  muted: { color: 'rgba(226,240,255,0.85)', bg: 'rgba(255,255,255,0.08)', border: 'rgba(175,212,255,0.2)' },
};

/**
 * A small status pill — pattern status (emerging/established/weakening/
 * resolved), hypothesis direction (strengthening/weakening/stable), event
 * kind. Callers map their own domain vocabulary to a tone; this component
 * doesn't hardcode any product-specific status strings.
 */
export function RubixBadge({ tone = 'muted', children }: RubixBadgeProps) {
  const s = toneStyle[tone];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '3px 10px',
        borderRadius: 999,
        fontSize: 10.5,
        fontWeight: 700,
        letterSpacing: '0.06em',
        color: s.color,
        background: s.bg,
        border: `1px solid ${s.border}`,
      }}
    >
      {children}
    </span>
  );
}
