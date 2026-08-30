/**
 * Login Page - Rubix Design System
 *
 * User authentication with email/password or Google. Uses the same
 * .rubix-* token/class layer (app/globals.css) and layout patterns as the
 * rest of the signed-in app (see components/rubix/SaveWorkModal.tsx for the
 * equivalent auth form used mid-app), rather than the older Apple-inspired
 * glass-card theme.
 */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { login, loginWithGoogle, resetPassword, isAnonymous } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    try {
      setError('');
      setMessage('');
      setLoading(true);
      await login(email, password);
      router.push('/personas');
    } catch (err: any) {
      setError(err.message || 'Failed to log in');
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    try {
      setError('');
      setMessage('');
      setLoading(true);
      await loginWithGoogle();
      router.push('/personas');
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google');
    } finally {
      setLoading(false);
    }
  }

  async function handleForgotPassword() {
    if (!email) {
      return setError('Please enter your email address');
    }

    try {
      setError('');
      setMessage('');
      setLoading(true);
      await resetPassword(email);
      setMessage('Password reset email sent! Check your inbox.');
    } catch (err: any) {
      setError(err.message || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rubix-scope rubix-app-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div className="rubix-modal-panel" style={{ width: 440, maxWidth: '100%', padding: '30px 28px 26px' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9 }}>
          <img src="/rubicks-icon.png" alt="" aria-hidden="true" style={{ width: 26, height: 26, objectFit: 'contain' }} />
          <span style={{ fontWeight: 700, fontSize: 16 }}>Rubicks</span>
        </div>

        {/* Header */}
        <div style={{ marginTop: 20, textAlign: 'center' }}>
          <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em' }}>Welcome back</div>
          <div style={{ marginTop: 7, fontSize: 13.5, color: 'rgba(216,234,255,0.7)' }}>
            Log in to continue your simulations
          </div>
        </div>

        {/* Guest-session warning - signing into a different account here leaves today's demo work behind unless it was saved first. */}
        {isAnonymous && (
          <div style={{ marginTop: 20, padding: '11px 14px', borderRadius: 12, fontSize: 13, lineHeight: 1.55, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
            You&apos;re currently exploring as a guest. Signing in here won&apos;t bring that work with it - go back and use <strong>Save your work</strong> first if you want to keep it.
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div style={{ marginTop: 20, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(255,210,200,0.95)', background: 'rgba(255,120,100,0.12)', border: '1px solid rgba(255,150,135,0.28)' }} role="alert">
            {error}
          </div>
        )}

        {/* Success Message */}
        {message && (
          <div style={{ marginTop: 20, padding: '11px 14px', borderRadius: 12, fontSize: 13, color: 'rgba(180,255,210,0.95)', background: 'rgba(100,255,150,0.12)', border: '1px solid rgba(140,255,180,0.28)' }} role="status">
            {message}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ marginTop: 22 }}>
          <label className="rubix-field-label" htmlFor="login-email">EMAIL ADDRESS</label>
          <input
            id="login-email"
            type="email"
            placeholder="you@example.com"
            className="rubix-input"
            style={{ marginTop: 9, width: '100%' }}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <div style={{ marginTop: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="rubix-field-label" htmlFor="login-password">PASSWORD</label>
              <button
                type="button"
                onClick={handleForgotPassword}
                style={{ background: 'none', border: 'none', padding: 0, fontSize: 12.5, fontWeight: 600, color: 'var(--rubix-blue)', cursor: 'pointer' }}
              >
                Forgot password?
              </button>
            </div>
            <input
              id="login-password"
              type="password"
              placeholder="••••••••"
              className="rubix-input"
              style={{ marginTop: 9, width: '100%' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="rubix-btn-primary" style={{ width: '100%', marginTop: 20 }} disabled={loading}>
            {loading ? 'Logging in…' : 'Log In'}
          </button>
        </form>

        {/* Divider */}
        <div style={{ margin: '20px 0', display: 'flex', alignItems: 'center', gap: 12 }} aria-hidden="true">
          <div style={{ flex: 1, height: 1, background: 'rgba(180,215,255,0.18)' }} />
          <span style={{ fontSize: 11.5, color: 'rgba(200,226,255,0.55)' }}>OR</span>
          <div style={{ flex: 1, height: 1, background: 'rgba(180,215,255,0.18)' }} />
        </div>

        {/* Google Sign In */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="rubix-btn-ghost"
          style={{ width: '100%' }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </button>

        {/* Sign Up Link */}
        <div style={{ textAlign: 'center', marginTop: 18, fontSize: 13.5, color: 'rgba(216,234,255,0.7)' }}>
          Don&apos;t have an account?{' '}
          <Link href="/signup" style={{ color: 'var(--rubix-blue)', fontWeight: 600 }}>
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
