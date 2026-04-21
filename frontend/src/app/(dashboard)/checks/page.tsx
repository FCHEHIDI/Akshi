"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type CheckResult } from "@/lib/api";
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
import { CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_ICON = {
  ok: <CheckCircle2 size={13} className="text-[var(--status-ok)]" />,
  fail: <XCircle size={13} className="text-[var(--status-fail)]" />,
  timeout: <Clock size={13} className="text-[var(--status-warn)]" />,
  error: <AlertCircle size={13} className="text-[var(--status-fail)]" />,
};

const STATUS_BADGE: Record<string, string> = {
  ok: "bg-[var(--status-ok-muted)] text-[var(--status-ok)] border-[var(--status-ok)]",
  fail: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
  timeout: "bg-[var(--status-warn-muted)] text-[var(--status-warn)] border-[var(--status-warn)]",
  error: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
};

export default function ChecksPage() {
  const checks = useQuery({ queryKey: ["checks"], queryFn: api.checks.list });
  const results = useQuery({ queryKey: ["results"], queryFn: () => api.results.recent(100) });

  // latest result per check
  const latestByCheck = (results.data ?? []).reduce<Record<string, CheckResult>>(
    (acc, r) => {
      if (!acc[r.health_check]) acc[r.health_check] = r;
      return acc;
    },
    {}
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Checks</h1>
        <span className="text-xs text-[var(--foreground-muted)] tabular-nums">
          {checks.data ? `${checks.data.length} configured` : ""}
        </span>
      </div>

      {checks.isLoading ? (
        <Skeleton className="h-48 w-full rounded-md" />
      ) : checks.isError ? (
        <p className="text-sm text-[var(--status-fail)]">Failed to load checks.</p>
      ) : checks.data?.length === 0 ? (
        <p className="text-sm text-[var(--foreground-muted)]">No checks configured yet.</p>
      ) : (
        <div className="border border-border rounded-md overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-[var(--foreground-muted)] text-xs w-8" />
                <TableHead className="text-[var(--foreground-muted)] text-xs">Name</TableHead>
                <TableHead className="text-[var(--foreground-muted)] text-xs">Type</TableHead>
                <TableHead className="text-[var(--foreground-muted)] text-xs">Target</TableHead>
                <TableHead className="text-[var(--foreground-muted)] text-xs">Interval</TableHead>
                <TableHead className="text-[var(--foreground-muted)] text-xs">Last result</TableHead>
                <TableHead className="text-[var(--foreground-muted)] text-xs text-right">Duration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(checks.data ?? []).map((check) => {
                const latest = latestByCheck[check.id];
                const status = latest?.status ?? "unknown";
                return (
                  <TableRow
                    key={check.id}
                    className={cn(
                      "border-border hover:bg-[var(--surface-2)]",
                      !check.is_enabled && "opacity-50"
                    )}
                  >
                    <TableCell className="py-2 pl-4">
                      {STATUS_ICON[status as keyof typeof STATUS_ICON] ?? (
                        <span className="w-3 h-3 rounded-full bg-[var(--foreground-subtle)] inline-block" />
                      )}
                    </TableCell>
                    <TableCell className="text-sm font-medium">{check.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-[10px] font-mono border-[var(--cobalt-muted)] text-[var(--cobalt)] bg-[var(--cobalt-muted)]">
                        {check.check_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-[var(--foreground-muted)] font-mono max-w-[180px] truncate">
                      {check.target}
                    </TableCell>
                    <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums">
                      {check.interval_seconds}s
                    </TableCell>
                    <TableCell>
                      {latest ? (
                        <Badge variant="outline" className={cn("text-[10px] font-medium", STATUS_BADGE[status] ?? "")}>
                          {status}
                        </Badge>
                      ) : (
                        <span className="text-xs text-[var(--foreground-subtle)]">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums text-right pr-4">
                      {latest ? `${latest.duration_ms} ms` : "—"}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
