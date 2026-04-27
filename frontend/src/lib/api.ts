import { getAccessToken, clearTokens } from "./auth";

const BASE = "/api";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
    ...init,
  });
  if (res.status === 401) {
    clearTokens();
    if (typeof window !== "undefined") window.location.replace("/login");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

/* ── Types ─────────────────────────────────────────────────── */

export interface Service {
  id: string;
  name: string;
  description: string;
  tags: string[];
  status: "active" | "paused" | "archived";
  sla_target: string | null;
  checks_count: number;
  open_incidents_count: number;
  created_at: string;
  updated_at: string;
}

export interface Check {
  id: string;
  service_id: string;
  service_name: string;
  name: string;
  check_type: "http" | "tcp" | "ping" | "cron";
  config: Record<string, unknown>;
  target: string;
  interval_seconds: number;
  retry_count: number;
  is_enabled: boolean;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CheckResult {
  id: string;
  health_check: string;
  health_check_name: string;
  service_id: string;
  status: "ok" | "fail" | "timeout" | "unknown";
  duration_ms: number;
  response_code: number | null;
  error_message: string;
  checked_via: string;
  created_at: string;
}

export interface Incident {
  id: string;
  service_id: string;
  service_name: string;
  health_check_name: string | null;
  check_type: string | null;
  state: "open" | "acknowledged" | "resolved";
  severity: "low" | "medium" | "high" | "critical";
  opened_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  ack_note: string;
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: "admin" | "operator" | "viewer";
  joined_at: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: Member["role"];
  status: "pending" | "accepted" | "expired" | "cancelled";
  invited_by: string;
  created_at: string;
  expires_at: string;
}

/* ── Paginated wrapper ─────────────────────────────────────── */

interface Paginated<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}

async function apiFetchList<T>(path: string): Promise<T[]> {
  const data = await apiFetch<Paginated<T> | T[]>(path);
  if (Array.isArray(data)) return data;
  return data.results;
}

/* ── API calls ──────────────────────────────────────────────── */

export const api = {
  services: {
    list: () => apiFetchList<Service>("/v1/services"),
  },
  checks: {
    list: () => apiFetchList<Check>("/v1/checks"),
  },
  results: {
    recent: (limit = 50) =>
      apiFetchList<CheckResult>(`/v1/results/recent?limit=${limit}`),
  },
  incidents: {
    list: (state?: string) =>
      apiFetchList<Incident>(
        `/v1/incidents${state ? `?state=${state}` : ""}`
      ),
    acknowledge: (id: string, note?: string) =>
      apiFetch(`/v1/incidents/${id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ ack_note: note ?? "" }),
      }),
    resolve: (id: string) =>
      apiFetch(`/v1/incidents/${id}/resolve`, { method: "POST" }),
  },
  team: {
    members: () => apiFetchList<Member>("/v1/team/members"),
    invitations: () => apiFetchList<Invitation>("/v1/team/invitations"),
    invite: (email: string, role: Member["role"]) =>
      apiFetch<Invitation>("/v1/team/invitations", {
        method: "POST",
        body: JSON.stringify({ email, role }),
      }),
    cancelInvitation: (id: string) =>
      apiFetch(`/v1/team/invitations/${id}`, { method: "DELETE" }),
    removeMember: (id: string) =>
      apiFetch(`/v1/team/members/${id}`, { method: "DELETE" }),
  },
  invitations: {
    /** Public — accepts by token, returns JWT */
    accept: (token: string, password: string, fullName: string) =>
      apiFetch<{ access_token: string }>("/v1/invitations/accept", {
        method: "POST",
        body: JSON.stringify({ token, password, full_name: fullName }),
      }),
    peek: (token: string) =>
      apiFetch<{ email: string; org_name: string; role: string }>(
        `/v1/invitations/${token}/peek`
      ),
  },
  onboarding: {
    createOrg: (payload: { org_name: string; slug: string; full_name: string; email: string; password: string }) =>
      apiFetch<{ access_token: string }>("/v1/onboarding/create-org", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
} as const;


