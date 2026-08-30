/**
 * Landing Page - Rubicks
 *
 * Route: / (root)
 *
 * Hero image carries the pitch - wordmark, tagline, and feature list are
 * baked into the artwork itself. Two crops exist for two very different
 * aspect ratios: public/landing-hero.png (landscape, desktop/tablet) and
 * public/landing-hero-mobile.png (portrait, phone widths - same scene,
 * feature list stacked below it instead of beside it). This page's job is
 * just: show the right one, and get the visitor into a real anonymous demo
 * session with one click.
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '../contexts/AuthContext';

const MOBILE_BREAKPOINT = '(max-width: 640px)';

export default function LandingPage() {
  const router = useRouter();
  const { user, loading: authLoading, startDemo } = useAuth();
  const [isChecking, setIsChecking] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState('');

  // Which hero crop to show. Only ever read once isChecking is false, i.e.
  // after mount - never during SSR/hydration - so reading matchMedia here
  // can't cause a hydration mismatch.
  useEffect(() => {
    const mq = window.matchMedia(MOBILE_BREAKPOINT);
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

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
    <div className="relative w-screen h-screen overflow-hidden bg-background">
      <Image
        key={isMobile ? 'mobile' : 'desktop'}
        src={isMobile ? '/landing-hero-mobile.png' : '/landing-hero.png'}
        alt="Rubicks - Mapping the pieces. Understanding the person. Advanced human modeling that connects memories, experiences, and behaviors to reveal the full story of who we become."
        fill
        priority
        sizes="100vw"
        className="object-cover object-center"
      />

      {/* CTA sits on the rug, right where it meets the hardwood floor in the artwork - that
          line falls at a different height in each crop, so its position differs per image. */}
      <div
        className="absolute inset-x-0 flex flex-col items-center gap-1.5 px-6"
        style={{ top: isMobile ? '66%' : '87%', transform: 'translateY(-50%)' }}
      >
        <button
          onClick={handleCTA}
          disabled={starting}
          className="btn-primary disabled:opacity-70 disabled:cursor-wait text-sm px-6 py-2.5 shadow-2xl flex flex-col items-center gap-0.5"
        >
          <span>{starting ? 'Starting…' : 'Try Rubicks'}</span>
          {!starting && <span className="text-[10px] font-normal text-white/70">No account required</span>}
        </button>
        {startError && (
          <p className="text-xs text-destructive font-body bg-white/90 rounded px-2 py-1">{startError}</p>
        )}
        <p className="mt-1 max-w-md text-center text-[10px] leading-snug text-slate/80 font-body bg-white/70 backdrop-blur-sm rounded px-2 py-1">
          This tool simulates psychological development for educational purposes.
          It is not a diagnostic tool, medical advice, or substitute for therapy.
          All personas are fictional.
        </p>
      </div>
    </div>
  );
}
