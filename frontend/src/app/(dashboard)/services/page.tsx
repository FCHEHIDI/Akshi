"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type Service, type CheckResult } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  ok: "bg-[var(--status-ok-muted)] text-[var(--status-ok)] border-[var(--status-ok)]",
  fail: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
  timeout: "bg-[var(--status-warn-muted)] text-[var(--status-warn)] border-[var(--status-warn)]",
  error: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
  unknown: "bg-[var(--surface-2)] text-[var(--foreground-subtle)] border-border",
};

function ServiceCard({
  service,
  results,
}: {
  service: Service;
  results: CheckResult[];
}) {
  const svcResults = results.filter((r) => r.service_id === service.id);
  const latest = svcResults[0];
  const status = latest?.status ?? "unknown";
  const avgMs =
    svcResults.length > 0
      ? Math.round(svcResults.reduce((s, r) => s + r.duration_ms, 0) / svcResults.length)
      : null;

  return (
    <Card className="bg-[var(--surface-1)] border-border hover:border-[var(--foreground-subtle)] transition-colors">
      <CardHeader className="pb-2 pt-4 px-4">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm font-medium">{service.name}</CardTitle>
          <Badge variant="outline" className={cn("text-[10px] font-medium", STATUS_COLORS[status])}>
            {status}
          </Badge>
        </div>
        <p className="text-xs text-[var(--foreground-subtle)] font-mono">
              {service.tags.join(" · ")}
            </p>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-2">
        {service.description && (
          <p className="text-xs text-[var(--foreground-muted)]">{service.description}</p>
        )}
        <div className="flex items-center gap-4 pt-1">
          {avgMs !== null && (
            <span className="text-xs text-[var(--foreground-subtle)] tabular-nums">
              avg {avgMs} ms
            </span>
          )}
          {latest && (
            <span className="text-xs text-[var(--foreground-subtle)] tabular-nums">
              {new Date(latest.created_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function ServicesPage() {
  const services = useQuery({ queryKey: ["services"], queryFn: api.services.list });
  const results = useQuery({ queryKey: ["results"], queryFn: () => api.results.recent(100) });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Services</h1>
        <span className="text-xs text-[var(--foreground-muted)] tabular-nums">
          {services.data ? `${services.data.length} total` : ""}
        </span>
      </div>

      {services.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-md" />
          ))}
        </div>
      ) : services.isError ? (
        <p className="text-sm text-[var(--status-fail)]">Failed to load services.</p>
      ) : services.data?.length === 0 ? (
        <p className="text-sm text-[var(--foreground-muted)]">No services configured yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(services.data ?? []).map((svc) => (
            <ServiceCard
              key={svc.id}
              service={svc}
              results={results.data ?? []}
            />
          ))}
        </div>
      )}
    </div>
  );
}
