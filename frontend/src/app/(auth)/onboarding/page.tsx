"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";
import { CheckCircle2 } from "lucide-react";

type Step = "org" | "account" | "done";

function slugify(value: string): string {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

const stepIdx = (s: Step) => (["org", "account", "done"] as Step[]).indexOf(s);

const slideVariants = {
  enter: { opacity: 0, x: 20 },
  center: { opacity: 1, x: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2 } },
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

const inputCls =
  "w-full h-10 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)] focus:border-[var(--accent-teal)] transition-colors";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("org");

  const [orgName, setOrgName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleOrgNext(e: React.FormEvent) {
    e.preventDefault();
    if (!orgName.trim() || !slug.trim()) return;
    setStep("account");
  }

  async function handleAccountSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { setError("Passwords do not match"); return; }
    setLoading(true);
    setError(null);
    try {
      const data = await api.onboarding.createOrg({
        org_name: orgName.trim(),
        slug: slug.trim(),
        full_name: fullName.trim(),
        email: email.trim(),
        password,
      });
      setAccessToken(data.access_token);
      setStep("done");
      setTimeout(() => router.push("/dashboard"), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const current = stepIdx(step);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] overflow-hidden relative px-6 py-12">
      <CosmicGrain />

      {/* Radial violet glow */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0"
        style={{ background: "radial-gradient(ellipse 80% 60% at 50% -10%, #3B006A 0%, transparent 70%)", opacity: 0.6 }}
      />

      {/* Concentric waves */}
      <svg aria-hidden viewBox="0 0 600 600" className="pointer-events-none select-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] opacity-30 z-0" fill="none">
        {[80, 160, 240, 320, 400, 480].map((r) => (
          <circle key={r} cx="300" cy="300" r={r} stroke="#FF00C8" strokeWidth="0.5" opacity={0.05 + (480 - r) * 0.0003} />
        ))}
      </svg>

      {/* Magenta smoke glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full blur-[120px] z-0"
        style={{ background: "var(--accent-teal)", opacity: 0.06 }}
      />

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" } }}
        className="relative z-10 w-full max-w-sm"
      >
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)]/90 backdrop-blur-md px-8 py-10 shadow-[0_0_60px_rgba(59,0,106,0.4)]">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <Link href="/">
              <Image src="/logo_principal.png" alt="Akshi" width={200} height={62} className="h-16 w-auto" priority />
            </Link>
          </div>

          {/* Step progress */}
          <div className="flex items-center gap-2 mb-8">
            {(["org", "account", "done"] as Step[]).map((s, i) => (
              <div key={s} className="flex items-center gap-2 flex-1">
                <div
                  className="w-2 h-2 rounded-full transition-all duration-300"
                  style={{
                    background: i < current ? "var(--accent-teal-muted)" : i === current ? "var(--accent-teal)" : "var(--border)",
                    boxShadow: i === current ? "0 0 8px rgba(255,0,200,0.5)" : "none",
                  }}
                />
                {i < 2 && <div className="flex-1 h-px" style={{ background: i < current ? "var(--accent-teal-muted)" : "var(--border)" }} />}
              </div>
            ))}
          </div>

          {/* Step content */}
          <AnimatePresence mode="wait">
            {step === "org" && (
              <motion.div key="org" variants={slideVariants} initial="enter" animate="center" exit="exit">
                <h1 className="text-lg font-semibold mb-1">Name your workspace</h1>
                <p className="text-sm text-[var(--foreground-muted)] mb-6">
                  This is how your organisation will appear in Akshi.
                </p>
                <form onSubmit={handleOrgNext} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs text-[var(--foreground-muted)]" htmlFor="org-name">Organisation name</label>
                    <input
                      id="org-name" type="text" required placeholder="Acme Inc."
                      value={orgName}
                      onChange={(e) => {
                        setOrgName(e.target.value);
                        if (!slugEdited) setSlug(slugify(e.target.value));
                      }}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-[var(--foreground-muted)]" htmlFor="slug">Workspace URL slug</label>
                    <div className="flex items-center h-10 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] overflow-hidden focus-within:ring-1 focus-within:ring-[var(--accent-teal)] focus-within:border-[var(--accent-teal)] transition-colors">
                      <span className="pl-3 pr-1 text-xs text-[var(--foreground-subtle)] shrink-0">akshi.io/</span>
                      <input
                        id="slug" type="text" required pattern="[a-z0-9\-]+" title="Lowercase letters, numbers and hyphens only"
                        placeholder="acme" value={slug}
                        onChange={(e) => { setSlugEdited(true); setSlug(slugify(e.target.value)); }}
                        className="flex-1 h-full bg-transparent pr-3 text-sm text-foreground focus:outline-none"
                      />
                    </div>
                  </div>
                  <button type="submit" className="w-full h-10 rounded-lg bg-[var(--accent-teal)] text-white text-sm font-semibold hover:bg-[var(--accent-teal-hover)] transition-colors shadow-[0_0_20px_rgba(255,0,200,0.25)] mt-2">
                    Continue →
                  </button>
                </form>
              </motion.div>
            )}

            {step === "account" && (
              <motion.div key="account" variants={slideVariants} initial="enter" animate="center" exit="exit">
                <h1 className="text-lg font-semibold mb-1">Create your admin account</h1>
                <p className="text-sm text-[var(--foreground-muted)] mb-6">
                  First admin of <span className="text-foreground font-medium">{orgName}</span>.
                </p>
                <form onSubmit={handleAccountSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs text-[var(--foreground-muted)]" htmlFor="full-name">Full name</label>
                    <input id="full-name" type="text" required placeholder="Ada Lovelace" value={fullName} onChange={(e) => setFullName(e.target.value)} className={inputCls} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-[var(--foreground-muted)]" htmlFor="email">Work email</label>
                    <input id="email" type="email" required placeholder="ada@acme.com" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-[var(--foreground-muted)]" htmlFor="password">Password</label>
                    <input id="password" type="password" required minLength={8} placeholder="At least 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} className={inputCls} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-[var(--foreground-muted)]" htmlFor="confirm">Confirm password</label>
                    <input id="confirm" type="password" required placeholder="Repeat password" value={confirm} onChange={(e) => setConfirm(e.target.value)} className={inputCls} />
                  </div>
                  {error && (
                    <p className="text-xs text-red-400 bg-red-950/50 border border-red-800 rounded-lg px-3 py-2">{error}</p>
                  )}
                  <div className="flex gap-2 pt-1">
                    <button type="button" onClick={() => setStep("org")} className="flex-1 h-10 rounded-lg border border-[var(--border)] bg-transparent text-sm text-[var(--foreground-muted)] hover:text-foreground hover:border-[var(--foreground-subtle)] transition-colors">
                      Back
                    </button>
                    <button type="submit" disabled={loading} className="flex-1 h-10 rounded-lg bg-[var(--accent-teal)] text-white text-sm font-semibold hover:bg-[var(--accent-teal-hover)] transition-colors shadow-[0_0_20px_rgba(255,0,200,0.25)] disabled:opacity-50">
                      {loading ? "Creating…" : "Create workspace"}
                    </button>
                  </div>
                </form>
              </motion.div>
            )}

            {step === "done" && (
              <motion.div key="done" variants={slideVariants} initial="enter" animate="center" exit="exit" className="flex flex-col items-center text-center gap-4 py-6">
                <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: "var(--accent-teal-muted)", boxShadow: "0 0 30px rgba(255,0,200,0.2)" }}>
                  <CheckCircle2 size={26} className="text-[var(--accent-teal)]" strokeWidth={1.5} />
                </div>
                <h1 className="text-xl font-semibold">Workspace created!</h1>
                <p className="text-sm text-[var(--foreground-muted)]">Taking you to your dashboard…</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <p className="mt-6 text-center text-xs text-[var(--foreground-subtle)]">
          Already have a workspace?{" "}
          <Link href="/login" className="text-[var(--accent-teal)] hover:underline">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
}
