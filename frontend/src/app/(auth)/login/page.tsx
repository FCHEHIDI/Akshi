"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { setAccessToken, isAuthenticated } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@sentinelops.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Already logged in → skip to dashboard
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
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] px-4">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="mb-8 text-center space-y-1">
          <p className="text-[10px] font-medium tracking-[0.2em] uppercase text-[var(--foreground-subtle)]">
            SentinelOps
          </p>
          <h1 className="text-xl font-semibold text-foreground">Sign in to your workspace</h1>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[var(--surface-1)] border border-border rounded-lg p-6 space-y-4"
        >
          <div className="space-y-1.5">
            <label className="text-xs text-[var(--foreground-muted)]" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
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

        <p className="mt-4 text-center text-[10px] text-[var(--foreground-subtle)]">
          Dev credentials: admin@sentinelops.local / dev1234!
        </p>
      </div>
    </div>
  );
}
