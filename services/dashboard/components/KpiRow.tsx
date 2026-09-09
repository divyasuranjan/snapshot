import { Card, CardLabel } from "@/components/ui/Card";
import { formatCount } from "@/lib/format";

function KpiTile({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardLabel>{label}</CardLabel>
      <div className="mt-2 truncate font-mono text-2xl font-semibold tabular-nums text-text-primary">
        {value}
      </div>
    </Card>
  );
}

export function KpiRow({
  totalClicks,
  topReferrer,
  topCountry,
  topBrowser,
}: {
  totalClicks: number | null;
  topReferrer: string | null;
  topCountry: string | null;
  topBrowser: string | null;
}) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <KpiTile label="Total clicks" value={totalClicks !== null ? formatCount(totalClicks) : "—"} />
      <KpiTile label="Top referrer" value={topReferrer ?? "—"} />
      <KpiTile label="Top country" value={topCountry ?? "—"} />
      <KpiTile label="Top browser" value={topBrowser ?? "—"} />
    </div>
  );
}
