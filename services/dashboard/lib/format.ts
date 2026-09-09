const numberFormatter = new Intl.NumberFormat("en-US");

export function formatCount(n: number): string {
  return numberFormatter.format(n);
}

export function formatBucketLabel(iso: string, interval: "hour" | "day"): string {
  const d = new Date(iso);
  if (interval === "hour") {
    return d.toLocaleTimeString("en-US", { hour: "numeric", hour12: true });
  }
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

// Converts an ISO 3166-1 alpha-2 country code into its flag emoji by
// shifting each letter into the Unicode regional-indicator range -- no
// image assets or icon library needed.
export function countryFlag(countryCode: string | null | undefined): string {
  if (!countryCode || countryCode.length !== 2) return "";
  const codePoints = [...countryCode.toUpperCase()].map((c) => 0x1f1e6 + (c.charCodeAt(0) - 65));
  return String.fromCodePoint(...codePoints);
}
