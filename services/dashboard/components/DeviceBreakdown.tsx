"use client";

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import type { NamedCount } from "@/lib/types";
import { formatCount } from "@/lib/format";

const DEVICE_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];

export function DeviceBreakdown({
  byDevice,
  byBrowser,
}: {
  byDevice: NamedCount[];
  byBrowser: NamedCount[];
}) {
  const total = byDevice.reduce((sum, d) => sum + d.clicks, 0) || 1;

  return (
    <div>
      <div className="flex items-center gap-4">
        <div className="h-[110px] w-[110px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={byDevice}
                dataKey="clicks"
                nameKey="name"
                innerRadius={34}
                outerRadius={52}
                strokeWidth={0}
              >
                {byDevice.map((d, i) => (
                  <Cell key={d.name} fill={DEVICE_COLORS[i % DEVICE_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-1 flex-col gap-1.5">
          {byDevice.map((d, i) => (
            <div key={d.name} className="flex items-center gap-2 text-xs">
              <span
                className="h-2 w-2 shrink-0 rounded-sm"
                style={{ background: DEVICE_COLORS[i % DEVICE_COLORS.length] }}
              />
              <span className="capitalize text-text-secondary">{d.name}</span>
              <span className="ml-auto font-mono tabular-nums text-text-primary">
                {Math.round((d.clicks / total) * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-2 border-t border-border pt-4">
        {byBrowser.slice(0, 4).map((b) => (
          <div key={b.name} className="flex items-center justify-between text-xs">
            <span className="text-text-secondary">{b.name}</span>
            <span className="font-mono tabular-nums text-text-primary">{formatCount(b.clicks)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
