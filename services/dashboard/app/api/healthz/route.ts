import { NextResponse } from "next/server";

// Liveness only: the dashboard has no hard runtime dependency of its own
// (each card fetches analytics-worker/shortlink-api independently and
// degrades to its own error state if one is down, per app/page.tsx), so
// there's no separate readiness check -- "the Next.js server is answering
// requests" is the whole story here.
export function GET() {
  return NextResponse.json({ status: "ok" });
}
