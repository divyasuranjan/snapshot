import { countryFlag, formatCount } from "@/lib/format";
import type { CountryRow } from "@/lib/types";

export function GeoList({ countries }: { countries: CountryRow[] }) {
  const max = Math.max(...countries.map((c) => c.clicks), 1);

  return (
    <div className="flex flex-col gap-3">
      {countries.map((c) => (
        <div key={c.country} className="flex items-center gap-3">
          <span className="w-40 shrink-0 truncate text-sm text-text-primary">
            <span aria-hidden className="mr-1.5">
              {countryFlag(c.country_code)}
            </span>
            {c.country}
          </span>
          <div className="h-1.5 flex-1 rounded-full bg-surface-2">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.max((c.clicks / max) * 100, 3)}%`,
                background: "var(--chart-5)",
              }}
            />
          </div>
          <span className="w-12 shrink-0 text-right font-mono text-xs tabular-nums text-text-secondary">
            {formatCount(c.clicks)}
          </span>
        </div>
      ))}
    </div>
  );
}
