/**
 * Auth Context
 * 
 * Provides authentication state and methods throughout the app
 */
'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import {
  User,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth';
import { auth, hasConfig } from '@/lib/firebase';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signup: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
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
      setLoading(false);
      return;
    }

    // Listen for auth state changes
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Auth helpers: if auth isn't configured, surface clear errors instead of crashing the app at import time.
  async function signup(email: string, password: string) {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    try {
      await createUserWithEmailAndPassword(auth, email, password);
    } catch (error: any) {
      throw new Error(error.message);
    }
  }

  async function login(email: string, password: string) {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (error: any) {
      throw new Error(error.message);
    }
  }

  async function logout() {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    try {
      await signOut(auth);
    } catch (error: any) {
      throw new Error(error.message);
    }
  }

  async function resetPassword(email: string) {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (error: any) {
      throw new Error(error.message);
    }
  }

  async function loginWithGoogle() {
    if (!auth) throw new Error('Authentication is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.');
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (error: any) {
      throw new Error(error.message);
    }
  }

  const value = {
    user,
    loading,
    signup,
    login,
    logout,
    resetPassword,
    loginWithGoogle,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
