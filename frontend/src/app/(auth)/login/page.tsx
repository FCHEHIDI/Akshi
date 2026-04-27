"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { setAccessToken, isAuthenticated } from "@/lib/auth";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" as const } },
};

function CosmicGrain() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 opacity-[0.04] z-0"
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        backgroundSize: "256px 256px",
      }}
    />
  );
}

function ConcentricWaves({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 600 600"
      className={"pointer-events-none select-none absolute " + (className ?? "")}
      fill="none"
    >
      {[80, 160, 240, 320, 400, 480].map((r) => (
        <circle key={r} cx="300" cy="300" r={r} stroke="#FF00C8" strokeWidth="0.5" opacity={0.05 + (480 - r) * 0.0003} />
      ))}
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) router.replace("/dashboard");
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { error?: string }).error ?? "Invalid credentials");
      }
      const data = await res.json() as { access_token: string };
      setAccessToken(data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] overflow-hidden relative">
      <CosmicGrain />

      {/* Radial violet top glow */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          background: "radial-gradient(ellipse 80% 60% at 50% -10%, #3B006A 0%, transparent 70%)",
          opacity: 0.6,
        }}
      />

      {/* Concentric waves behind card */}
      <ConcentricWaves className="left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] opacity-40 z-0" />

      {/* Magenta smoke glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full blur-[120px] z-0"
        style={{ background: "var(--accent-teal)", opacity: 0.07 }}
      />

      {/* Card */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="show"
        className="relative z-10 w-full max-w-sm mx-6"
      >
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)]/90 backdrop-blur-md px-8 py-10 shadow-[0_0_60px_rgba(59,0,106,0.4)]">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <Link href="/">
              <Image src="/logo_principal.png" alt="Akshi" width={200} height={62} className="h-16 w-auto" priority />
            </Link>
          </div>

          {/* Tagline */}
          <p
            className="text-center text-[10px] font-medium uppercase tracking-[0.2em] text-[var(--accent-teal)] mb-8"
            style={{ fontFamily: "var(--font-orbitron)" }}
          >
            Observability Beyond Vision
          </p>

          <h1 className="text-lg font-semibold text-center mb-1">Welcome back</h1>
          <p className="text-sm text-[var(--foreground-muted)] text-center mb-8">Sign in to your workspace</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-[var(--foreground-muted)]" htmlFor="email">
                Work email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-10 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)] focus:border-[var(--accent-teal)] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-[var(--foreground-muted)]" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-10 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)] focus:border-[var(--accent-teal)] transition-colors"
              />
            </div>

            {error && (
              <p className="text-xs text-red-400 bg-red-950/50 border border-red-800 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full h-10 rounded-lg bg-[var(--accent-teal)] text-white text-sm font-semibold hover:bg-[var(--accent-teal-hover)] transition-colors shadow-[0_0_20px_rgba(255,0,200,0.25)] disabled:opacity-50 mt-2"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-[var(--foreground-subtle)]">
            No workspace yet?{" "}
            <Link href="/onboarding" className="text-[var(--accent-teal)] hover:underline">
              Create one free
            </Link>
          </p>
        </div>

        {/* Bottom tagline */}
        <p
          className="mt-6 text-center text-[10px] text-[var(--foreground-subtle)] tracking-widest uppercase"
          style={{ fontFamily: "var(--font-orbitron)" }}
        >
          अक्षि · The Eye That Sees Systems
        </p>
      </motion.div>
    </div>
  );
}
