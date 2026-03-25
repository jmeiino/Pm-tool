"use client";

import { cn } from "@/lib/utils";

const statusConfig = {
  idle: { color: "bg-green-500", label: "Verfügbar" },
  working: { color: "bg-blue-500 animate-pulse", label: "Arbeitet" },
  waiting: { color: "bg-yellow-500", label: "Wartet" },
  offline: { color: "bg-gray-400", label: "Offline" },
};

interface AgentStatusBadgeProps {
  status: keyof typeof statusConfig;
  showLabel?: boolean;
  size?: "sm" | "md";
}

export function AgentStatusBadge({ status, showLabel = false, size = "sm" }: AgentStatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.offline;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={cn(
          "inline-block rounded-full",
          config.color,
          size === "sm" ? "h-2 w-2" : "h-3 w-3"
        )}
      />
      {showLabel && <span className="text-xs text-gray-500">{config.label}</span>}
    </span>
  );
}
