/**
 * Firebase Configuration
 * 
 * Initializes Firebase app with environment variables
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const isServer = typeof window === 'undefined';
const hasConfig =
  !!firebaseConfig.apiKey &&
  !!firebaseConfig.authDomain &&
  !!firebaseConfig.projectId &&
  !!firebaseConfig.appId;

// Avoid initializing Firebase on the server to prevent SSR build errors.
const app = !isServer && hasConfig
  ? (getApps().length === 0 ? initializeApp(firebaseConfig) : getApp())
  : null;

// Expose auth only when initialized; consumers should guard for null.
const auth = app ? getAuth(app) : null;

export { app, auth, hasConfig };
