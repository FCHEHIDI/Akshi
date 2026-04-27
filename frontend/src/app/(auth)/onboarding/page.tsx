"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";
import { CheckCircle2 } from "lucide-react";

type Step = "org" | "account" | "done";

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function StepDot({ current, step }: { current: Step; step: Step }) {
  const order: Step[] = ["org", "account", "done"];
  const currentIdx = order.indexOf(current);
  const stepIdx = order.indexOf(step);
  const done = stepIdx < currentIdx;
  const active = step === current;

  return (
    <div
      className={[
        "w-2 h-2 rounded-full transition-colors",
        active ? "bg-[var(--accent-teal)]" : done ? "bg-[var(--accent-teal-muted)]" : "bg-[var(--border)]",
      ].join(" ")}
    />
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("org");

  // Step 1 — org
  const [orgName, setOrgName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);

  // Step 2 — account
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
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
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
      // Auto-redirect after a moment
      setTimeout(() => router.push("/dashboard"), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-[var(--background)]">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-[380px] shrink-0 border-r border-[var(--border)] bg-[var(--surface-1)] px-10 py-12">
        <div className="flex items-center gap-2.5">
          <svg width="18" height="18" viewBox="0 0 22 22" fill="none" aria-hidden>
            <ellipse cx="11" cy="11" rx="10" ry="6.5" stroke="var(--accent-teal)" strokeWidth="1.4" />
            <circle cx="11" cy="11" r="3" fill="var(--accent-teal)" />
            <circle cx="11" cy="11" r="1.2" fill="var(--surface-1)" />
          </svg>
          <span className="text-sm font-semibold tracking-tight">Akshi</span>
        </div>

        <div className="space-y-5">
          <p className="text-[10px] font-medium tracking-[0.25em] uppercase text-[var(--accent-teal)]">
            Get started
          </p>
          <h2 className="text-lg font-semibold leading-snug max-w-[260px]">
            Your workspace is ready in under a minute
          </h2>
          <div className="space-y-3 pt-1">
            {[
              "Isolated schema — your data stays yours",
              "Invite your team at any time",
              "No credit card required",
            ].map((item) => (
              <div key={item} className="flex items-start gap-2 text-sm text-[var(--foreground-muted)]">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[var(--accent-teal)] shrink-0" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-[var(--foreground-subtle)]">
          Already have a workspace?{" "}
          <Link href="/login" className="text-[var(--accent-teal)] hover:underline">
            Sign in
          </Link>
        </p>
      </div>

      {/* Right panel */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Step dots */}
          <div className="flex items-center gap-1.5 mb-8">
            <StepDot current={step} step="org" />
            <StepDot current={step} step="account" />
            <StepDot current={step} step="done" />
          </div>

          {/* ── Step 1: Organisation ── */}
          {step === "org" && (
            <>
              <h1 className="text-xl font-semibold mb-1">Name your workspace</h1>
              <p className="text-sm text-[var(--foreground-muted)] mb-8">
                This is how your organisation will appear in Akshi.
              </p>

              <form onSubmit={handleOrgNext} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--foreground-muted)]" htmlFor="org-name">
                    Organisation name
                  </label>
                  <input
                    id="org-name"
                    type="text"
                    required
                    placeholder="Acme Inc."
                    value={orgName}
                    onChange={(e) => {
                      setOrgName(e.target.value);
                      if (!slugEdited) setSlug(slugify(e.target.value));
                    }}
                    className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--foreground-muted)]" htmlFor="slug">
                    Workspace URL slug
                  </label>
                  <div className="flex items-center h-9 rounded-md border border-border bg-[var(--surface-2)] overflow-hidden focus-within:ring-1 focus-within:ring-[var(--accent-teal)]">
                    <span className="pl-3 pr-1 text-xs text-[var(--foreground-subtle)] shrink-0">
                      akshi.io/
                    </span>
                    <input
                      id="slug"
                      type="text"
                      required
                      pattern="[a-z0-9-]+"
                      title="Lowercase letters, numbers and hyphens only"
                      placeholder="acme"
                      value={slug}
                      onChange={(e) => {
                        setSlugEdited(true);
                        setSlug(slugify(e.target.value));
                      }}
                      className="flex-1 h-full bg-transparent pr-3 text-sm text-foreground focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full h-9 rounded-md bg-[var(--accent-teal)] text-white text-sm font-medium hover:bg-[var(--accent-teal-hover)] transition-colors mt-2"
                >
                  Continue
                </button>
              </form>
            </>
          )}

          {/* ── Step 2: Admin account ── */}
          {step === "account" && (
            <>
              <h1 className="text-xl font-semibold mb-1">Create your admin account</h1>
              <p className="text-sm text-[var(--foreground-muted)] mb-8">
                You&apos;ll be the first admin of <span className="text-foreground font-medium">{orgName}</span>.
              </p>

              <form onSubmit={handleAccountSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--foreground-muted)]" htmlFor="full-name">
                    Full name
                  </label>
                  <input
                    id="full-name"
                    type="text"
                    required
                    placeholder="Ada Lovelace"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--foreground-muted)]" htmlFor="email">
                    Work email
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    placeholder="ada@acme.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--foreground-muted)]" htmlFor="password">
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    required
                    minLength={8}
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--foreground-muted)]" htmlFor="confirm">
                    Confirm password
                  </label>
                  <input
                    id="confirm"
                    type="password"
                    required
                    placeholder="Repeat password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
                  />
                </div>

                {error && (
                  <p className="text-xs text-[var(--status-fail)] bg-[var(--status-fail-muted)] border border-[var(--status-fail)] rounded px-3 py-2">
                    {error}
                  </p>
                )}

                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setStep("org")}
                    className="flex-1 h-9 rounded-md border border-border bg-transparent text-sm text-[var(--foreground-muted)] hover:text-foreground hover:border-[var(--foreground-subtle)] transition-colors"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 h-9 rounded-md bg-[var(--accent-teal)] text-white text-sm font-medium hover:bg-[var(--accent-teal-hover)] transition-colors disabled:opacity-50"
                  >
                    {loading ? "Creating…" : "Create workspace"}
                  </button>
                </div>
              </form>
            </>
          )}

          {/* ── Step 3: Done ── */}
          {step === "done" && (
            <div className="flex flex-col items-center text-center gap-4 py-8">
              <div className="w-12 h-12 rounded-full bg-[var(--status-ok-muted)] flex items-center justify-center">
                <CheckCircle2 size={22} className="text-[var(--status-ok)]" strokeWidth={1.5} />
              </div>
              <h1 className="text-xl font-semibold">Workspace created!</h1>
              <p className="text-sm text-[var(--foreground-muted)]">
                Taking you to your dashboard…
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
