"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setAccessToken, isAuthenticated } from "@/lib/auth";

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
    <div className="min-h-screen flex bg-[var(--background)]">
      {/* Left panel — decorative */}
      <div className="hidden lg:flex flex-col justify-between w-[420px] shrink-0 border-r border-[var(--border)] bg-[var(--surface-1)] px-10 py-12">
        <div className="flex items-center gap-2.5">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
            <ellipse cx="11" cy="11" rx="10" ry="6.5" stroke="var(--accent-teal)" strokeWidth="1.4" />
            <circle cx="11" cy="11" r="3" fill="var(--accent-teal)" />
            <circle cx="11" cy="11" r="1.2" fill="var(--surface-1)" />
          </svg>
          <span className="text-sm font-semibold tracking-tight text-foreground">Akshi</span>
        </div>

        <div className="space-y-6">
          <p className="text-[10px] font-medium tracking-[0.25em] uppercase text-[var(--accent-teal)]">
            अक्षि · the eye that never closes
          </p>
          <blockquote className="text-lg font-medium leading-snug text-foreground max-w-[280px]">
            &ldquo;One dashboard for every service, every check, every second.&rdquo;
          </blockquote>
          <div className="flex flex-col gap-3 pt-2">
            {["Health checks every 30 s", "P99 incident alerts < 15 s", "SLO burn-rate tracking"].map((item) => (
              <div key={item} className="flex items-center gap-2 text-sm text-[var(--foreground-muted)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-teal)] shrink-0" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-[var(--foreground-subtle)]">
          © {new Date().getFullYear()} Akshi
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile brand */}
          <div className="flex items-center justify-center gap-2 mb-10 lg:hidden">
            <svg width="20" height="20" viewBox="0 0 22 22" fill="none" aria-hidden>
              <ellipse cx="11" cy="11" rx="10" ry="6.5" stroke="var(--accent-teal)" strokeWidth="1.4" />
              <circle cx="11" cy="11" r="3" fill="var(--accent-teal)" />
              <circle cx="11" cy="11" r="1.2" fill="var(--background)" />
            </svg>
            <span className="text-sm font-semibold tracking-tight">Akshi</span>
          </div>

          <h1 className="text-xl font-semibold mb-1">Welcome back</h1>
          <p className="text-sm text-[var(--foreground-muted)] mb-8">
            Sign in to your workspace
          </p>

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
                autoComplete="current-password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
              />
            </div>

            {error && (
              <p className="text-xs text-[var(--status-fail)] bg-[var(--status-fail-muted)] border border-[var(--status-fail)] rounded px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full h-9 rounded-md bg-[var(--accent-teal)] text-white text-sm font-medium transition-opacity hover:opacity-90 disabled:opacity-50"
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
      </div>
    </div>
  );
}
