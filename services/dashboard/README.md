# dashboard

Next.js (App Router, TypeScript) analytics UI: the product surface of
Snapshot. Server Components fetch aggregated stats directly from
analytics-worker; a small route handler proxies link creation to
shortlink-api so the browser never talks to either internal service
directly.

## Design

- **Palette**: dark-first, indigo accent (`#7C7AFF` dark / `#5046E5`
  light) against near-black/near-white neutrals — not default
  Tailwind/shadcn colors. Both themes are hand-tuned, not one inverted
  into the other. Toggle in the header; persisted via `next-themes`.
- **Type**: Inter for UI text, JetBrains Mono (tabular figures) for every
  number — KPI values, chart ticks, list counts.
- **Layout**: KPI row → clicks-over-time chart → top referrers + device
  breakdown → geo distribution. Time range (`24h` / `7d` / `30d`) is a
  plain `?range=` search param, so it's server-rendered, shareable, and
  needs no client JS.
- **Charts**: Recharts, reskinned (custom tooltip, gradient area fill, no
  default legend/grid look) rather than left at defaults. Geo is a ranked
  country list with flag emoji, not a map — see the root README for why.
- **States**: every card fetches independently and fails independently —
  one dependency being down degrades that card to an error message, not
  the whole page. Empty (zero clicks, no seed data) gets its own message,
  distinct from an error. Loading gets a skeleton matching the real
  layout (`app/loading.tsx`), not a spinner.
- **Sample data**: set `DEMO_MODE=true` to show a "Sample data" badge
  after running analytics-worker's seed script — see its README.

## Configuration (environment variables)

See [`.env.example`](.env.example). `ANALYTICS_WORKER_URL` and
`SHORTLINK_API_URL` are server-only — the browser never sees them, since
all requests to those services happen from Server Components or the
`/api/links` route handler.

## Running locally

```bash
npm install
npm run dev
```

Requires `analytics-worker` and `shortlink-api` reachable at the
configured URLs.

## Tests

```bash
npm test
```

Vitest + React Testing Library, covering the pure data-shaping logic
(`lib/format.ts`, `lib/api.ts`'s range-to-query-param mapping and its
error handling on a failed/unreachable fetch) and component behavior
(range selector active state, KPI fallback to `—` on missing data,
proportional referrer bars, country flag rendering).
