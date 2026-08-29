'use client';

import { ReactNode, useEffect, useRef } from 'react';
import { useFocusTrap } from '@/lib/rubix/useFocusTrap';

interface RubixDrawerProps {
  open: boolean;
  onClose: () => void;
  kind: string;
  kindColor?: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
}

/**
 * The single reusable right-overlay drawer shell (desktop) - Experience,
 * Pattern, Hypothesis, Attachment, Therapy, and Starting Conditions detail
 * all render through this same component with their own content, rather
 * than each building their own overlay. On narrow viewports .rubix-drawer-panel
 * itself goes full-width (see globals.css), turning this into a full-screen
 * sheet without any separate mobile variant to maintain.
 */
export function RubixDrawer({ open, onClose, kind, kindColor = '#7fb2ff', title, subtitle, children }: RubixDrawerProps) {
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
    <div style={{ position: 'fixed', inset: 0, zIndex: 60, display: 'flex', justifyContent: 'flex-end' }}>
      <div
        aria-hidden="true"
        onClick={onClose}
        style={{ position: 'absolute', inset: 0, background: 'rgba(4,14,44,0.55)', backdropFilter: 'blur(4px)' }}
      />
      <div ref={panelRef} tabIndex={-1} className="rubix-drawer-panel rubix-scroll" role="dialog" aria-modal="true" aria-label={title} style={{ position: 'relative', width: 560, maxWidth: '92vw', height: '100vh', overflowY: 'auto', padding: '26px 28px 44px', outline: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}>
          <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: '0.12em', color: kindColor }}>{kind}</div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            style={{ width: 34, height: 34, borderRadius: 11, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(180,215,255,0.26)', color: 'inherit' }}
          >
            ✕
          </button>
        </div>
        <div style={{ marginTop: 16, fontSize: 25, fontWeight: 700, letterSpacing: '-0.025em', lineHeight: 1.2 }}>{title}</div>
        {subtitle && <div style={{ marginTop: 10, fontSize: 14, lineHeight: 1.6, color: 'rgba(226,240,255,0.85)' }}>{subtitle}</div>}
        <div style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 12 }}>{children}</div>
      </div>
    </div>
  );
}

interface RubixDrawerSectionProps {
  label: string;
  meta?: string;
  metaColor?: string;
  children?: ReactNode;
}

/** One bordered section inside a drawer - label/meta header, arbitrary body. */
export function RubixDrawerSection({ label, meta, metaColor = 'rgba(210,232,255,0.75)', children }: RubixDrawerSectionProps) {
  return (
    <div style={{ borderRadius: 18, padding: 18, background: 'linear-gradient(165deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04))', border: '1px solid rgba(180,215,255,0.2)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: '0.1em', color: 'rgba(200,226,255,0.66)' }}>{label}</div>
        {meta && <div style={{ fontSize: 11, fontWeight: 600, color: metaColor }}>{meta}</div>}
      </div>
      {children && <div style={{ marginTop: 10 }}>{children}</div>}
    </div>
  );
}
