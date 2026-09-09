export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-8 text-center">
      <p className="text-sm font-medium text-text-secondary">{title}</p>
      <p className="text-xs text-text-muted">{description}</p>
    </div>
  );
}

export function ErrorState({ label, error }: { label: string; error: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-8 text-center">
      <p className="text-sm font-medium text-danger">Couldn&apos;t load {label}</p>
      <p className="text-xs text-text-muted">{error}</p>
    </div>
  );
}
