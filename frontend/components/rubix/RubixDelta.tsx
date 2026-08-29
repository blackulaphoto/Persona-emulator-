interface RubixDeltaProps {
  /** Already-formatted signed value, e.g. "+0.12" or "-6". */
  label: string;
  /**
   * Whether this direction of change reads as good/bad/neutral for this
   * specific metric - callers decide (e.g. Neuroticism decreasing is
   * "positive", Openness decreasing usually isn't "negative" at all).
   * This component only renders the pill; it doesn't guess semantics.
   */
  tone: 'positive' | 'negative' | 'neutral';
}

const toneColor: Record<RubixDeltaProps['tone'], { color: string; bg: string }> = {
  positive: { color: '#a8f2cf', bg: 'rgba(80,220,160,0.18)' },
  negative: { color: '#ffc9a6', bg: 'rgba(255,170,120,0.18)' },
  neutral: { color: 'rgba(214,235,255,0.75)', bg: 'rgba(255,255,255,0.08)' },
};

/** Small delta pill for personality_delta / attachment_delta values. */
export function RubixDelta({ label, tone }: RubixDeltaProps) {
  const s = toneColor[tone];
  return (
    <span className="rubix-delta" style={{ color: s.color, background: s.bg }}>
      {label}
    </span>
  );
}
