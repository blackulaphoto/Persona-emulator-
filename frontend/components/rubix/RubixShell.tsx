'use client';

import { ReactNode, useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { RubixSidebar, RubixSidebarPersonaContext } from './RubixSidebar';
import { useFocusTrap } from '@/lib/rubix/useFocusTrap';

interface RubixShellProps {
  persona?: RubixSidebarPersonaContext;
  children: ReactNode;
}

/**
 * The Rubix app shell - layered cobalt/indigo background, sidebar, scrollable
 * main content. Every Rubix page (Lives, Create, Dashboard, Build, Full Life,
 * Narrative, Compare, Talk) renders inside this. Background blooms are pure
 * CSS (no JS animation loop) so a large timeline stays smooth.
 *
 * Below 768px the sidebar becomes an off-canvas drawer (see .rubix-shell-*
 * classes in globals.css) opened via a topbar menu button, rather than a
 * fixed 258px column that would eat most of a phone-width viewport.
 */
export function RubixShell({ persona, children }: RubixShellProps) {
  const [navOpen, setNavOpen] = useState(false);
  const pathname = usePathname();
  const sidebarWrapRef = useRef<HTMLDivElement>(null);
  // Only ever activates on mobile, when the sidebar becomes a real dismissible
  // overlay (navOpen is always false on desktop, where it's a permanent,
  // non-modal nav panel that correctly stays outside any focus trap).
  useFocusTrap(sidebarWrapRef, navOpen);

  // Close the drawer on navigation so it doesn't stay open over the next page.
  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!navOpen) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setNavOpen(false);
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [navOpen]);

  return (
    <div className="rubix-scope rubix-app-bg" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', height: '100vh', overflow: 'hidden', position: 'relative' }}>
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: -160,
          left: '38%',
          width: 760,
          height: 520,
          pointerEvents: 'none',
          filter: 'blur(60px)',
          opacity: 0.5,
          animation: 'rubixDrift 14s ease-in-out infinite',
          background: 'radial-gradient(50% 50% at 50% 50%, rgba(140,200,255,0.55) 0%, rgba(140,200,255,0) 70%)',
        }}
      />

      <div className="rubix-mobile-topbar">
        <button
          type="button"
          className="rubix-menu-button"
          onClick={() => setNavOpen(true)}
          aria-label="Open menu"
          aria-expanded={navOpen}
        >
          <span aria-hidden="true" style={{ fontSize: 18, lineHeight: 1 }}>☰</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: 15 }}>
          <img src="/rubicks-icon.png" alt="" aria-hidden="true" style={{ width: 22, height: 22, objectFit: 'contain' }} />
          Rubicks
        </div>
        <div style={{ width: 40 }} aria-hidden="true" />
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0, position: 'relative' }}>
        <div
          className="rubix-shell-backdrop"
          data-open={navOpen ? 'true' : 'false'}
          onClick={() => setNavOpen(false)}
          aria-hidden="true"
        />
        <div ref={sidebarWrapRef} className="rubix-shell-sidebar-wrap" data-open={navOpen ? 'true' : 'false'}>
          <RubixSidebar persona={persona} onClose={() => setNavOpen(false)} />
        </div>
        {/* No z-index here (DOM order alone already paints this above the
            decorative bloom behind it) - position+z-index together would
            create a stacking context that traps any position:fixed
            descendant (RubixDrawer/RubixModal render inside {children}) below
            sibling chrome like .rubix-mobile-topbar instead of letting it
            escape to the viewport-level stack where it belongs. */}
        <main className="rubix-scroll" style={{ position: 'relative', flex: 1, minWidth: 0, height: '100%', overflowY: 'auto', overflowX: 'hidden', padding: '22px 30px 60px' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
