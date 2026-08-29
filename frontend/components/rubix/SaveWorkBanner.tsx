'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { SaveWorkModal } from './SaveWorkModal';

const DISMISS_KEY = 'rubicks_save_work_dismissed';

/**
 * Slim, dismissible "save your work" nudge for anonymous demo sessions -
 * rendered once in RubixShell so it appears app-wide without every page
 * wiring it up individually. Deliberately not a full-screen interruption:
 * dismissing it just hides it for the rest of this browser tab's session
 * (sessionStorage, not localStorage) so it comes back on the next visit
 * rather than nagging every navigation forever, but also doesn't reappear
 * mid-session after someone has already dismissed it once.
 */
export function SaveWorkBanner() {
  const { isAnonymous } = useAuth();
  const [dismissed, setDismissed] = useState(true); // default hidden until we've checked sessionStorage, avoids a flash
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    try {
      setDismissed(sessionStorage.getItem(DISMISS_KEY) === 'true');
    } catch {
      setDismissed(false);
    }
  }, []);

  if (!isAnonymous || dismissed) return null;

  function dismiss() {
    setDismissed(true);
    try {
      sessionStorage.setItem(DISMISS_KEY, 'true');
    } catch {
      // sessionStorage unavailable (private mode, etc.) - dismissal just won't persist, not worth failing over
    }
  }

  return (
    <>
      <div
        role="status"
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap',
          padding: '10px 16px', marginBottom: 18, borderRadius: 14,
          background: 'linear-gradient(120deg, rgba(140,200,255,0.16), rgba(120,140,255,0.08))',
          border: '1px solid rgba(160,205,255,0.25)',
        }}
      >
        <div style={{ fontSize: 13, color: 'rgba(226,240,255,0.88)' }}>
          You&apos;re exploring as a guest. <strong>Save your work</strong> to keep it.
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <button type="button" className="rubix-btn-primary" style={{ padding: '7px 16px', fontSize: 12.5 }} onClick={() => setModalOpen(true)}>
            Save your work
          </button>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Dismiss"
            style={{ width: 28, height: 28, borderRadius: 9, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, background: 'transparent', border: '1px solid rgba(180,215,255,0.22)', color: 'rgba(210,232,255,0.7)' }}
          >
            ✕
          </button>
        </div>
      </div>
      <SaveWorkModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
