import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center justify-between">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-9 w-64" />
      </div>

      <div className="mb-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="h-3 w-20" />
            <Skeleton className="mt-3 h-7 w-16" />
          </Card>
        ))}
      </div>

      <Card className="mb-3">
        <Skeleton className="mb-4 h-3 w-32" />
        <Skeleton className="h-[220px] w-full" />
      </Card>

      <div className="mb-3 grid grid-cols-1 gap-3 lg:grid-cols-[1.3fr_1fr]">
        <Card>
          <Skeleton className="mb-4 h-3 w-24" />
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="mb-3 h-8 w-full" />
          ))}
        </Card>
        <Card>
          <Skeleton className="mb-4 h-3 w-16" />
          <Skeleton className="h-[110px] w-full" />
        </Card>
      </div>

      <Card>
        <Skeleton className="mb-4 h-3 w-24" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="mb-3 h-6 w-full" />
        ))}
      </Card>
    </main>
  );
}
