"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Server,
  ShieldAlert,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/services", label: "Services", icon: Server },
  { href: "/checks", label: "Checks", icon: Activity },
  { href: "/incidents", label: "Incidents", icon: ShieldAlert },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="flex flex-col w-[240px] shrink-0 border-r border-border bg-[var(--surface-1)] h-full"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="flex items-center gap-2 h-14 px-5 border-b border-border">
        <span className="text-[var(--accent-teal)] font-semibold tracking-tight text-sm">
          SentinelOps
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors",
                active
                  ? "bg-[var(--surface-3)] text-foreground"
                  : "text-[var(--foreground-muted)] hover:bg-[var(--surface-2)] hover:text-foreground"
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon size={15} strokeWidth={1.5} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-border">
        <span className="text-[10px] text-[var(--foreground-subtle)] uppercase tracking-widest">
          acme
        </span>
      </div>
    </aside>
  );
}
