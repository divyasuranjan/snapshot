import { NextResponse } from "next/server";

// Server-only: the browser calls this route, and this route calls
// shortlink-api directly. The browser never sees SHORTLINK_API_URL or
// talks to the internal service itself.
const SHORTLINK_API_URL = process.env.SHORTLINK_API_URL ?? "http://localhost:8099";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const url = typeof body === "object" && body !== null ? (body as Record<string, unknown>).url : undefined;
  if (typeof url !== "string" || url.trim() === "") {
    return NextResponse.json({ error: "url is required" }, { status: 422 });
  }

  // Forward the caller's real IP so shortlink-api's rate limiter tracks
  // individual visitors rather than bucketing every request from this
  // proxy under one IP.
  const forwardedFor = request.headers.get("x-forwarded-for");

  try {
    const upstream = await fetch(`${SHORTLINK_API_URL}/api/links`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(forwardedFor ? { "X-Forwarded-For": forwardedFor } : {}),
      },
      body: JSON.stringify({ url }),
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ error: "Could not reach shortlink-api" }, { status: 502 });
  }
}
