/**
 * Firebase Configuration
 *
 * Initializes Firebase app with environment variables
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const isServer = typeof window === 'undefined';

// Local/CI-only: point the client SDK at the real Firebase Auth Emulator
// instead of production Firebase. This is NOT the dev-auth-bypass - it's a
// real Firebase Auth server running on localhost, so signInAnonymously(),
// linkWithCredential(), etc. all behave exactly as they would in
// production, just against demo-project data. Requires no real Firebase
// project or secrets. See NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST in
// frontend/.env.local.example.
const emulatorHost = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST;
const useEmulator = !isServer && process.env.NODE_ENV !== 'production' && !!emulatorHost;

// The emulator needs *a* config shape (apiKey/projectId), but the values
// are never checked against a real project - only used to route to the
// local emulator and tag tokens with a matching project id.
const hasConfig =
  useEmulator ||
  (!!firebaseConfig.apiKey &&
    !!firebaseConfig.authDomain &&
    !!firebaseConfig.projectId &&
    !!firebaseConfig.appId);

const effectiveConfig = useEmulator
  ? {
      apiKey: 'demo-emulator-key',
      authDomain: 'localhost',
      projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || 'demo-rubicks',
      appId: 'demo-emulator-app-id',
    }
  : firebaseConfig;

// Avoid initializing Firebase on the server to prevent SSR build errors.
const app = !isServer && hasConfig
  ? (getApps().length === 0 ? initializeApp(effectiveConfig) : getApp())
  : null;

// Expose auth only when initialized; consumers should guard for null.
const auth = app ? getAuth(app) : null;

if (auth && useEmulator) {
  // Must be called before any other auth operation - safe to call more
  // than once (e.g. React Strict Mode double-invoke) per the Firebase docs.
  connectAuthEmulator(auth, `http://${emulatorHost}`, { disableWarnings: true });
}

// LOCAL-DEV-ONLY AUTH BYPASS gate, shared by AuthContext and authHeaders so
// there is exactly one place that decides whether the bypass may activate.
// Requires ALL of:
//   1. NEXT_PUBLIC_AUTH_DEV_BYPASS=true explicitly set (missing Firebase
//      config alone is never enough - a misconfigured deploy must fail
//      loudly, not silently fall back to a fake signed-in user).
//   2. Not a production build (Next.js sets NODE_ENV=production for
//      `next build`/`next start` regardless of what's left in .env).
//   3. Firebase itself is not actually configured/reachable (hasConfig is
//      false). The instant real config or the emulator is wired up, this
//      is structurally dead code - there's nothing to "forget to turn off".
export const devBypassEnabled =
  !isServer &&
  process.env.NODE_ENV !== 'production' &&
  process.env.NEXT_PUBLIC_AUTH_DEV_BYPASS === 'true' &&
  !hasConfig;

export { app, auth, hasConfig };
