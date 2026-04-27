"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { AiDrawer, AiDrawerTrigger } from "@/components/layout/AiDrawer";
import { isAuthenticated, clearTokens } from "@/lib/auth";
import { LogOut } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [aiOpen, setAiOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  function handleLogout() {
    clearTokens();
    router.replace("/login");
  }

  return (
    <div className="flex h-full overflow-hidden">
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-end gap-2 h-14 px-5 border-b border-[var(--border)] bg-[var(--surface-1)]/80 backdrop-blur-sm shrink-0">
          <AiDrawerTrigger onClick={() => setAiOpen(true)} />
          <button
            onClick={handleLogout}
            title="Sign out"
            className="flex items-center justify-center w-7 h-7 rounded text-[var(--foreground-subtle)] hover:text-[var(--accent-teal)] hover:bg-[var(--accent-teal-muted)] transition-colors"
          >
            <LogOut size={13} strokeWidth={1.5} />
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>

      <AiDrawer open={aiOpen} onOpenChange={setAiOpen} />
    </div>
  );
}

