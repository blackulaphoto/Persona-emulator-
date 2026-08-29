'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export interface RubixSidebarPersonaContext {
  id: string;
  name: string;
}

interface RubixSidebarProps {
  /** Present only when viewing a specific persona - adds the persona-scoped nav section. */
  persona?: RubixSidebarPersonaContext;
  /** Called after a nav link is clicked - lets RubixShell close the mobile drawer immediately rather than waiting for the route-change effect. */
  onClose?: () => void;
}

interface NavItem {
  key: string;
  label: string;
  href: string;
  dot: string;
}

const DOT = {
  cyan: '#6fe3ff',
  blue: '#7fb2ff',
  violet: '#b39bff',
  green: '#6fe3b0',
  coral: '#ff9282',
};

function NavLink({ item, active, onClick }: { item: NavItem; active: boolean; onClick?: () => void }) {
  return (
    <Link href={item.href} className="rubix-nav-item" data-active={active ? 'true' : 'false'} onClick={onClick}>
      <span
        aria-hidden="true"
        style={{ width: 9, height: 9, borderRadius: 3, flex: '0 0 9px', background: item.dot, boxShadow: `0 0 10px ${item.dot}` }}
      />
      <span>{item.label}</span>
    </Link>
  );
}

/** Real Rubix sidebar - Lives always, persona-scoped destinations when viewing a life, real signed-in user. No fake subscription tier, no "Mobile" nav item. */
export function RubixSidebar({ persona, onClose }: RubixSidebarProps) {
  const pathname = usePathname() || '';
  const { user, logout } = useAuth();
  const router = useRouter();

  const globalItems: NavItem[] = [{ key: 'lives', label: 'Lives', href: '/personas', dot: DOT.cyan }];

  const personaItems: NavItem[] = persona
    ? [
        { key: 'dashboard', label: persona.name, href: `/persona/${persona.id}`, dot: DOT.blue },
        { key: 'build', label: 'Build their life', href: `/persona/${persona.id}/build`, dot: DOT.coral },
        { key: 'timeline', label: 'Full life', href: `/persona/${persona.id}/timeline`, dot: DOT.cyan },
        { key: 'narrative', label: 'Narrative', href: `/persona/${persona.id}/narrative`, dot: DOT.violet },
        { key: 'compare', label: 'Compare', href: `/persona/${persona.id}/compare`, dot: DOT.green },
        { key: 'talk', label: `Talk to ${persona.name}`, href: `/persona/${persona.id}/talk`, dot: DOT.coral },
      ]
    : [];

  const isActive = (href: string) => (href === '/personas' ? pathname === '/personas' : pathname === href);

  async function handleLogout() {
    try {
      await logout();
      router.push('/login');
    } catch {
      // logout() already surfaces its own error state via AuthContext consumers if needed
    }
  }

  const initial = (user?.displayName || user?.email || '?').trim().charAt(0).toUpperCase();

  return (
    <aside className="rubix-sidebar rubix-scroll" style={{ position: 'relative', zIndex: 3, width: 258, flex: '0 0 258px', height: '100vh', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column', padding: '26px 18px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '0 6px 4px' }}>
        <div className="rubix-diamond" style={{ width: 38, height: 38, flex: '0 0 38px' }} />
        <div>
          <div style={{ fontSize: 23, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1 }}>Rubix</div>
          <div style={{ fontSize: 11.5, fontWeight: 400, color: 'rgba(200,224,255,0.62)', marginTop: 4 }}>Build minds. Understand lives.</div>
        </div>
      </div>

      <nav style={{ marginTop: 26, display: 'flex', flexDirection: 'column', gap: 5 }} aria-label="Primary">
        {globalItems.map((item) => (
          <NavLink key={item.key} item={item} active={isActive(item.href)} onClick={onClose} />
        ))}
      </nav>

      {persona && (
        <nav style={{ marginTop: 18, paddingTop: 16, borderTop: '1px solid rgba(150,195,255,0.16)', display: 'flex', flexDirection: 'column', gap: 5 }} aria-label={`${persona.name}'s life`}>
          <div style={{ padding: '0 13px 6px', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', color: 'rgba(200,226,255,0.5)' }}>
            THIS LIFE
          </div>
          {personaItems.map((item) => (
            <NavLink key={item.key} item={item} active={isActive(item.href)} onClick={onClose} />
          ))}
        </nav>
      )}

      <div style={{ marginTop: 'auto', paddingTop: 22, flex: '0 0 auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '10px 12px', borderRadius: 15, background: 'linear-gradient(165deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04))', border: '1px solid rgba(160,200,255,0.16)' }}>
            <div className="rubix-avatar" style={{ width: 32, height: 32, flex: '0 0 32px', fontSize: 13, background: 'linear-gradient(160deg,#9fd4ff,#3f77ee)' }}>
              {initial}
            </div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontSize: 12.5, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.displayName || user.email}
              </div>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              style={{ fontSize: 11.5, color: 'rgba(200,224,255,0.6)', background: 'transparent', border: 'none', cursor: 'pointer', padding: 4 }}
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
