/**
 * Auth Context
 *
 * Provides authentication state and methods throughout the app.
 *
 * Three real Firebase authentication modes, no shared/fake identifiers:
 *  - Anonymous demo (startDemo) - a real, unique Firebase UID with no
 *    registration step. This is what "Try Rubicks" calls.
 *  - Email/password (signup, login)
 *  - Google (loginWithGoogle)
 *
 * An anonymous session can later be upgraded to a real account WITHOUT
 * losing its data, because linking keeps the same Firebase UID:
 *  - convertAnonymousWithEmail attaches email/password credentials to the
 *    current anonymous user via linkWithCredential.
 *  - convertAnonymousWithGoogle attaches a Google credential to the current
 *    anonymous user via linkWithPopup.
 * Neither ever signs the user out and creates a new one - every Rubicks
 * record already owned by that UID stays owned by it automatically, since
 * the backend keys everything off the Firebase UID (see
 * backend/app/core/auth.py::get_current_user).
 */
'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import {
  User,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInAnonymously,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  EmailAuthProvider,
  signInWithPopup,
  linkWithCredential,
  linkWithPopup,
} from 'firebase/auth';
import { auth, devBypassEnabled } from '@/lib/firebase';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  /** True when `user` is a real Firebase anonymous user - a "Try Rubicks" demo session that hasn't been saved to an account yet. */
  isAnonymous: boolean;
  /** Enter the app with no account: signs in anonymously if nobody is signed in yet, otherwise no-ops. Never replaces an already-authenticated session (anonymous or registered). */
  startDemo: () => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  /** Save the current demo session by attaching email/password credentials to the SAME Firebase user, so every persona/experience/etc. it created stays attached. Throws with code 'auth/email-already-in-use' if that email is already a registered account. */
  convertAnonymousWithEmail: (email: string, password: string) => Promise<void>;
  /** Save the current demo session by attaching a Google credential to the SAME Firebase user. Throws with code 'auth/credential-already-in-use' if that Google account already exists. */
  convertAnonymousWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If auth isn't configured (e.g., missing env vars), skip initializing Firebase on server/SSR.
    if (!auth) {
      if (devBypassEnabled) {
        // LOCAL-DEV-ONLY AUTH BYPASS - gated in lib/firebase.ts
        // (devBypassEnabled): requires an explicit opt-in env var, a
        // non-production build, AND Firebase being genuinely unconfigured.
        // Mirrors lib/authHeaders.ts and backend/app/core/auth.py's own
        // bypass. `auth` is non-null the instant real Firebase config or
        // the Auth Emulator is set up, so this branch is then unreachable
        // regardless of the flag - there's nothing to forget to turn off.
        setUser({ uid: 'dev-local-user', email: 'dev@local.test', displayName: 'Dev User (no auth configured)', isAnonymous: false } as unknown as User);
      } else {
        setUser(null);
      }
      setLoading(false);
      return;
    }

    // Listen for auth state changes - fires for anonymous, email/password,
    // and Google users identically, and again after a successful link
    // (same uid, updated providerData).
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  function requireAuth() {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    return auth;
  }

  // Firebase's onAuthStateChanged is NOT reliably fired after
  // linkWithCredential/linkWithPopup (a known SDK gap - the link succeeds
  // and auth.currentUser is updated, but existing listeners often don't
  // re-fire since the uid didn't change). Every function below that changes
  // what the signed-in user looks like applies the operation's own returned
  // user directly, rather than only waiting on the passive listener - and
  // spreads it into a new object so React's setState reference check can't
  // skip the re-render even if the SDK mutated the User object in place.
  function applyUser(nextUser: User | null) {
    setUser(nextUser ? ({ ...nextUser } as User) : null);
  }

  async function startDemo() {
    const a = requireAuth();
    // A registered user (or an existing demo session) clicking "Try
    // Rubicks" just continues as themselves - never replace an existing
    // session with a brand new anonymous one.
    if (a.currentUser) return;
    const { user: nextUser } = await signInAnonymously(a);
    applyUser(nextUser);
  }

  async function signup(email: string, password: string) {
    const a = requireAuth();
    const { user: nextUser } = await createUserWithEmailAndPassword(a, email, password);
    applyUser(nextUser);
  }

  async function login(email: string, password: string) {
    const a = requireAuth();
    const { user: nextUser } = await signInWithEmailAndPassword(a, email, password);
    applyUser(nextUser);
  }

  async function logout() {
    const a = requireAuth();
    await signOut(a);
    applyUser(null);
  }

  async function resetPassword(email: string) {
    const a = requireAuth();
    await sendPasswordResetEmail(a, email);
  }

  async function loginWithGoogle() {
    const a = requireAuth();
    const provider = new GoogleAuthProvider();
    const { user: nextUser } = await signInWithPopup(a, provider);
    applyUser(nextUser);
  }

  async function convertAnonymousWithEmail(email: string, password: string) {
    const a = requireAuth();
    const current = a.currentUser;
    if (!current || !current.isAnonymous) {
      throw new Error('No demo session to save - not currently signed in anonymously.');
    }
    const credential = EmailAuthProvider.credential(email, password);
    // linkWithCredential, not createUserWithEmailAndPassword - this keeps
    // the SAME Firebase UID, which is the entire point: every persona,
    // experience, snapshot, etc. already owned by this UID stays owned by
    // it with zero backend changes needed.
    const { user: nextUser } = await linkWithCredential(current, credential);
    applyUser(nextUser);
  }

  async function convertAnonymousWithGoogle() {
    const a = requireAuth();
    const current = a.currentUser;
    if (!current || !current.isAnonymous) {
      throw new Error('No demo session to save - not currently signed in anonymously.');
    }
    const provider = new GoogleAuthProvider();
    // linkWithPopup, not signInWithPopup - keeps the SAME Firebase UID.
    const { user: nextUser } = await linkWithPopup(current, provider);
    applyUser(nextUser);
  }

  const value: AuthContextType = {
    user,
    loading,
    isAnonymous: !!user?.isAnonymous,
    startDemo,
    signup,
    login,
    loginWithGoogle,
    convertAnonymousWithEmail,
    convertAnonymousWithGoogle,
    logout,
    resetPassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
