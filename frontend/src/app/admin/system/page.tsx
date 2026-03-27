"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  useSystemHealth,
  useAdminIntegrations,
  useForceSync,
  useAdminSyncLogs,
} from "@/hooks/useAdmin";
import { formatDate } from "@/lib/utils";

const integrationTypeLabels: Record<string, string> = {
  jira: "Jira",
  confluence: "Confluence",
  github: "GitHub",
  microsoft_calendar: "Microsoft Kalender",
  microsoft_email: "Microsoft E-Mail",
  microsoft_teams: "Microsoft Teams",
  microsoft_todo: "Microsoft Todo",
};

const syncStatusVariant: Record<string, "success" | "warning" | "danger"> = {
  idle: "success",
  syncing: "warning",
  error: "danger",
};

function SystemHealthSection() {
  const { data, isLoading } = useSystemHealth();

  if (isLoading) {
    return (
      <Card title="Systemstatus">
        <div className="flex gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-32" />
          ))}
        </div>
      </Card>
    );
  }

  if (!data) return null;

  const services = [
    { name: "Datenbank", ...data.database },
    { name: "Redis", ...data.redis },
    { name: "Celery", ...data.celery },
  ];

  return (
    <Card title="Systemstatus">
      <div className="flex flex-wrap gap-6">
        {services.map((svc) => (
          <div key={svc.name} className="flex items-center gap-3">
            <div
              className={`h-3 w-3 rounded-full ${
                svc.status === "ok" ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <div>
              <div className="text-sm font-medium text-inotec-text">
                {svc.name}
              </div>
              <div className="text-xs text-inotec-muted">
                {svc.status === "ok"
                  ? "workers" in svc && svc.workers !== undefined
                    ? `OK (${svc.workers} Worker)`
                    : "OK"
                  : svc.detail || "Fehler"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function IntegrationsSection() {
  const { data, isLoading } = useAdminIntegrations();
  const forceSync = useForceSync();

  if (isLoading) {
    return (
      <Card title="Integrationen">
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  const integrations = data ?? [];

  return (
    <Card title="Integrationen">
      {integrations.length === 0 ? (
        <p className="text-sm text-inotec-muted">
          Keine Integrationen konfiguriert.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-xs font-semibold uppercase tracking-wide text-inotec-muted">
                <th className="px-3 py-2">Benutzer</th>
                <th className="px-3 py-2">Typ</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Letzter Sync</th>
                <th className="px-3 py-2">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {integrations.map((cfg) => (
                <tr
                  key={cfg.id}
                  className="border-b border-gray-100 hover:bg-surface-up"
                >
                  <td className="px-3 py-2 text-inotec-text">
                    {cfg.user_full_name}
                  </td>
                  <td className="px-3 py-2 text-inotec-body">
                    {integrationTypeLabels[cfg.integration_type] ??
                      cfg.integration_type}
                  </td>
                  <td className="px-3 py-2">
                    <Badge
                      variant={
                        syncStatusVariant[cfg.sync_status] ?? "default"
                      }
                    >
                      {cfg.sync_status === "idle"
                        ? "Bereit"
                        : cfg.sync_status === "syncing"
                          ? "Synchronisiert"
                          : "Fehler"}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-inotec-muted">
                    {cfg.last_synced_at
                      ? formatDate(cfg.last_synced_at)
                      : "Nie"}
                  </td>
                  <td className="px-3 py-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={
                        !cfg.is_enabled ||
                        cfg.sync_status === "syncing" ||
                        forceSync.isPending
                      }
                      onClick={() => forceSync.mutate(cfg.id)}
                    >
                      Sync erzwingen
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function SyncLogsSection() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const { data, isLoading } = useAdminSyncLogs(
    statusFilter ? { status: statusFilter } : undefined
  );

  const logStatusVariant: Record<string, "success" | "warning" | "danger"> = {
    completed: "success",
    started: "warning",
    failed: "danger",
  };

  return (
    <Card
      title="Sync-Protokoll"
      action={
        <select
          value={statusFilter ?? ""}
          onChange={(e) => setStatusFilter(e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs focus:border-brand focus:outline-none"
        >
          <option value="">Alle</option>
          <option value="completed">Erfolgreich</option>
          <option value="failed">Fehlgeschlagen</option>
          <option value="started">Gestartet</option>
        </select>
      }
    >
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      ) : (
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b border-gray-200 text-xs font-semibold uppercase tracking-wide text-inotec-muted">
                <th className="px-3 py-2">Benutzer</th>
                <th className="px-3 py-2">Typ</th>
                <th className="px-3 py-2">Richtung</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Datensaetze</th>
                <th className="px-3 py-2">Gestartet</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((log) => (
                <tr
                  key={log.id}
                  className="border-b border-gray-100 hover:bg-surface-up"
                >
                  <td className="px-3 py-2 text-inotec-text">
                    {log.username}
                  </td>
                  <td className="px-3 py-2 text-inotec-body">
                    {integrationTypeLabels[log.integration_type] ??
                      log.integration_type}
                  </td>
                  <td className="px-3 py-2 text-inotec-muted">
                    {log.direction}
                  </td>
                  <td className="px-3 py-2">
                    <Badge
                      variant={logStatusVariant[log.status] ?? "default"}
                    >
                      {log.status === "completed"
                        ? "OK"
                        : log.status === "failed"
                          ? "Fehler"
                          : "Laeuft"}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-inotec-body">
                    {log.records_processed} ({log.records_created} neu,{" "}
                    {log.records_updated} aktualisiert)
                  </td>
                  <td className="px-3 py-2 text-inotec-muted">
                    {formatDate(log.started_at)}
                  </td>
                </tr>
              ))}
              {(data ?? []).length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-6 text-center text-inotec-muted"
                  >
                    Keine Sync-Logs vorhanden.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

export default function SystemPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          System & Integrationen
        </h2>
        <p className="text-sm text-gray-500">
          Systemgesundheit, Integrations-Status und Sync-Protokolle
        </p>
      </div>

      <SystemHealthSection />
      <IntegrationsSection />
      <SyncLogsSection />
    </div>
  );
}
