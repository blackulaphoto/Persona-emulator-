interface RubixMetricProps {
  label: string;
  /** Display text for the current value, e.g. "62" or "0.62". Caller formats. */
  valueLabel: string;
  /** 0-100 fill width. */
  percent: number;
  /** Accent hex/rgba used for the fill glow and value text. Defaults to the Rubix blue accent. */
  accent?: string;
  /** Optional 0-100 marker position (e.g. baseline, for a baseline-vs-current metric). */
  markerPercent?: number;
}

/** A single labeled meter row — used for Big Five traits and State dimensions alike. */
export function RubixMetric({ label, valueLabel, percent, accent = '#7fb2ff', markerPercent }: RubixMetricProps) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ fontSize: 13.5, fontWeight: 500, color: 'rgba(232,243,255,0.94)', minWidth: 0 }}>{label}</div>
        <div style={{ fontSize: 12, fontWeight: 600, minWidth: 0, color: accent }}>{valueLabel}</div>
      </div>
      <div className="rubix-meter-track" style={{ marginTop: 7 }}>
        <div
          className="rubix-meter-fill"
          style={{ width: `${clamped}%`, background: `linear-gradient(90deg, rgba(255,255,255,0.35), ${accent})`, boxShadow: `0 0 10px ${accent}` }}
        />
        {markerPercent != null && (
          <div className="rubix-meter-marker" style={{ left: `calc(${Math.max(0, Math.min(100, markerPercent))}% - 1.5px)` }} />
        )}
      </div>
    </div>
  );
}
