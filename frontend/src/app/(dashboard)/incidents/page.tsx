"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type Incident } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

type StateFilter = "all" | "open" | "acknowledged" | "resolved";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
  high: "bg-[var(--status-fail-muted)] text-[var(--status-fail)] border-[var(--status-fail)]",
  medium: "bg-[var(--status-warn-muted)] text-[var(--status-warn)] border-[var(--status-warn)]",
  low: "bg-[var(--surface-2)] text-[var(--foreground-muted)] border-border",
};

const STATE_COLORS: Record<string, string> = {
  open: "text-[var(--status-fail)]",
  acknowledged: "text-[var(--status-warn)]",
  resolved: "text-[var(--status-ok)]",
};

const FILTERS: { label: string; value: StateFilter }[] = [
  { label: "All", value: "all" },
  { label: "Open", value: "open" },
  { label: "Acknowledged", value: "acknowledged" },
  { label: "Resolved", value: "resolved" },
];

export default function IncidentsPage() {
  const [filter, setFilter] = useState<StateFilter>("open");
  const queryClient = useQueryClient();

  const incidents = useQuery({
    queryKey: ["incidents", filter],
    queryFn: () => api.incidents.list(filter === "all" ? undefined : filter),
  });

  const ack = useMutation({
    mutationFn: (id: string) => api.incidents.acknowledge(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["incidents"] }),
  });

  const resolve = useMutation({
    mutationFn: (id: string) => api.incidents.resolve(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["incidents"] }),
  });

  const rows = incidents.data ?? [];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Incidents</h1>
        <span className="text-xs text-[var(--foreground-muted)] tabular-nums">
          {incidents.data ? `${incidents.data.length} results` : ""}
        </span>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={cn(
              "px-3 py-1.5 text-xs rounded transition-colors",
              filter === f.value
                ? "bg-[var(--surface-3)] text-foreground"
                : "text-[var(--foreground-muted)] hover:text-foreground hover:bg-[var(--surface-2)]"
            )}
          >
            {f.label}
          </button>
        ))}
        <Separator orientation="vertical" className="h-4 mx-1" />
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ["incidents"] })}
          className="px-3 py-1.5 text-xs text-[var(--foreground-muted)] hover:text-foreground transition-colors rounded"
        >
          Refresh
        </button>
      </div>

      {incidents.isLoading ? (
        <Skeleton className="h-48 w-full rounded-md" />
      ) : incidents.isError ? (
        <p className="text-sm text-[var(--status-fail)]">Failed to load incidents.</p>
      ) : rows.length === 0 ? (
        <div className="flex items-center gap-2 py-6 text-sm text-[var(--status-ok)]">
          <CheckCircle2 size={15} />
          No incidents for this filter.
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
                <TableHead className="text-[var(--foreground-muted)] text-xs">Resolved</TableHead>
                <TableHead className="text-[var(--foreground-muted)] text-xs" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((inc: Incident) => (
                <TableRow key={inc.id} className="border-border hover:bg-[var(--surface-2)]">
                  <TableCell className="text-sm font-medium">{inc.service_name}</TableCell>
                  <TableCell className="text-sm text-[var(--foreground-muted)]">
                    {inc.health_check_name ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn("text-[10px] font-medium", SEVERITY_COLORS[inc.severity])}
                    >
                      {inc.severity}
                    </Badge>
                  </TableCell>
                  <TableCell
                    className={cn(
                      "text-xs capitalize font-medium",
                      STATE_COLORS[inc.state] ?? "text-[var(--foreground-muted)]"
                    )}
                  >
                    {inc.state}
                  </TableCell>
                  <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums">
                    {new Date(inc.opened_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums">
                    {inc.resolved_at ? new Date(inc.resolved_at).toLocaleString() : "—"}
                  </TableCell>
                  <TableCell className="text-right pr-4">
                    <div className="flex items-center justify-end gap-1.5">
                      {inc.state === "open" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-[10px] text-[var(--status-warn)] hover:text-[var(--status-warn)] hover:bg-[var(--status-warn-muted)]"
                          disabled={ack.isPending}
                          onClick={() => ack.mutate(inc.id)}
                        >
                          Ack
                        </Button>
                      )}
                      {inc.state !== "resolved" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-[10px] text-[var(--status-ok)] hover:text-[var(--status-ok)] hover:bg-[var(--status-ok-muted)]"
                          disabled={resolve.isPending}
                          onClick={() => resolve.mutate(inc.id)}
                        >
                          Resolve
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
