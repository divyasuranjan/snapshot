import { getDevices, getGeo, getReferrers, getTimeseries } from "@/lib/api";
import type { TimeRange } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState } from "@/components/ui/StateMessage";
import { RangeSelector } from "@/components/RangeSelector";
import { ThemeToggle } from "@/components/ThemeToggle";
import { CreateLinkForm } from "@/components/CreateLinkForm";
import { KpiRow } from "@/components/KpiRow";
import { TimeseriesChart } from "@/components/TimeseriesChart";
import { ReferrersList } from "@/components/ReferrersList";
import { DeviceBreakdown } from "@/components/DeviceBreakdown";
import { GeoList } from "@/components/GeoList";

function isValidRange(value: string | undefined): value is TimeRange {
  return value === "24h" || value === "7d" || value === "30d";
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ range?: string }>;
}) {
  const { range: rawRange } = await searchParams;
  const range: TimeRange = isValidRange(rawRange) ? rawRange : "24h";

  const [timeseries, referrers, devices, geo] = await Promise.all([
    getTimeseries(range),
    getReferrers(range, 8),
    getDevices(range),
    getGeo(range, 8),
  ]);

  const totalClicks = timeseries.ok
    ? timeseries.data.series.reduce((sum, p) => sum + p.clicks, 0)
    : null;
  const topReferrer = referrers.ok ? (referrers.data.referrers[0]?.referrer ?? null) : null;
  const topCountry = geo.ok ? (geo.data.by_country[0]?.country ?? null) : null;
  const topBrowser = devices.ok ? (devices.data.by_browser[0]?.name ?? null) : null;

  const isDemoMode = process.env.DEMO_MODE === "true";

  return (
    <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="h-6 w-6 rounded-md bg-accent" />
          <span className="text-base font-bold text-text-primary">Snapshot</span>
          {isDemoMode && <Badge variant="accent">Sample data</Badge>}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <CreateLinkForm />
          <RangeSelector current={range} />
          <ThemeToggle />
        </div>
      </header>

      <div className="mb-3">
        <KpiRow
          totalClicks={totalClicks}
          topReferrer={topReferrer}
          topCountry={topCountry}
          topBrowser={topBrowser}
        />
      </div>

      <Card className="mb-3">
        <CardHeader label="Clicks over time" />
        {!timeseries.ok ? (
          <ErrorState label="clicks over time" error={timeseries.error} />
        ) : timeseries.data.series.every((p) => p.clicks === 0) ? (
          <EmptyState
            title="No clicks yet"
            description="Once your links get traffic, this chart fills in automatically."
          />
        ) : (
          <TimeseriesChart data={timeseries.data.series} interval={timeseries.data.interval} />
        )}
      </Card>

      <div className="mb-3 grid grid-cols-1 gap-3 lg:grid-cols-[1.3fr_1fr]">
        <Card>
          <CardHeader label="Top referrers" />
          {!referrers.ok ? (
            <ErrorState label="referrers" error={referrers.error} />
          ) : referrers.data.referrers.length === 0 ? (
            <EmptyState title="No referrers yet" description="Referrer domains will show up here as clicks come in." />
          ) : (
            <ReferrersList referrers={referrers.data.referrers} />
          )}
        </Card>

        <Card>
          <CardHeader label="Devices" />
          {!devices.ok ? (
            <ErrorState label="device breakdown" error={devices.error} />
          ) : devices.data.by_device.length === 0 ? (
            <EmptyState title="No device data yet" description="Device, browser, and OS breakdowns appear here once clicks come in." />
          ) : (
            <DeviceBreakdown byDevice={devices.data.by_device} byBrowser={devices.data.by_browser} />
          )}
        </Card>
      </div>

      <Card>
        <CardHeader label="Top countries" />
        {!geo.ok ? (
          <ErrorState label="geo distribution" error={geo.error} />
        ) : geo.data.by_country.length === 0 ? (
          <EmptyState title="No geo data yet" description="Click locations will show up here once clicks come in." />
        ) : (
          <GeoList countries={geo.data.by_country} />
        )}
      </Card>
    </main>
  );
}
