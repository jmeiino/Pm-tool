"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { Card } from "@/components/ui/Card";
import {
  useImportDashboard,
  useGitHubConflicts,
  useUpdateSyncSchedule,
  type ImportHistoryEntry,
} from "@/hooks/useImport";
import { useToast } from "@/components/ui/Toast";
import { useSyncIntegration } from "@/hooks/useIntegrations";
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

const TYPE_META: Record<string, { label: string; icon: string; color: string }> = {
  jira: { label: "Jira", icon: "J", color: "bg-blue-500" },
  github: { label: "GitHub", icon: "G", color: "bg-gray-800" },
  confluence: { label: "Confluence", icon: "C", color: "bg-blue-400" },
};

function IntegrationCard({ entry }: { entry: ImportHistoryEntry }) {
  const meta = TYPE_META[entry.integration_type] || {
    label: entry.integration_type,
    icon: "?",
    color: "bg-gray-500",
  };
  const syncIntegration = useSyncIntegration();
  const updateSchedule = useUpdateSyncSchedule();
  const { addToast } = useToast();
  const [editingInterval, setEditingInterval] = useState(false);
  const [intervalValue, setIntervalValue] = useState(
    entry.poll_interval?.toString() || "15"
  );

  const handleSync = () => {
    syncIntegration.mutate(entry.integration_id, {
      onSuccess: () => addToast("success", `${meta.label}-Sync gestartet`),
      onError: () => addToast("error", `${meta.label}-Sync fehlgeschlagen`),
    });
  };

  const handleSaveInterval = () => {
    updateSchedule.mutate(
      { integration_id: entry.integration_id, poll_interval: Number(intervalValue) },
      {
        onSuccess: () => {
          addToast("success", `Intervall auf ${intervalValue} Min. gesetzt`);
          setEditingInterval(false);
        },
      }
    );
  };

  const lastLog = entry.recent_logs[0];

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-lg ${meta.color} text-white font-bold`}
          >
            {meta.icon}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-900">{meta.label}</h4>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant={entry.sync_status === "idle" ? "success" : entry.sync_status === "syncing" ? "info" : "danger"}>
                {entry.sync_status === "idle" ? "Bereit" : entry.sync_status === "syncing" ? "Synchronisiert..." : "Fehler"}
              </Badge>
              <span className="text-xs text-gray-500">
                {entry.item_count} Element(e) importiert
              </span>
            </div>
          </div>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleSync}
          disabled={syncIntegration.isPending || entry.sync_status === "syncing"}
        >
          <ArrowPathIcon className="h-4 w-4" />
          Sync
        </Button>
      </div>

      {/* Letzter Sync */}
      <div className="mt-3 text-xs text-gray-500">
        {entry.last_synced_at ? (
          <span>
            Letzter Sync: {new Date(entry.last_synced_at).toLocaleString("de-DE")}
          </span>
        ) : (
          <span>Noch nie synchronisiert</span>
        )}
      </div>

      {/* Sync-Intervall */}
      <div className="mt-2 flex items-center gap-2">
        <ClockIcon className="h-4 w-4 text-gray-400" />
        {editingInterval ? (
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="1"
              max="120"
              value={intervalValue}
              onChange={(e) => setIntervalValue(e.target.value)}
              className="w-16 rounded border border-gray-300 px-2 py-1 text-xs"
            />
            <span className="text-xs text-gray-500">Min.</span>
            <Button variant="ghost" size="sm" onClick={handleSaveInterval}>
              Speichern
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setEditingInterval(false)}>
              Abbrechen
            </Button>
          </div>
        ) : (
          <button
            onClick={() => setEditingInterval(true)}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Intervall: {entry.poll_interval || "Standard"} Min.
          </button>
        )}
      </div>

      {/* Letzte Logs */}
      {entry.recent_logs.length > 0 && (
        <div className="mt-3 space-y-1">
          <p className="text-xs font-medium text-gray-500 uppercase">Letzte Syncs</p>
          {entry.recent_logs.slice(0, 3).map((log) => (
            <div key={log.id} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Badge
                  variant={log.status === "completed" ? "success" : log.status === "started" ? "info" : "danger"}
                >
                  {log.status === "completed" ? "OK" : log.status === "started" ? "..." : "Fehler"}
                </Badge>
                <span className="text-gray-500">
                  +{log.records_created} / ~{log.records_updated}
                </span>
              </div>
              <span className="text-gray-400">
                {log.started_at ? new Date(log.started_at).toLocaleString("de-DE", {
                  hour: "2-digit",
                  minute: "2-digit",
                  day: "2-digit",
                  month: "2-digit",
                }) : "–"}
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export function ImportDashboard() {
  const { data, isLoading } = useImportDashboard();
  const { data: conflictsData } = useGitHubConflicts();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const integrations = data?.integrations || [];
  const conflictCount = conflictsData?.count || 0;

  return (
    <div className="space-y-4">
      {/* Konflikt-Warnung */}
      {conflictCount > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
          <div>
            <p className="text-sm font-medium text-yellow-800">
              {conflictCount} Konflikt(e) erkannt
            </p>
            <p className="text-xs text-yellow-700">
              Issues wurden sowohl lokal als auch auf GitHub geändert.
            </p>
          </div>
        </div>
      )}

      {integrations.length === 0 ? (
        <div className="text-center py-8 text-sm text-gray-500">
          Keine aktiven Integrationen. Verbinde Jira, GitHub oder Confluence in den Einstellungen.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {integrations.map((entry) => (
            <IntegrationCard key={entry.integration_id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
