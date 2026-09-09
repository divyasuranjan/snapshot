"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex max-w-6xl flex-col items-center justify-center px-4 py-24 text-center">
      <p className="text-lg font-semibold text-text-primary">Something went wrong</p>
      <p className="mt-1 text-sm text-text-secondary">
        The dashboard hit an unexpected error rendering this page.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-4 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover"
      >
        Try again
      </button>
    </main>
  );
}
