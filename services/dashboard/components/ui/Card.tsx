import { cn } from "@/lib/utils";

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-surface p-5 shadow-[var(--shadow-card)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardLabel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "text-xs font-semibold uppercase tracking-wide text-text-secondary",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  label,
  aside,
}: {
  label: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <CardLabel>{label}</CardLabel>
      {aside}
    </div>
  );
}
