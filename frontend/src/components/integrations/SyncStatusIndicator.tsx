"use client";

interface SyncStatusIndicatorProps {
  status: "idle" | "syncing" | "error";
  lastSyncedAt?: string | null;
}

export function SyncStatusIndicator({
  status,
  lastSyncedAt,
}: SyncStatusIndicatorProps) {
  const statusConfig = {
    idle: { color: "bg-green-500", label: "Verbunden" },
    syncing: { color: "bg-blue-500 animate-pulse", label: "Synchronisiert..." },
    error: { color: "bg-red-500", label: "Fehler" },
  };

  const config = statusConfig[status];

  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return "Gerade eben";
    if (diffMin < 60) return `Vor ${diffMin} Min.`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `Vor ${diffHours} Std.`;
    const diffDays = Math.floor(diffHours / 24);
    return `Vor ${diffDays} Tag(en)`;
  };

  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block h-2 w-2 rounded-full ${config.color}`} />
      <span className="text-xs text-gray-500">
        {config.label}
        {lastSyncedAt && status === "idle" && (
          <> &middot; {formatRelativeTime(lastSyncedAt)}</>
        )}
      </span>
    </div>
  );
}
