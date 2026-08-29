'use client';

import { FormEvent, useState } from 'react';
import { GoogleAuthProvider, signInWithCredential, AuthCredential } from 'firebase/auth';
import { useAuth } from '@/contexts/AuthContext';
import { auth } from '@/lib/firebase';
import { RubixModal } from './RubixModal';
import { isAccountCollision, friendlyAuthErrorMessage } from '@/lib/authErrors';

interface SaveWorkModalProps {
  open: boolean;
  onClose: () => void;
}

type Collision =
  | { kind: 'email'; email: string }
  | { kind: 'google'; credential: AuthCredential | null };

/**
 * "Save your work" - lets an anonymous demo session attach a real account
 * without losing anything, via convertAnonymousWithEmail/Google
 * (AuthContext), which link credentials onto the SAME Firebase UID rather
 * than creating a new one. If that email/Google account already exists,
 * shows the account-already-exists case explicitly instead of silently
 * discarding or pretending to merge the demo's data (see AuthContext and
 * lib/authErrors for the collision detection).
 */
export function SaveWorkModal({ open, onClose }: SaveWorkModalProps) {
  const { convertAnonymousWithEmail, convertAnonymousWithGoogle, loginWithGoogle, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [signInPassword, setSignInPassword] = useState('');
  const [loading, setLoading] = useState<'google' | 'email' | 'switch' | null>(null);
  const [error, setError] = useState('');
  const [collision, setCollision] = useState<Collision | null>(null);

  function reset() {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setSignInPassword('');
    setLoading(null);
    setError('');
    setCollision(null);
  }

  function handleClose() {
    reset();
    onClose();
  }

  async function handleGoogle() {
    setError('');
    setLoading('google');
    try {
      await convertAnonymousWithGoogle();
      handleClose();
    } catch (err: any) {
      setLoading(null);
      if (err?.code === 'auth/popup-closed-by-user' || err?.code === 'auth/cancelled-popup-request') {
        return; // user backed out of the popup - not an error worth showing
      }
      if (isAccountCollision(err)) {
        setCollision({ kind: 'google', credential: GoogleAuthProvider.credentialFromError(err) });
      } else {
        setError(friendlyAuthErrorMessage(err));
      }
    }
  }

  async function handleEmailSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (password.length < 6) {
      setError('Please choose a password with at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading('email');
    try {
      await convertAnonymousWithEmail(email, password);
      handleClose();
    } catch (err: any) {
      setLoading(null);
      if (isAccountCollision(err)) {
        setCollision({ kind: 'email', email });
      } else {
        setError(friendlyAuthErrorMessage(err));
      }
    }
  }

  async function handleSwitchToExisting() {
    if (!collision) return;
    setError('');
    setLoading('switch');
    try {
      if (collision.kind === 'google') {
        if (collision.credential && auth) {
          await signInWithCredential(auth, collision.credential);
        } else {
          // No reusable credential came back with the error - fall back to
          // a normal fresh Google sign-in to the existing account.
          await loginWithGoogle();
        }
      } else {
        await login(collision.email, signInPassword);
      }
      handleClose();
    } catch (err: any) {
      setLoading(null);
      setError(friendlyAuthErrorMessage(err));
    }
  }

  if (!open) return null;

  return (
    <RubixModal
      open={open}
      onClose={handleClose}
      eyebrow="SAVE YOUR WORK"
      title={collision ? 'That account already exists' : 'Keep this life'}
      subtitle={collision ? undefined : "Create a free account and everything you've built stays exactly as it is."}
      width={440}
    >
      {collision ? (
        <div>
          <p style={{ fontSize: 13.5, lineHeight: 1.6, color: 'rgba(226,240,255,0.85)' }}>
            {collision.kind === 'email' ? `An account already exists for ${collision.email}.` : 'That Google account is already in use.'}{' '}
            Signing into it now won&apos;t bring today&apos;s demo along — what you&apos;ve built here stays behind unless you save it under a different account instead.
          </p>

          {collision.kind === 'email' && (
            <div style={{ marginTop: 16 }}>
              <label className="rubix-field-label" htmlFor="save-switch-password">PASSWORD FOR {collision.email}</label>
              <input
                id="save-switch-password"
                type="password"
                className="rubix-input"
                style={{ marginTop: 9, width: '100%' }}
                value={signInPassword}
                onChange={(e) => setSignInPassword(e.target.value)}
                autoFocus
              />
            </div>
          )}

          {error && (
            <div style={{ marginTop: 14, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
              {error}
            </div>
          )}

          <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 9 }}>
            <button
              type="button"
              className="rubix-btn-ghost"
              disabled={loading === 'switch' || (collision.kind === 'email' && !signInPassword)}
              onClick={handleSwitchToExisting}
            >
              {loading === 'switch' ? 'Signing in…' : 'Sign in to that account'}
            </button>
            <button type="button" className="rubix-btn-primary" onClick={() => { setCollision(null); setError(''); }}>
              Keep exploring the demo
            </button>
          </div>
        </div>
      ) : (
        <div>
          <button type="button" className="rubix-btn-primary" style={{ width: '100%' }} disabled={loading !== null} onClick={handleGoogle}>
            {loading === 'google' ? 'Connecting…' : 'Continue with Google'}
          </button>

          <div style={{ margin: '18px 0', display: 'flex', alignItems: 'center', gap: 12 }} aria-hidden="true">
            <div style={{ flex: 1, height: 1, background: 'rgba(180,215,255,0.18)' }} />
            <span style={{ fontSize: 11.5, color: 'rgba(200,226,255,0.55)' }}>OR</span>
            <div style={{ flex: 1, height: 1, background: 'rgba(180,215,255,0.18)' }} />
          </div>

          <form onSubmit={handleEmailSubmit}>
            <label className="rubix-field-label" htmlFor="save-email">EMAIL</label>
            <input
              id="save-email"
              type="email"
              required
              className="rubix-input"
              style={{ marginTop: 9, width: '100%' }}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <div style={{ marginTop: 12 }}>
              <label className="rubix-field-label" htmlFor="save-password">PASSWORD</label>
              <input
                id="save-password"
                type="password"
                required
                minLength={6}
                className="rubix-input"
                style={{ marginTop: 9, width: '100%' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div style={{ marginTop: 12 }}>
              <label className="rubix-field-label" htmlFor="save-confirm-password">CONFIRM PASSWORD</label>
              <input
                id="save-confirm-password"
                type="password"
                required
                className="rubix-input"
                style={{ marginTop: 9, width: '100%' }}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            {error && (
              <div style={{ marginTop: 14, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
                {error}
              </div>
            )}

            <div style={{ marginTop: 18 }}>
              <button type="submit" className="rubix-btn-primary" style={{ width: '100%' }} disabled={loading !== null}>
                {loading === 'email' ? 'Creating account…' : 'Create account'}
              </button>
            </div>
          </form>
        </div>
      )}
    </RubixModal>
  );
}
