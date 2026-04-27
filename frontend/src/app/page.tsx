"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Eye, Siren, BarChart3, Bot, Lock, Sparkles } from "lucide-react";

/* ── Animation variants ─────────────────────────── */
const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" as const, delay: i * 0.1 },
  }),
};

/* ── Sub-components ─────────────────────────────── */
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
      className={"pointer-events-none select-none " + (className ?? "")}
      fill="none"
    >
      {[80, 160, 240, 320, 400, 480].map((r) => (
        <circle
          key={r}
          cx="300"
          cy="300"
          r={r}
          stroke="#FF00C8"
          strokeWidth="0.5"
          opacity={0.06 + (480 - r) * 0.0003}
        />
      ))}
    </svg>
  );
}

function FeatureCard({
  icon,
  title,
  body,
  delay = 0,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
  delay?: number;
}) {
  return (
    <motion.div
      variants={fadeUp}
      custom={delay}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true }}
      className="group relative rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6 flex flex-col gap-3 hover:border-[var(--accent-teal)] transition-all duration-300 overflow-hidden"
    >
      <div className="absolute -top-10 -left-10 w-32 h-32 rounded-full bg-[var(--accent-teal)] opacity-0 group-hover:opacity-[0.07] blur-2xl transition-opacity duration-500" />
      <span className="relative w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--accent-teal-muted)] text-[var(--accent-teal)]">
        {icon}
      </span>
      <h3 className="relative text-sm font-semibold text-foreground">{title}</h3>
      <p className="relative text-sm text-[var(--foreground-muted)] leading-relaxed">{body}</p>
    </motion.div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--background)] text-foreground overflow-x-hidden">
      <CosmicGrain />

      {/* Radial violet glow */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          background: "radial-gradient(ellipse 80% 60% at 50% -10%, #3B006A 0%, transparent 70%)",
          opacity: 0.6,
        }}
      />

      {/* Nav */}
      <header className="relative z-30 sticky top-0 border-b border-[var(--border-muted)] bg-[var(--background)]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-3">
            <Image src="/logo_principal.png" alt="Akshi" width={180} height={56} className="h-14 w-auto" priority />
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-[var(--foreground-muted)] hover:text-foreground transition-colors">
              Sign in
            </Link>
            <Link href="/onboarding" className="rounded-md bg-[var(--accent-teal)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-teal-hover)] transition-colors shadow-[0_0_20px_rgba(255,0,200,0.3)]">
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pt-32 pb-28 text-center">
        <ConcentricWaves className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] opacity-60" />
        <div aria-hidden className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-80 w-[700px] rounded-full blur-[100px] opacity-25" style={{ background: "var(--accent-teal)" }} />

        <motion.div variants={fadeUp} custom={0} initial="hidden" animate="show">
          <span className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-1)] px-4 py-1.5 text-[11px] font-medium uppercase tracking-[0.2em] text-[var(--accent-teal)]" style={{ fontFamily: "var(--font-orbitron)" }}>
            अक्षि · The Eye That Sees Systems
          </span>
        </motion.div>

        <motion.h1 variants={fadeUp} custom={1} initial="hidden" animate="show" className="mt-8 text-5xl font-bold leading-tight tracking-tight sm:text-6xl lg:text-7xl">
          Observability
          <br />
          <span className="text-[var(--accent-teal)]" style={{ textShadow: "0 0 40px rgba(255,0,200,0.4)" }}>
            Beyond Vision
          </span>
        </motion.h1>

        <motion.p variants={fadeUp} custom={2} initial="hidden" animate="show" className="mx-auto mt-7 max-w-xl text-base text-[var(--foreground-muted)] leading-relaxed">
          Akshi gives engineering teams a single pane of glass for health checks, incident management, SLO tracking, and runbook automation — all multi-tenant, all real-time.
        </motion.p>

        <motion.div variants={fadeUp} custom={3} initial="hidden" animate="show" className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/onboarding" className="rounded-md bg-[var(--accent-teal)] px-7 py-3 text-sm font-semibold text-white hover:bg-[var(--accent-teal-hover)] transition-colors shadow-[0_0_30px_rgba(255,0,200,0.35)]">
            Create your workspace
          </Link>
          <Link href="/login" className="rounded-md border border-[var(--border)] bg-[var(--surface-1)] px-7 py-3 text-sm font-medium text-[var(--foreground-muted)] hover:text-foreground hover:border-[var(--accent-teal)] transition-all">
            Sign in →
          </Link>
        </motion.div>

        <motion.div variants={fadeUp} custom={4} initial="hidden" animate="show" className="mt-16 flex flex-wrap justify-center gap-10 text-sm">
          {[
            { label: "Uptime checks", value: "Every 30 s" },
            { label: "Incident P99 alert", value: "< 15 s" },
            { label: "SLO tracking", value: "99.99 %" },
          ].map(({ label, value }) => (
            <div key={label} className="flex flex-col items-center gap-1">
              <span className="text-2xl font-bold tabular-nums" style={{ color: "var(--silver)", fontFamily: "var(--font-orbitron)" }}>{value}</span>
              <span className="text-xs text-[var(--foreground-subtle)] uppercase tracking-widest">{label}</span>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-28">
        <motion.h2 variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="text-[10px] font-medium uppercase tracking-[0.3em] text-[var(--foreground-subtle)] mb-10 text-center" style={{ fontFamily: "var(--font-orbitron)" }}>
          Built for on-call teams
        </motion.h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <FeatureCard delay={0} icon={<Eye size={18} />} title="Health Checks" body="HTTP, TCP, ping, and cron monitors running on distributed agents. Configurable retry logic, custom headers, and TLS inspection." />
          <FeatureCard delay={1} icon={<Siren size={18} />} title="Incident Management" body="Auto-open incidents on threshold breach. Severity triage, acknowledgement workflows, and resolution timelines — all in one view." />
          <FeatureCard delay={2} icon={<BarChart3 size={18} />} title="SLO Tracking" body="Define error budgets per service. Burn-rate alerts warn your team before the budget is exhausted — not after." />
          <FeatureCard delay={3} icon={<Bot size={18} />} title="Runbook Automation" body="Trigger automated remediation scripts on incident creation. Integrate with your existing toolchain via webhooks and plugins." />
          <FeatureCard delay={4} icon={<Lock size={18} />} title="Multi-Tenant" body="Isolated PostgreSQL schemas per organisation. Invite team members with role-based access — admin, operator, or read-only." />
          <FeatureCard delay={5} icon={<Sparkles size={18} />} title="AI Co-pilot" body="Ask Akshi AI why an incident fired, what changed, and what to do next. Grounded in your telemetry, not generic guesses." />
        </div>
      </section>

      {/* How it works */}
      <section className="relative z-10 border-t border-[var(--border)] overflow-hidden">
        <div className="absolute inset-0 bg-[var(--surface-1)]" />
        <div aria-hidden className="pointer-events-none absolute right-0 top-0 h-full w-1/2 opacity-10" style={{ background: "radial-gradient(ellipse at right center, #FF00C8 0%, transparent 70%)" }} />
        <div className="relative z-10 mx-auto max-w-6xl px-6 py-28">
          <motion.h2 variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="text-[10px] font-medium uppercase tracking-[0.3em] text-[var(--foreground-subtle)] mb-14 text-center" style={{ fontFamily: "var(--font-orbitron)" }}>
            The Constellation Method
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
            {[
              { step: "01", title: "Connect your services", body: "Register HTTP endpoints, TCP ports, or cron jobs. Akshi agents probe them from multiple regions." },
              { step: "02", title: "Define your SLOs", body: "Set availability, latency, and error-rate targets. Akshi calculates your error budget in real time." },
              { step: "03", title: "Respond with context", body: "Alerts arrive with full trace context. The AI drawer surfaces root cause and recommended runbook." },
            ].map(({ step, title, body }, i) => (
              <motion.div key={step} variants={fadeUp} custom={i} initial="hidden" whileInView="show" viewport={{ once: true }} className="flex flex-col items-center gap-4">
                <span className="text-4xl font-black tabular-nums" style={{ color: "var(--accent-teal)", fontFamily: "var(--font-orbitron)", textShadow: "0 0 20px rgba(255,0,200,0.3)" }}>{step}</span>
                <h3 className="text-base font-semibold">{title}</h3>
                <p className="text-sm text-[var(--foreground-muted)] leading-relaxed max-w-xs">{body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-28 text-center">
        <ConcentricWaves className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] opacity-40" />
        <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="relative z-10">
          <h2 className="text-3xl font-bold tracking-tight">
            Ready to see every service <span className="text-[var(--accent-teal)]">at a glance?</span>
          </h2>
          <p className="mt-4 text-sm text-[var(--foreground-muted)]">Create your workspace in under a minute. No credit card required.</p>
          <Link href="/onboarding" className="mt-9 inline-flex rounded-md bg-[var(--accent-teal)] px-9 py-3.5 text-sm font-semibold text-white hover:bg-[var(--accent-teal-hover)] transition-colors shadow-[0_0_40px_rgba(255,0,200,0.35)]">
            Start for free
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-[var(--border)] py-8">
        <div className="mx-auto max-w-6xl px-6 flex items-center justify-between text-xs text-[var(--foreground-subtle)]">
          <span>© {new Date().getFullYear()} Akshi · अक्षि</span>
          <div className="flex gap-6">
            <Link href="/login" className="hover:text-foreground transition-colors">Sign in</Link>
            <Link href="/onboarding" className="hover:text-foreground transition-colors">Get started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
