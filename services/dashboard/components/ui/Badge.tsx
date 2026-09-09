import { cn } from "@/lib/utils";

export function Badge({
  children,
  variant = "accent",
  className,
}: {
  children: React.ReactNode;
  variant?: "accent" | "danger" | "neutral";
  className?: string;
}) {
  const variantClasses = {
    accent: "bg-accent-subtle text-accent-on-subtle",
    danger: "bg-danger-subtle text-danger-on-subtle",
    neutral: "bg-surface-2 text-text-secondary",
  }[variant];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold",
        variantClasses,
        className,
      )}
    >
      {children}
    </span>
  );
}
