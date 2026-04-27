"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";
import { CheckCircle2, AlertTriangle } from "lucide-react";

interface Peek {
  email: string;
  org_name: string;
  role: string;
}

export default function InviteAcceptPage() {
  const params = useParams();
  const router = useRouter();
  const token = typeof params?.token === "string" ? params.token : "";

  const [peek, setPeek] = useState<Peek | null>(null);
  const [peekError, setPeekError] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.invitations.peek(token)
      .then(setPeek)
      .catch(() => setPeekError("This invitation link is invalid or has expired."));
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.invitations.accept(token, password, fullName.trim());
      setAccessToken(data.access_token);
      setDone(true);
      setTimeout(() => router.push("/dashboard"), 1800);
    } catch (err) {
      setError(err instanceof Error && !err.message.includes("<") ? err.message : "Failed to accept invitation. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] px-4 py-12">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="flex items-center justify-center gap-2 mb-10">
          <svg width="20" height="20" viewBox="0 0 22 22" fill="none" aria-hidden>
            <ellipse cx="11" cy="11" rx="10" ry="6.5" stroke="var(--accent-teal)" strokeWidth="1.4" />
            <circle cx="11" cy="11" r="3" fill="var(--accent-teal)" />
            <circle cx="11" cy="11" r="1.2" fill="var(--background)" />
          </svg>
          <span className="text-sm font-semibold tracking-tight">Akshi</span>
        </div>

        {/* Peek error state */}
        {peekError && (
          <div className="flex flex-col items-center gap-4 text-center py-6">
            <div className="w-12 h-12 rounded-full bg-[var(--status-fail-muted)] flex items-center justify-center">
              <AlertTriangle size={22} className="text-[var(--status-fail)]" strokeWidth={1.5} />
            </div>
            <h1 className="text-lg font-semibold">Invitation not valid</h1>
            <p className="text-sm text-[var(--foreground-muted)]">{peekError}</p>
            <Link
              href="/login"
              className="text-sm text-[var(--accent-teal)] hover:underline"
            >
              Back to sign in
            </Link>
          </div>
        )}

        {/* Loading peek */}
        {!peek && !peekError && (
          <div className="flex flex-col items-center gap-3 py-10 text-sm text-[var(--foreground-muted)]">
            <div className="w-5 h-5 rounded-full border-2 border-[var(--accent-teal)] border-t-transparent animate-spin" />
            Verifying invitation…
          </div>
        )}

        {/* Done */}
        {done && (
          <div className="flex flex-col items-center text-center gap-4 py-8">
            <div className="w-12 h-12 rounded-full bg-[var(--status-ok-muted)] flex items-center justify-center">
              <CheckCircle2 size={22} className="text-[var(--status-ok)]" strokeWidth={1.5} />
            </div>
            <h1 className="text-xl font-semibold">You&apos;re in!</h1>
            <p className="text-sm text-[var(--foreground-muted)]">
              Taking you to <span className="text-foreground font-medium">{peek?.org_name}</span>…
            </p>
          </div>
        )}

        {/* Form */}
        {peek && !done && (
          <>
            <div className="mb-8 space-y-1">
              <h1 className="text-xl font-semibold">Accept invitation</h1>
              <p className="text-sm text-[var(--foreground-muted)]">
                You were invited to join{" "}
                <span className="text-foreground font-medium">{peek.org_name}</span> as{" "}
                <span className="capitalize text-[var(--accent-teal)]">{peek.role}</span>.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs text-[var(--foreground-muted)]" htmlFor="email-display">
                  Email
                </label>
                <input
                  id="email-display"
                  type="email"
                  readOnly
                  value={peek.email}
                  className="w-full h-9 rounded-md border border-border bg-[var(--surface-3)] px-3 text-sm text-[var(--foreground-muted)] cursor-not-allowed"
                />
              </div>

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
                <label className="text-xs text-[var(--foreground-muted)]" htmlFor="password">
                  Set password
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

              <button
                type="submit"
                disabled={loading}
                className="w-full h-9 rounded-md bg-[var(--accent-teal)] text-white text-sm font-medium hover:bg-[var(--accent-teal-hover)] transition-colors disabled:opacity-50 mt-2"
              >
                {loading ? "Joining…" : "Join workspace"}
              </button>
            </form>

            <p className="mt-6 text-center text-xs text-[var(--foreground-subtle)]">
              Already have an account?{" "}
              <Link href="/login" className="text-[var(--accent-teal)] hover:underline">
                Sign in
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
