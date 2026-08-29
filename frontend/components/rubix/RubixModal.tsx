'use client';

import { ReactNode, useEffect, useRef } from 'react';
import { useFocusTrap } from '@/lib/rubix/useFocusTrap';

interface RubixModalProps {
  open: boolean;
  onClose: () => void;
  eyebrow?: string;
  eyebrowColor?: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
  width?: number;
}

/** The single reusable centered modal shell - Add Therapy/Support uses this. */
export function RubixModal({ open, onClose, eyebrow, eyebrowColor = '#a8f2cf', title, subtitle, children, width = 520 }: RubixModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  useFocusTrap(panelRef, open);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div aria-hidden="true" onClick={onClose} style={{ position: 'absolute', inset: 0, background: 'rgba(4,14,44,0.6)', backdropFilter: 'blur(5px)' }} />
      <div ref={panelRef} tabIndex={-1} className="rubix-modal-panel rubix-scroll" role="dialog" aria-modal="true" aria-label={title} style={{ position: 'relative', width, maxWidth: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '26px 28px 24px', outline: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 14 }}>
          <div>
            {eyebrow && <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: '0.12em', color: eyebrowColor }}>{eyebrow}</div>}
            <div style={{ marginTop: eyebrow ? 12 : 0, fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>{title}</div>
            {subtitle && <div style={{ marginTop: 8, fontSize: 13.5, lineHeight: 1.55, color: 'rgba(226,240,255,0.82)' }}>{subtitle}</div>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            style={{ width: 32, height: 32, flex: '0 0 32px', borderRadius: 11, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(185,220,255,0.28)', color: 'inherit' }}
          >
            ✕
          </button>
        </div>
        <div style={{ marginTop: 22 }}>{children}</div>
      </div>
    </div>
  );
}
