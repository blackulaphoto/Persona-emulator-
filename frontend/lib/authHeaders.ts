/**
 * Shared Firebase auth header helper.
 *
 * Previously duplicated three times (lib/api.ts, components/PersonaNarrative.tsx,
 * components/FeedbackModal.tsx). Every authenticated backend call should go
 * through this one function so there is exactly one place that knows how to
 * get a real Firebase ID token. Anonymous demo users, email/password users,
 * and Google users all reach this the same way - auth.currentUser.getIdToken()
 * works identically for all three, so there is no demo-specific branch here.
 */
import { auth, hasConfig, devBypassEnabled } from '@/lib/firebase';

export async function getAuthHeaders(): Promise<HeadersInit> {
  // LOCAL-DEV-ONLY AUTH BYPASS - see devBypassEnabled in lib/firebase.ts for
  // the full gating (explicit opt-in env var, non-production, no Firebase
  // config reachable at all). Mirrors backend/app/core/auth.py's own gate.
  if (devBypassEnabled) {
    return {
      Authorization: 'Bearer dev-local-bypass',
      'Content-Type': 'application/json',
    };
  }
  if (!hasConfig || !auth) {
    throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
  }
  const user = auth.currentUser;
  if (!user) {
    throw new Error('Not authenticated');
  }
  const token = await user.getIdToken();
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}
