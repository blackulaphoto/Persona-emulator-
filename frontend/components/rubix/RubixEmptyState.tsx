import { ReactNode } from 'react';

interface RubixEmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

/** Professional empty state in the Rubix visual language - floating diamond, title, optional action. No invented data to fill the gap. */
export function RubixEmptyState({ title, description, action }: RubixEmptyStateProps) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
      <div style={{ width: 44, height: 44, margin: '0 auto 18px' }}>
        <div className="rubix-diamond" style={{ width: 44, height: 44 }} />
      </div>
      <div style={{ fontSize: 15.5, fontWeight: 600, color: 'var(--rubix-text)' }}>{title}</div>
      {description && (
        <div style={{ marginTop: 8, fontSize: 13.5, lineHeight: 1.6, color: 'var(--rubix-text-dim)', maxWidth: 420, marginLeft: 'auto', marginRight: 'auto' }}>
          {description}
        </div>
      )}
      {action && <div style={{ marginTop: 18 }}>{action}</div>}
    </div>
  );
}
