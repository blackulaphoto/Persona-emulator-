/**
 * Landing Page - Persona Evolution Simulator
 *
 * Route: / (root)
 * Premium psychological simulation landing experience
 *
 * IMAGES MUST BE PLACED IN: /public/splash/images/
 * - hero.png
 * - why_its_different.png
 * - how_it_works.png
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LandingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [scrollY, setScrollY] = useState(0);
  const [activeQuestion, setActiveQuestion] = useState(0);
  const [isChecking, setIsChecking] = useState(true);

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

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Cycle through "Have you ever..." questions
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveQuestion((prev) => (prev + 1) % 3);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  function handleCTA() {
    localStorage.setItem('hasSeenLanding', 'true');
    // If user is authenticated, go to personas; otherwise go to signup
    if (user) {
      router.push('/personas');
    } else {
      router.push('/signup');
    }
  }

  // Show loading spinner while checking localStorage
  if (isChecking) {
    return (
      <div className="min-h-screen bg-[#1a1d20] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-[#5B6B4D] border-t-transparent mx-auto mb-4"></div>
          <p className="text-[#8B9D83] font-['Outfit']">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1a1d20]">
      {/* SECTION 1 - HERO */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        {/* Hero background image */}
        <div className="absolute inset-0">
          <img
            src="/splash/images/hero.png"
            alt=""
            className="absolute inset-0 w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#1a1d20]/40 to-[#1a1d20]" />
        </div>

        {/* Hero content */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <h1
            className="text-5xl md:text-7xl font-bold text-[#F8F6F1] mb-6 font-['Crimson_Pro'] leading-tight"
            style={{
              transform: `translateY(${scrollY * 0.3}px)`,
              opacity: 1 - scrollY / 500
            }}
          >
            Who would you be…<br />
            if one moment had gone differently?
          </h1>

          <p
            className="text-xl md:text-2xl text-[#8B9D83] mb-12 font-['Outfit'] max-w-2xl mx-auto"
            style={{
              transform: `translateY(${scrollY * 0.2}px)`,
              opacity: 1 - scrollY / 500
            }}
          >
            A psychological simulation engine that models how life experiences shape personality over time.
          </p>

          <button
            onClick={handleCTA}
            className="bg-[#5B6B4D] hover:bg-[#4a5a3e] text-white font-semibold text-lg px-8 py-4 rounded-lg shadow-2xl transition-all transform hover:scale-105 font-['Outfit']"
            style={{
              opacity: 1 - scrollY / 500
            }}
          >
            Create Your First Persona
          </button>
        </div>

        {/* Scroll indicator */}
        <div
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce"
          style={{ opacity: 1 - scrollY / 300 }}
        >
          <svg className="w-6 h-6 text-[#8B9D83]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* SECTION 2 - THE QUESTION */}
      <section className="relative min-h-screen flex items-center justify-center py-20 bg-gradient-to-b from-[#1a1d20] to-[#0f1215]">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="space-y-8 mb-16">
            <p className="text-2xl md:text-3xl text-[#F8F6F1] font-['Crimson_Pro'] italic leading-relaxed">
              Have you ever…
            </p>

            <div className="min-h-[200px] flex items-center justify-center">
              <QuestionFade
                questions={[
                  "wondered why one childhood moment still echoes?",
                  "noticed how different people break — or grow — from the same pain?",
                  "imagined who you might have been under different circumstances?"
                ]}
                activeIndex={activeQuestion}
              />
            </div>

            <div className="pt-8 border-t border-[#8B9D83]/20">
              <p className="text-2xl text-[#5B6B4D] font-['Outfit'] font-medium">
                This app exists to explore that.
              </p>
            </div>
          </div>

          <button
            onClick={handleCTA}
            className="bg-[#5B6B4D] hover:bg-[#4a5a3e] text-white font-semibold text-lg px-8 py-4 rounded-lg transition-all font-['Outfit']"
          >
            Create Your First Persona
          </button>
        </div>
      </section>

      {/* SECTION 3 - WHAT THIS IS */}
      <section className="relative py-20 bg-[#0f1215]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left: Image */}
            <div className="relative h-[400px] rounded-2xl overflow-hidden">
              <img
                src="/splash/images/why_its_different.png"
                alt=""
                className="absolute inset-0 w-full h-full object-cover"
              />
            </div>

            {/* Right: Content */}
            <div className="space-y-6">
              <div className="space-y-4">
                <p className="text-2xl text-[#F8F6F1] font-['Crimson_Pro'] font-semibold">
                  This is not a quiz.
                </p>
                <p className="text-2xl text-[#F8F6F1] font-['Crimson_Pro'] font-semibold">
                  This is not a diagnosis.
                </p>
                <p className="text-2xl text-[#5B6B4D] font-['Crimson_Pro'] font-bold">
                  This is a simulation.
                </p>
              </div>

              <div className="pt-6 space-y-4 text-[#8B9D83] font-['Outfit']">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-[#5B6B4D] flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p>Personas evolve through experiences</p>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-[#5B6B4D] flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p>Experiences affect traits</p>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-[#5B6B4D] flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p>Interventions alter trajectories</p>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-[#5B6B4D] flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p>Timelines reveal causality</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4 - HOW IT WORKS */}
      <section className="relative py-20 bg-gradient-to-b from-[#0f1215] to-[#1a1d20]">
        {/* Background image */}
        <div className="absolute inset-0 opacity-20">
          <img
            src="/splash/images/how_it_works.png"
            alt=""
            className="absolute inset-0 w-full h-full object-cover"
          />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-6">
          <h2 className="text-4xl md:text-5xl font-bold text-center text-[#F8F6F1] mb-16 font-['Crimson_Pro']">
            How It Works
          </h2>

          <div className="space-y-12">
            <HowItWorksStep
              number="1"
              title="Create a Persona"
              description="Define a starting psychological baseline."
              delay={0}
            />
            <HowItWorksStep
              number="2"
              title="Add Experiences"
              description="Life events — positive, neutral, traumatic — accumulate over time."
              delay={200}
            />
            <HowItWorksStep
              number="3"
              title="Observe Change"
              description="Traits evolve. Patterns emerge. Outcomes diverge."
              delay={400}
            />
          </div>
        </div>
      </section>

      {/* SECTION 5 - WHY IT'S DIFFERENT */}
      <section className="py-20 bg-[#1a1d20]">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-4xl md:text-5xl font-bold text-center text-[#F8F6F1] mb-12 font-['Crimson_Pro']">
            Why It's Different
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            <DifferenceCard
              title="Data-driven psychological modeling"
              icon="🧬"
            />
            <DifferenceCard
              title="Time-based personality evolution"
              icon="⏳"
            />
            <DifferenceCard
              title="Reversible and remixable life paths"
              icon="🔄"
            />
            <DifferenceCard
              title="Designed for exploration, not judgment"
              icon="🔍"
            />
          </div>
        </div>
      </section>

      {/* SECTION 6 - FINAL CTA */}
      <section className="relative py-32 bg-gradient-to-b from-[#1a1d20] via-[#0f1215] to-[#000000]">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <p className="text-3xl md:text-4xl text-[#F8F6F1] mb-8 font-['Crimson_Pro'] italic leading-relaxed">
            Understanding doesn't change the past.
          </p>
          <p className="text-3xl md:text-4xl text-[#5B6B4D] mb-12 font-['Crimson_Pro'] font-semibold">
            But it can change how we see it.
          </p>

          <button
            onClick={handleCTA}
            className="bg-[#5B6B4D] hover:bg-[#4a5a3e] text-white font-semibold text-lg px-12 py-5 rounded-lg shadow-2xl transition-all transform hover:scale-105 font-['Outfit']"
          >
            Create Your First Persona
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#000000] py-8 border-t border-[#8B9D83]/10">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-[#8B9D83]/60 text-sm font-['Outfit']">
            This tool simulates psychological development for educational purposes.
            It is not a diagnostic tool, medical advice, or substitute for therapy.
            All personas are fictional.
          </p>
        </div>
      </footer>
    </div>
  );
}

// Question fade component
function QuestionFade({ questions, activeIndex }: { questions: string[]; activeIndex: number }) {
  return (
    <div className="relative w-full">
      {questions.map((question, idx) => (
        <p
          key={idx}
          className={`text-xl md:text-2xl text-[#8B9D83] font-['Outfit'] transition-all duration-1000 absolute w-full ${
            idx === activeIndex
              ? 'opacity-100 translate-y-0'
              : idx === (activeIndex - 1 + questions.length) % questions.length
              ? 'opacity-0 -translate-y-4'
              : 'opacity-0 translate-y-4'
          }`}
        >
          {question}
        </p>
      ))}
    </div>
  );
}

// How it works step
function HowItWorksStep({
  number,
  title,
  description,
  delay
}: {
  number: string;
  title: string;
  description: string;
  delay: number;
}) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`flex items-start gap-6 transition-all duration-1000 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}
    >
      <div className="flex-shrink-0 w-16 h-16 rounded-full bg-[#5B6B4D]/20 border-2 border-[#5B6B4D] flex items-center justify-center">
        <span className="text-2xl font-bold text-[#5B6B4D] font-['Crimson_Pro']">{number}</span>
      </div>
      <div className="pt-2">
        <h3 className="text-2xl font-bold text-[#F8F6F1] mb-2 font-['Crimson_Pro']">{title}</h3>
        <p className="text-lg text-[#8B9D83] font-['Outfit']">{description}</p>
      </div>
    </div>
  );
}

// Difference card
function DifferenceCard({ title, icon }: { title: string; icon: string }) {
  return (
    <div className="bg-gradient-to-br from-[#2D3136] to-[#1a1d20] p-6 rounded-xl border border-[#8B9D83]/20 hover:border-[#5B6B4D]/40 transition-all">
      <div className="text-4xl mb-3">{icon}</div>
      <p className="text-lg text-[#F8F6F1] font-['Outfit']">{title}</p>
    </div>
  );
}
