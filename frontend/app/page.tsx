/**
 * Landing Page - Rubicks
 *
 * Route: / (root)
 *
 * Single hero image (public/landing-hero.png) carries the pitch - wordmark,
 * tagline, and feature list are baked into the artwork itself. This page's
 * job is just: show it, and get the visitor into a real anonymous demo
 * session with one click.
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '../contexts/AuthContext';

export default function LandingPage() {
  const router = useRouter();
  const { user, loading: authLoading, startDemo } = useAuth();
  const [isChecking, setIsChecking] = useState(true);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState('');

  // Check if user is authenticated or has seen landing page before
  useEffect(() => {
    // Wait for auth to finish loading
    if (authLoading) {
      return;
    }

    // If user is authenticated, skip landing page
    if (user) {
      router.push('/personas');
      return;
    }

    // If user has seen landing page before, skip to personas (will redirect to login)
    const hasSeenLanding = localStorage.getItem('hasSeenLanding');
    if (hasSeenLanding === 'true') {
      router.push('/personas');
    } else {
      setIsChecking(false);
    }
  }, [user, authLoading, router]);

  async function handleCTA() {
    localStorage.setItem('hasSeenLanding', 'true');
    // Already authenticated (registered or an existing demo session) -
    // continue as that user. Never start a second anonymous account for
    // someone who's already signed in.
    if (user) {
      router.push('/personas');
      return;
    }
    // Try Rubicks: real Firebase anonymous sign-in, no registration step.
    setStartError('');
    setStarting(true);
    try {
      await startDemo();
      router.push('/personas');
    } catch (err: any) {
      setStartError(err?.message || 'Could not start your demo. Please try again.');
      setStarting(false);
    }
  }

  // Show loading spinner while checking localStorage
  if (isChecking) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary border-t-transparent mx-auto mb-4"></div>
          <p className="text-muted-foreground font-body">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-6 py-12">
      <div className="max-w-5xl w-full text-center">
        <Image
          src="/landing-hero.png"
          alt="Rubicks - Mapping the pieces. Understanding the person. Advanced human modeling that connects memories, experiences, and behaviors to reveal the full story of who we become."
          width={1672}
          height={941}
          priority
          className="w-full h-auto rounded-3xl shadow-2xl border border-black/5"
        />

        <div className="mt-10 flex flex-col items-center gap-3">
          <button
            onClick={handleCTA}
            disabled={starting}
            className="btn-primary disabled:opacity-70 disabled:cursor-wait text-lg px-10 py-4 flex flex-col items-center gap-0.5"
          >
            <span>{starting ? 'Starting…' : 'Try Rubicks'}</span>
            {!starting && <span className="text-xs font-normal text-white/70">No account required</span>}
          </button>
          {startError && (
            <p className="text-sm text-destructive font-body">{startError}</p>
          )}
        </div>
      </div>

      <footer className="mt-14 max-w-2xl text-center">
        <p className="text-xs text-muted-foreground font-body leading-relaxed">
          This tool simulates psychological development for educational purposes.
          It is not a diagnostic tool, medical advice, or substitute for therapy.
          All personas are fictional.
        </p>
      </footer>
    </div>
  );
}
