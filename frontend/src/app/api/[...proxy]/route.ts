/**
 * Next.js catch-all proxy route.
 *
 * Forwards all /api/* requests to the Django backend while preserving the
 * original browser Host header as X-Forwarded-Host so that django-tenants
 * can resolve the correct tenant schema.
 */
import { type NextRequest, NextResponse } from "next/server";

const BACKEND = "http://127.0.0.1:8000";

async function proxy(request: NextRequest): Promise<NextResponse> {
  const { pathname, search } = request.nextUrl;
  const backendUrl = `${BACKEND}${pathname}${search}`;

  const headers = new Headers();
  // Forward auth and content-type headers
  for (const [key, value] of request.headers.entries()) {
    const lower = key.toLowerCase();
    if (
      lower === "authorization" ||
      lower === "content-type" ||
      lower === "accept" ||
      lower === "cookie"
    ) {
      headers.set(key, value);
    }
  }

  // Pass original browser host (without port) so django-tenants resolves the right tenant
  const rawHost = request.headers.get("host") ?? "";
  const originalHost = rawHost.split(":")[0]; // strip port — domain table has no port
  headers.set("x-forwarded-host", originalHost);

  let body: string | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.text();
  }

  const upstream = await fetch(backendUrl, {
    method: request.method,
    headers,
    body,
  });

  const responseHeaders = new Headers();
  for (const [key, value] of upstream.headers.entries()) {
    const lower = key.toLowerCase();
    if (lower !== "content-encoding" && lower !== "transfer-encoding") {
      responseHeaders.set(key, value);
    }
  }

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
