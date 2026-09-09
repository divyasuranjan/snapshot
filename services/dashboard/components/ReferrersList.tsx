import { formatCount } from "@/lib/format";
import type { ReferrerRow } from "@/lib/types";

export function ReferrersList({ referrers }: { referrers: ReferrerRow[] }) {
  const max = Math.max(...referrers.map((r) => r.clicks), 1);

  return (
    <div className="flex flex-col gap-3">
      {referrers.map((r) => (
        <div key={r.referrer}>
          <div className="mb-1 flex items-center justify-between gap-2 text-sm">
            <span className="truncate text-text-primary">{r.referrer}</span>
            <span className="shrink-0 font-mono text-xs tabular-nums text-text-secondary">
              {formatCount(r.clicks)}
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-surface-2">
            <div
              className="h-full rounded-full bg-accent"
              style={{ width: `${Math.max((r.clicks / max) * 100, 3)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
