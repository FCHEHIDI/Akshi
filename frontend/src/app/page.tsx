import Link from "next/link";

function FeatureCard({ icon, title, body }: { icon: string; title: string; body: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6 flex flex-col gap-3 hover:border-[var(--accent-teal-muted)] transition-colors">
      <span className="text-2xl">{icon}</span>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <p className="text-sm text-[var(--foreground-muted)] leading-relaxed">{body}</p>
    </div>
  );
}

function PillBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--accent-teal-muted)] bg-[var(--accent-teal-muted)]/30 px-3 py-1 text-[11px] font-medium text-[var(--accent-teal)] uppercase tracking-widest">
      {children}
    </span>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--background)] text-foreground">
      {/* ── Noise overlay ── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
          backgroundSize: "256px 256px",
        }}
      />

      {/* ── Top nav ── */}
      <header className="sticky top-0 z-30 border-b border-[var(--border-muted)] bg-[var(--background)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2.5">
            {/* Eye glyph */}
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
              <ellipse cx="11" cy="11" rx="10" ry="6.5" stroke="var(--accent-teal)" strokeWidth="1.4" />
              <circle cx="11" cy="11" r="3" fill="var(--accent-teal)" />
              <circle cx="11" cy="11" r="1.2" fill="var(--background)" />
            </svg>
            <span className="text-sm font-semibold tracking-tight">Akshi</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-[var(--foreground-muted)] hover:text-foreground transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/onboarding"
              className="rounded-md bg-[var(--accent-teal)] px-4 py-1.5 text-sm font-medium text-white hover:bg-[var(--accent-teal-hover)] transition-colors"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative mx-auto max-w-6xl px-6 pt-28 pb-24 text-center">
        {/* Glow behind hero */}
        <div
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-72 w-[600px] rounded-full blur-3xl opacity-20"
          style={{ background: "var(--accent-teal)" }}
        />

        <PillBadge>अक्षि · the eye that never closes</PillBadge>

        <h1 className="mt-6 text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
          Infrastructure observability
          <br />
          <span className="text-[var(--accent-teal)]">without the noise</span>
        </h1>

        <p className="mx-auto mt-6 max-w-xl text-base text-[var(--foreground-muted)] leading-relaxed">
          Akshi gives engineering teams a single pane of glass for health checks, incident
          management, SLO tracking, and runbook automation — all multi-tenant, all real-time.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/onboarding"
            className="rounded-md bg-[var(--accent-teal)] px-6 py-2.5 text-sm font-semibold text-white hover:bg-[var(--accent-teal-hover)] transition-colors"
          >
            Create your workspace
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-[var(--border)] bg-[var(--surface-1)] px-6 py-2.5 text-sm font-medium text-[var(--foreground-muted)] hover:text-foreground hover:border-[var(--foreground-subtle)] transition-colors"
          >
            Sign in
          </Link>
        </div>

        {/* Stat pills */}
        <div className="mt-14 flex flex-wrap justify-center gap-6 text-sm">
          {[
            { label: "Uptime checks", value: "Every 30 s" },
            { label: "Incident P99 alert", value: "< 15 s" },
            { label: "SLO tracking", value: "99.99 %" },
          ].map(({ label, value }) => (
            <div key={label} className="flex flex-col items-center gap-0.5">
              <span className="text-xl font-semibold tabular-nums text-foreground">{value}</span>
              <span className="text-xs text-[var(--foreground-subtle)]">{label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Feature grid ── */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="text-xs font-medium uppercase tracking-widest text-[var(--foreground-subtle)] mb-8 text-center">
          Built for on-call teams
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <FeatureCard
            icon="👁"
            title="Health Checks"
            body="HTTP, TCP, ping, and cron monitors running on distributed agents. Configurable retry logic, custom headers, and TLS inspection."
          />
          <FeatureCard
            icon="🚨"
            title="Incident Management"
            body="Auto-open incidents on threshold breach. Severity triage, acknowledgement workflows, and resolution timelines — all in one view."
          />
          <FeatureCard
            icon="📊"
            title="SLO Tracking"
            body="Define error budgets per service. Burn-rate alerts warn your team before the budget is exhausted — not after."
          />
          <FeatureCard
            icon="🤖"
            title="Runbook Automation"
            body="Trigger automated remediation scripts on incident creation. Integrate with your existing toolchain via webhooks and plugins."
          />
          <FeatureCard
            icon="🔐"
            title="Multi-Tenant"
            body="Isolated PostgreSQL schemas per organisation. Invite team members with role-based access — admin, operator, or read-only."
          />
          <FeatureCard
            icon="✨"
            title="AI Co-pilot"
            body="Ask Akshi AI why an incident fired, what changed, and what to do next. Grounded in your telemetry, not generic guesses."
          />
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="border-t border-[var(--border)] bg-[var(--surface-1)]">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <h2 className="text-xs font-medium uppercase tracking-widest text-[var(--foreground-subtle)] mb-12 text-center">
            The Backend Constellation Method
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {[
              {
                step: "01",
                title: "Connect your services",
                body: "Register HTTP endpoints, TCP ports, or cron jobs. Akshi agents probe them from multiple regions.",
              },
              {
                step: "02",
                title: "Define your SLOs",
                body: "Set availability, latency, and error-rate targets. Akshi calculates your error budget in real time.",
              },
              {
                step: "03",
                title: "Respond with context",
                body: "Alerts arrive with full trace context. The AI drawer surfaces root cause and recommended runbook.",
              },
            ].map(({ step, title, body }) => (
              <div key={step} className="flex flex-col items-center gap-3">
                <span className="text-3xl font-bold tabular-nums text-[var(--accent-teal)] opacity-50">
                  {step}
                </span>
                <h3 className="text-sm font-semibold">{title}</h3>
                <p className="text-sm text-[var(--foreground-muted)] leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="mx-auto max-w-6xl px-6 py-24 text-center">
        <h2 className="text-2xl font-bold tracking-tight">
          Ready to see every service at a glance?
        </h2>
        <p className="mt-3 text-sm text-[var(--foreground-muted)]">
          Create your workspace in under a minute. No credit card required.
        </p>
        <Link
          href="/onboarding"
          className="mt-8 inline-flex rounded-md bg-[var(--accent-teal)] px-8 py-3 text-sm font-semibold text-white hover:bg-[var(--accent-teal-hover)] transition-colors"
        >
          Start for free
        </Link>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[var(--border)] py-8">
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


