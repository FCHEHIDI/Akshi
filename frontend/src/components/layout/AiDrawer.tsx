"use client";

import { useState } from "react";
import { Eye, X, ChevronRight } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface AiMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: string;
}

interface AiDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  messages?: AiMessage[];
}

export function AiDrawer({ open, onOpenChange, messages = [] }: AiDrawerProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange} modal={false}>
      <SheetContent
        side="right"
        className={cn(
          "w-[400px] p-0 border-l flex flex-col",
          "bg-[var(--ai-surface)] border-[var(--ai-border)]"
        )}
        style={{ boxShadow: "none" }}
      >
        <SheetHeader className="flex-row items-center justify-between px-4 py-3 border-b border-[var(--ai-border)]">
          <div className="flex items-center gap-2">
            <Eye size={14} className="text-[var(--ai-accent)]" strokeWidth={1.25} />
            <SheetTitle className="text-sm font-medium text-foreground">
              AI Analysis
            </SheetTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-[var(--foreground-muted)] hover:text-foreground"
            onClick={() => onOpenChange(false)}
          >
            <X size={14} />
          </Button>
        </SheetHeader>

        <ScrollArea className="flex-1">
          <div className="px-4 py-3 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                <Eye size={28} className="text-[var(--ai-accent)] opacity-30" strokeWidth={0.75} />
                <p className="text-[var(--foreground-muted)] text-sm">
                  AI recommendations will appear here when incidents are detected.
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-[var(--foreground-subtle)] uppercase tracking-wider">
                      {msg.role === "assistant" ? "AI" : "You"}
                    </span>
                    <span className="text-[10px] text-[var(--foreground-subtle)]">
                      {msg.timestamp}
                    </span>
                  </div>
                  <div
                    className={cn(
                      "text-sm rounded p-3 border",
                      msg.role === "assistant"
                        ? "bg-[var(--surface-1)] border-[var(--ai-border)] text-foreground"
                        : "bg-[var(--cobalt-muted)] border-[var(--cobalt-muted)] text-[var(--foreground-muted)]"
                    )}
                  >
                    {msg.content}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

/* Trigger button shown in the topbar */
export function AiDrawerTrigger({
  onClick,
  hasMessages,
}: {
  onClick: () => void;
  hasMessages?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-3 py-1.5 rounded text-xs border transition-colors",
        hasMessages
          ? "bg-[var(--ai-surface)] border-[var(--ai-border)] text-[var(--ai-accent)] hover:border-[var(--ai-accent)]"
          : "bg-transparent border-border text-[var(--foreground-muted)] hover:text-foreground hover:border-[var(--foreground-subtle)]"
      )}
    >
      <Eye size={12} strokeWidth={1.25} />
      AI
      <ChevronRight size={11} />
    </button>
  );
}
