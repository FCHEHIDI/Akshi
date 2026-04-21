"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type Service, type CheckResult, type Incident } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

function StatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    ok: "bg-[var(--status-ok)]",
    fail: "bg-[var(--status-fail)]",
    timeout: "bg-[var(--status-warn)]",
    error: "bg-[var(--status-fail)]",
  };
  return (
    <span
      className={cn("inline-block w-2 h-2 rounded-full", map[status] ?? "bg-[var(--status-unknown)]")}
    />
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
    high: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
    medium: "bg-[var(--status-warn-muted)] text-[var(--status-warn)] border-[var(--status-warn)]",
    low: "bg-[var(--surface-2)] text-[var(--foreground-muted)] border-border",
  };
  return (
    <Badge variant="outline" className={cn("text-[10px] font-medium", map[severity])}>
      {severity}
    </Badge>
  );
}

function KpiCard({ title, value, sub }: { title: string; value: React.ReactNode; sub?: string }) {
  return (
    <Card className="bg-[var(--surface-1)] border-border">
      <CardHeader className="pb-1 pt-4 px-4">
        <CardTitle className="text-xs font-medium text-[var(--foreground-muted)] uppercase tracking-wider">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <div className="text-2xl font-semibold tabular-nums">{value}</div>
        {sub && <p className="text-xs text-[var(--foreground-subtle)] mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const services = useQuery({ queryKey: ["services"], queryFn: api.services.list });
  const results = useQuery({ queryKey: ["results"], queryFn: () => api.results.recent(50) });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: () => api.incidents.list() });

  const totalServices = services.data?.length ?? 0;

  // Compute per-service latest result status
  const latestByService = (results.data ?? []).reduce<Record<string, CheckResult>>((acc, r) => {
    if (!acc[r.health_check]) acc[r.health_check] = r;
    return acc;
  }, {});

  const healthyServices = (services.data ?? []).filter((s) => {
    // A service is healthy if all checks visible are ok
    const serviceResults = (results.data ?? []).filter((r) =>
      latestByService[r.health_check]?.health_check === r.health_check &&
      r.status === "ok"
    );
    return serviceResults.length > 0;
  }).length;

  const openIncidents = (incidents.data ?? []).filter((i) => i.state === "open").length;

  const avgMs =
    results.data && results.data.length > 0
      ? Math.round(results.data.reduce((s, r) => s + r.duration_ms, 0) / results.data.length)
      : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Dashboard</h1>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          title="Total Services"
          value={services.isLoading ? <Skeleton className="h-7 w-10" /> : totalServices}
        />
        <KpiCard
          title="Healthy"
          value={
            services.isLoading ? (
              <Skeleton className="h-7 w-10" />
            ) : (
              <span className={healthyServices === totalServices && totalServices > 0 ? "text-[var(--status-ok)]" : ""}>
                {healthyServices}
              </span>
            )
          }
          sub={totalServices > 0 ? `of ${totalServices}` : undefined}
        />
        <KpiCard
          title="Open Incidents"
          value={
            incidents.isLoading ? (
              <Skeleton className="h-7 w-10" />
            ) : (
              <span className={openIncidents > 0 ? "text-[var(--status-fail)]" : "text-[var(--status-ok)]"}>
                {openIncidents}
              </span>
            )
          }
        />
        <KpiCard
          title="Avg Response"
          value={results.isLoading ? <Skeleton className="h-7 w-14" /> : `${avgMs} ms`}
          sub={results.data ? `over last ${results.data.length} checks` : undefined}
        />
      </div>

      {/* Services grid */}
      <section className="space-y-2">
        <h2 className="text-xs font-medium text-[var(--foreground-muted)] uppercase tracking-wider">
          Services
        </h2>
        {services.isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-md" />
            ))}
          </div>
        ) : services.data?.length === 0 ? (
          <p className="text-sm text-[var(--foreground-muted)]">No services configured.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {(services.data ?? []).map((svc) => {
              const recentForSvc = (results.data ?? []).find((r) => r.service_id === svc.id);
              const status = recentForSvc?.status ?? "unknown";
              return (
                <Card
                  key={svc.id}
                  className="bg-[var(--surface-1)] border-border hover:border-[var(--foreground-subtle)] transition-colors"
                >
                  <CardContent className="p-3 flex items-start gap-2">
                    <StatusDot status={status} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{svc.name}</p>
                      <p className="text-xs text-[var(--foreground-subtle)] capitalize">{status}</p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* Incidents table */}
      <section className="space-y-2">
        <h2 className="text-xs font-medium text-[var(--foreground-muted)] uppercase tracking-wider">
          Active Incidents
        </h2>
        {incidents.isLoading ? (
          <Skeleton className="h-32 w-full rounded-md" />
        ) : (incidents.data ?? []).filter((i) => i.state !== "resolved").length === 0 ? (
          <div className="flex items-center gap-2 py-4 text-sm text-[var(--status-ok)]">
            <CheckCircle2 size={15} />
            No active incidents
          </div>
        ) : (
          <div className="border border-border rounded-md overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Service</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Check</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Severity</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">State</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Opened</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(incidents.data ?? [])
                  .filter((i) => i.state !== "resolved")
                  .map((inc) => (
                    <TableRow key={inc.id} className="border-border hover:bg-[var(--surface-2)]">
                      <TableCell className="text-sm font-medium">{inc.service_name}</TableCell>
                      <TableCell className="text-sm text-[var(--foreground-muted)]">
                        {inc.health_check_name ?? "—"}
                      </TableCell>
                      <TableCell>
                        <SeverityBadge severity={inc.severity} />
                      </TableCell>
                      <TableCell className="text-sm capitalize text-[var(--foreground-muted)]">
                        {inc.state}
                      </TableCell>
                      <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums">
                        {new Date(inc.opened_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>
    </div>
  );
}
