"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type Member, type Invitation } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { UserPlus, X, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

const ROLE_COLORS: Record<Member["role"], string> = {
  admin: "bg-[var(--cobalt-muted)] text-[var(--cobalt)] border-[var(--cobalt)]",
  operator: "bg-[var(--accent-teal-muted)] text-[var(--accent-teal)] border-[var(--accent-teal-muted)]",
  viewer: "bg-[var(--surface-2)] text-[var(--foreground-muted)] border-border",
};

const STATUS_COLORS: Record<Invitation["status"], string> = {
  pending: "bg-[var(--status-warn-muted)] text-[var(--status-warn)] border-[var(--status-warn)]",
  accepted: "bg-[var(--status-ok-muted)] text-[var(--status-ok)] border-[var(--status-ok)]",
  expired: "bg-[var(--surface-2)] text-[var(--foreground-subtle)] border-border",
  cancelled: "bg-[var(--surface-2)] text-[var(--foreground-subtle)] border-border",
};

function RoleBadge({ role }: { role: Member["role"] }) {
  return (
    <Badge variant="outline" className={cn("text-[10px] font-medium capitalize", ROLE_COLORS[role])}>
      {role}
    </Badge>
  );
}

function InviteModal({
  open,
  onClose,
  onSubmit,
  loading,
  error,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (email: string, role: Member["role"]) => void;
  loading: boolean;
  error: string | null;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Member["role"]>("operator");

  if (!open) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(email.trim(), role);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-sm bg-[var(--surface-1)] border border-border rounded-xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold">Invite team member</h2>
          <button
            onClick={onClose}
            className="text-[var(--foreground-subtle)] hover:text-foreground transition-colors"
          >
            <X size={15} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs text-[var(--foreground-muted)]" htmlFor="invite-email">
              Work email
            </label>
            <input
              id="invite-email"
              type="email"
              required
              placeholder="colleague@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground placeholder:text-[var(--foreground-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-[var(--foreground-muted)]" htmlFor="invite-role">
              Role
            </label>
            <select
              id="invite-role"
              value={role}
              onChange={(e) => setRole(e.target.value as Member["role"])}
              className="w-full h-9 rounded-md border border-border bg-[var(--surface-2)] px-3 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-[var(--accent-teal)]"
            >
              <option value="admin">Admin — full access</option>
              <option value="operator">Operator — ack & resolve incidents</option>
              <option value="viewer">Viewer — read only</option>
            </select>
          </div>

          {error && (
            <p className="text-xs text-[var(--status-fail)] bg-[var(--status-fail-muted)] border border-[var(--status-fail)] rounded px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex gap-2 pt-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              className="flex-1 bg-[var(--accent-teal)] hover:bg-[var(--accent-teal-hover)] text-white"
              disabled={loading}
            >
              {loading ? "Sending…" : "Send invite"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TeamPage() {
  const qc = useQueryClient();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  const members = useQuery({ queryKey: ["team-members"], queryFn: api.team.members });
  const invitations = useQuery({ queryKey: ["team-invitations"], queryFn: api.team.invitations });

  const inviteMut = useMutation({
    mutationFn: ({ email, role }: { email: string; role: Member["role"] }) =>
      api.team.invite(email, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["team-invitations"] });
      setInviteOpen(false);
      setInviteError(null);
    },
    onError: (err) => {
      setInviteError(err instanceof Error ? err.message : "Failed to send invite");
    },
  });

  const cancelMut = useMutation({
    mutationFn: (id: string) => api.team.cancelInvitation(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["team-invitations"] }),
  });

  const removeMut = useMutation({
    mutationFn: (id: string) => api.team.removeMember(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["team-members"] }),
  });

  const pendingInvites = (invitations.data ?? []).filter((i) => i.status === "pending");

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Team</h1>
          <p className="text-sm text-[var(--foreground-muted)] mt-0.5">
            Manage workspace members and pending invitations
          </p>
        </div>
        <Button
          size="sm"
          className="bg-[var(--accent-teal)] hover:bg-[var(--accent-teal-hover)] text-white gap-1.5"
          onClick={() => { setInviteOpen(true); setInviteError(null); }}
        >
          <UserPlus size={13} strokeWidth={1.5} />
          Invite
        </Button>
      </div>

      {/* Members */}
      <section className="space-y-2">
        <h2 className="text-xs font-medium text-[var(--foreground-muted)] uppercase tracking-wider">
          Members ({members.data?.length ?? 0})
        </h2>
        {members.isLoading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 rounded-md" />)}
          </div>
        ) : (members.data ?? []).length === 0 ? (
          <p className="text-sm text-[var(--foreground-muted)] py-4">No members found.</p>
        ) : (
          <div className="border border-border rounded-md overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Name</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Email</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Role</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Joined</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(members.data ?? []).map((m) => (
                  <TableRow key={m.id} className="border-border hover:bg-[var(--surface-2)]">
                    <TableCell className="text-sm font-medium">{m.full_name || "—"}</TableCell>
                    <TableCell className="text-sm text-[var(--foreground-muted)]">{m.email}</TableCell>
                    <TableCell><RoleBadge role={m.role} /></TableCell>
                    <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums">
                      {new Date(m.joined_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <button
                        onClick={() => removeMut.mutate(m.id)}
                        disabled={removeMut.isPending}
                        title="Remove member"
                        className="text-[var(--foreground-subtle)] hover:text-[var(--status-fail)] transition-colors disabled:opacity-40"
                      >
                        <X size={13} />
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      {/* Pending invitations */}
      <section className="space-y-2">
        <h2 className="text-xs font-medium text-[var(--foreground-muted)] uppercase tracking-wider">
          Pending invitations ({pendingInvites.length})
        </h2>
        {invitations.isLoading ? (
          <Skeleton className="h-24 rounded-md" />
        ) : pendingInvites.length === 0 ? (
          <div className="flex items-center gap-2 py-4 text-sm text-[var(--foreground-muted)]">
            <Clock size={14} strokeWidth={1.5} />
            No pending invitations
          </div>
        ) : (
          <div className="border border-border rounded-md overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Email</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Role</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Status</TableHead>
                  <TableHead className="text-[var(--foreground-muted)] text-xs">Expires</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingInvites.map((inv) => (
                  <TableRow key={inv.id} className="border-border hover:bg-[var(--surface-2)]">
                    <TableCell className="text-sm">{inv.email}</TableCell>
                    <TableCell><RoleBadge role={inv.role} /></TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={cn("text-[10px] capitalize", STATUS_COLORS[inv.status])}
                      >
                        {inv.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-[var(--foreground-subtle)] tabular-nums">
                      {new Date(inv.expires_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <button
                        onClick={() => cancelMut.mutate(inv.id)}
                        disabled={cancelMut.isPending}
                        title="Cancel invitation"
                        className="text-[var(--foreground-subtle)] hover:text-[var(--status-fail)] transition-colors disabled:opacity-40"
                      >
                        <X size={13} />
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <InviteModal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        onSubmit={(email, role) => inviteMut.mutate({ email, role })}
        loading={inviteMut.isPending}
        error={inviteError}
      />
    </div>
  );
}
