"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import type { TimeseriesPoint } from "@/lib/types";
import { formatBucketLabel, formatCount } from "@/lib/format";

function ChartTooltip({
  active,
  payload,
  interval,
}: {
  active?: boolean;
  payload?: { value: number; payload: TimeseriesPoint }[];
  interval: "hour" | "day";
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;

  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-xs shadow-[var(--shadow-card)]">
      <div className="text-text-secondary">{formatBucketLabel(point.bucket, interval)}</div>
      <div className="mt-0.5 font-mono font-semibold tabular-nums text-text-primary">
        {formatCount(point.clicks)} clicks
      </div>
    </div>
  );
}

export function TimeseriesChart({
  data,
  interval,
}: {
  data: TimeseriesPoint[];
  interval: "hour" | "day";
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="clicksFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.28} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="var(--border)" />
        <XAxis
          dataKey="bucket"
          tickFormatter={(v: string) => formatBucketLabel(v, interval)}
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
          minTickGap={32}
        />
        <Tooltip content={<ChartTooltip interval={interval} />} cursor={{ stroke: "var(--border-strong)" }} />
        <Area
          type="monotone"
          dataKey="clicks"
          stroke="var(--accent)"
          strokeWidth={2}
          fill="url(#clicksFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
