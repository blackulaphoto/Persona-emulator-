import Link from 'next/link';
import { ReactNode } from 'react';

interface RubixPageHeaderProps {
  /** Current screen name. Omit to just show "Lives" (e.g. on the Lives page itself). */
  title?: string;
  actions?: ReactNode;
}

/** The "Lives / {screen}" orientation bar at the top of every Rubix page. */
export function RubixPageHeader({ title, actions }: RubixPageHeaderProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, marginBottom: 22 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <Link href="/personas" style={{ fontSize: 13, color: 'rgba(205,228,255,0.62)' }}>
          Lives
        </Link>
        {title && (
          <>
            <span style={{ fontSize: 13, color: 'rgba(205,228,255,0.35)' }}>/</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#eaf3ff' }}>{title}</span>
          </>
        )}
      </div>
      {actions && <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>{actions}</div>}
    </div>
  );
}
