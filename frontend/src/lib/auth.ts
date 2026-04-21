/**
 * Lightweight auth token helpers.
 * Tokens are stored in localStorage under well-known keys.
 * All functions are no-ops during SSR (typeof window check).
 */

const ACCESS_KEY = "sentinel_access";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}
