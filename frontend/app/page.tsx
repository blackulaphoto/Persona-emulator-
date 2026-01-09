"use client";

// Enhanced Landing Page - Persona Evolution Simulator
// High-impact, futuristic redesign with bold gradients, dynamic reflections and motion
// Route: /  (root)

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, useScroll, useTransform } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";

export default function LandingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [activeQuestion, setActiveQuestion] = useState(0);
  const [isChecking, setIsChecking] = useState(true);

  // ----- SCROLL-BASED PARALLAX --------------------------------------------------
  const { scrollY } = useScroll();
  const headingY = useTransform(scrollY, [0, 600], [0, 200]);
  const headingOpacity = useTransform(scrollY, [0, 600], [1, 0]);

  // ----- ROUTING / AUTH ---------------------------------------------------------
  useEffect(() => {
    if (authLoading) return;
    if (user) {
      router.push("/personas");
      return;
    }
    const hasSeenLanding = localStorage.getItem("hasSeenLanding");
    if (hasSeenLanding === "true") {
      router.push("/personas");
    } else {
      setIsChecking(false);
    }
  }, [user, authLoading, router]);

  // ----- CYCLING QUESTIONS ------------------------------------------------------
  useEffect(() => {
    const interval = setInterval(
      () => setActiveQuestion((prev) => (prev + 1) % 3),
      3500
    );
    return () => clearInterval(interval);
  }, []);

  // ----- CTA HANDLER ------------------------------------------------------------
  function handleCTA() {
    localStorage.setItem("hasSeenLanding", "true");
    if (user) {
      router.push("/personas");
    } else {
      router.push("/signup");
    }
  }

  // ----- LOADING STATE ----------------------------------------------------------
  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-splash-bg-1 via-splash-bg-2 to-splash-bg-3">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-splash-accent border-t-transparent mx-auto mb-4" />
          <p className="text-splash-text font-['Outfit']">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-x-hidden bg-splash-bg-4 text-white">
      {/* BACKGROUND GLOW & LINES --------------------------------------------------*/}
      <div className="pointer-events-none select-none absolute inset-0 -z-10 [mask-image:radial-gradient(ellipse_at_center,rgba(255,255,255,0.8)_0%,transparent_70%)]">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 via-fuchsia-500/10 to-purple-600/5" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(0,255,255,0.15),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(255,0,90,0.15),transparent_60%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(115deg,transparent_0%,rgba(255,255,255,0.04)_50%,transparent_100%)] [background-size:3px_3px] opacity-30" />
      </div>

      {/* HERO ---------------------------------------------------------------------*/}
      <section className="relative flex flex-col items-center justify-center h-screen px-6 text-center">
        {/* REFLECTION */}
        <div className="absolute inset-x-0 bottom-0 h-1/3 [mask-image:linear-gradient(to_top,rgba(255,255,255,0.45),transparent)] overflow-hidden">
          <motion.div
            className="w-full h-full bg-gradient-to-r from-indigo-500/30 via-fuchsia-500/20 to-purple-600/30 blur-2xl"
            style={{ y: headingY, opacity: headingOpacity }}
          />
        </div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
          style={{ y: headingY, opacity: headingOpacity }}
          className="font-extrabold leading-tight tracking-tight text-5xl md:text-7xl lg:text-8xl bg-gradient-to-r from-indigo-400 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent drop-shadow-[0_2px_16px_rgba(236,72,255,0.45)]">
          Who would you be…
          <br />
          <span className="whitespace-nowrap">if one moment had gone differently?</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 1, ease: "easeOut" }}
          className="mt-8 max-w-2xl mx-auto text-lg md:text-xl text-splash-text/90">
          A psychological simulation engine that <span className="font-semibold">models how life experiences shape personality</span> over time.
        </motion.p>

        <motion.button
          whileHover={{ scale: 1.07 }}
          whileTap={{ scale: 0.96 }}
          onClick={handleCTA}
          className="mt-12 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-500 to-fuchsia-500 shadow-lg shadow-indigo-500/30 hover:shadow-fuchsia-500/40 font-semibold text-lg">
          Create Your First Persona
        </motion.button>
      </section>

      {/* FEATURES -----------------------------------------------------------------*/}
      <section className="relative py-24 px-6 md:px-12 lg:px-24 bg-splash-bg-4">
        <h2 className="text-center text-3xl md:text-4xl font-semibold mb-16 bg-gradient-to-r from-indigo-400 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent">
          Why It’s Different
        </h2>
        <div className="grid gap-12 md:grid-cols-3 max-w-6xl mx-auto">
          {[
            {
              title: "Hyper-Realistic Personas",
              desc: "Built with data-driven psychological modeling and machine learning algorithms that grow with every simulation.",
            },
            {
              title: "Live Time-Warp Scenarios",
              desc: "Fast-forward and rewind through pivotal life events with real-time personality adaptation.",
            },
            {
              title: "Research-Grade Insights",
              desc: "Visualize OCEAN trait deltas, resilience curves and growth charts inside an intuitive dashboard.",
            },
          ].map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: idx * 0.15 }}
              className="p-8 rounded-2xl bg-splash-card backdrop-blur-xl ring-1 ring-white/5 hover:ring-fuchsia-500/40 shadow-xl shadow-black/30 flex flex-col justify-between group">
              <div>
                <h3 className="text-xl font-semibold mb-4 text-white/90 group-hover:text-fuchsia-400">
                  {item.title}
                </h3>
                <p className="text-white/60 leading-relaxed">
                  {item.desc}
                </p>
              </div>
              <div className="mt-6 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
              <div className="mt-6 text-right">
                <span className="text-sm text-fuchsia-400 group-hover:text-indigo-300 transition-colors">Learn&nbsp;more&nbsp;→</span>
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
