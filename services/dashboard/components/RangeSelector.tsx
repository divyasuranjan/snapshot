import Link from "next/link";
import { cn } from "@/lib/utils";
import type { TimeRange } from "@/lib/types";

const RANGES: { value: TimeRange; label: string }[] = [
  { value: "24h", label: "24h" },
  { value: "7d", label: "7d" },
  { value: "30d", label: "30d" },
];

// Plain server-rendered links driven by the ?range= search param -- no
// client JS needed, works with the back button, and the current range is
// shareable as a URL.
export function RangeSelector({ current }: { current: TimeRange }) {
  return (
    <div className="flex rounded-lg border border-border bg-surface-2 p-1">
      {RANGES.map(({ value, label }) => (
        <Link
          key={value}
          href={`/?range=${value}`}
          className={cn(
            "rounded-md px-3 py-1.5 text-xs font-semibold transition-colors",
            value === current
              ? "bg-accent text-white"
              : "text-text-secondary hover:text-text-primary",
          )}
        >
          {label}
        </Link>
      ))}
    </div>
  );
}
