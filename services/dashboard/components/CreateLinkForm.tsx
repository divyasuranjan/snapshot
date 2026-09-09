"use client";

import { useState } from "react";
import type { CreateLinkResponse } from "@/lib/types";

type Status = { kind: "idle" } | { kind: "loading" } | { kind: "error"; message: string } | { kind: "success"; result: CreateLinkResponse };

export function CreateLinkForm() {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [copied, setCopied] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) {
      setStatus({ kind: "error", message: "Enter a URL first" });
      return;
    }

    setStatus({ kind: "loading" });
    try {
      const res = await fetch("/api/links", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const body = await res.json();
      if (!res.ok) {
        setStatus({ kind: "error", message: body.error ?? "Couldn't create that link" });
        return;
      }
      setStatus({ kind: "success", result: body as CreateLinkResponse });
      setCopied(false);
    } catch {
      setStatus({ kind: "error", message: "Couldn't reach shortlink-api" });
    }
  }

  function reset() {
    setUrl("");
    setStatus({ kind: "idle" });
  }

  if (status.kind === "success") {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-border bg-surface-2 px-3 py-1.5">
        <span className="font-mono text-sm text-accent">{status.result.short_url}</span>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(status.result.short_url);
            setCopied(true);
          }}
          className="text-xs font-semibold text-text-secondary hover:text-text-primary"
        >
          {copied ? "Copied" : "Copy"}
        </button>
        <button
          type="button"
          onClick={reset}
          className="text-xs text-text-muted hover:text-text-primary"
        >
          New
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com/your-long-url"
        className="w-56 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none sm:w-72"
      />
      <button
        type="submit"
        disabled={status.kind === "loading"}
        className="shrink-0 rounded-lg bg-accent px-3 py-1.5 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
      >
        {status.kind === "loading" ? "Shortening…" : "Shorten"}
      </button>
      {status.kind === "error" && (
        <span className="text-xs text-danger">{status.message}</span>
      )}
    </form>
  );
}
