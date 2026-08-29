/**
 * Shared Firebase auth header helper.
 *
 * Previously duplicated three times (lib/api.ts, components/PersonaNarrative.tsx,
 * components/FeedbackModal.tsx). Every authenticated backend call should go
 * through this one function so there is exactly one place that knows how to
 * get a real Firebase ID token.
 */
import { auth, hasConfig } from '@/lib/firebase';

export async function getAuthHeaders(): Promise<HeadersInit> {
  // QA-ONLY LOCAL FALLBACK - mirrors backend/app/core/auth.py's
  // _DEV_NO_FIREBASE_CONFIGURED branch. Only reachable when this checkout
  // has no NEXT_PUBLIC_FIREBASE_* env vars at all, i.e. real auth is
  // already impossible here regardless of this branch. Never fires once
  // real Firebase config exists.
  if (!hasConfig) {
    return {
      Authorization: 'Bearer dev-local-bypass',
      'Content-Type': 'application/json',
    };
  }
  if (!auth) {
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
