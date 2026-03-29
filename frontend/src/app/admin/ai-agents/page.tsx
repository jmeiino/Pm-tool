"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAIStats, useAgentOverview } from "@/hooks/useAdmin";

function AIStatsSection() {
  const { data, isLoading } = useAIStats();

  if (isLoading) {
    return (
      <Card title="AI-Nutzung (letzte 30 Tage)">
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <Card title="AI-Nutzung (letzte 30 Tage)">
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          <div>
            <div className="text-sm text-inotec-muted">Anfragen</div>
            <div className="text-xl font-bold text-inotec-text">
              {data.recent_30d.count}
            </div>
          </div>
          <div>
            <div className="text-sm text-inotec-muted">Tokens verbraucht</div>
            <div className="text-xl font-bold text-inotec-text">
              {data.recent_30d.tokens.toLocaleString("de-DE")}
            </div>
          </div>
          <div>
            <div className="text-sm text-inotec-muted">Gesamt (alle Zeit)</div>
            <div className="text-xl font-bold text-inotec-text">
              {data.total_tokens.toLocaleString("de-DE")}
            </div>
          </div>
          <div>
            <div className="text-sm text-inotec-muted">Cache gueltig</div>
            <div className="text-xl font-bold text-inotec-text">
              {data.cache.valid_entries}
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Nach Model">
          {data.by_model.length === 0 ? (
            <p className="text-sm text-inotec-muted">Keine Daten vorhanden.</p>
          ) : (
            <div className="space-y-3">
              {data.by_model.map((item) => (
                <div
                  key={item.model_used}
                  className="flex items-center justify-between"
                >
                  <div>
                    <span className="text-sm font-medium text-inotec-text">
                      {item.model_used || "Unbekannt"}
                    </span>
                    <span className="ml-2 text-xs text-inotec-muted">
                      {item.count} Anfragen
                    </span>
                  </div>
                  <span className="font-mono text-sm text-inotec-body">
                    {item.tokens.toLocaleString("de-DE")} Tokens
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Nach Typ">
          {data.by_type.length === 0 ? (
            <p className="text-sm text-inotec-muted">Keine Daten vorhanden.</p>
          ) : (
            <div className="space-y-3">
              {data.by_type.map((item) => (
                <div
                  key={item.result_type}
                  className="flex items-center justify-between"
                >
                  <div>
                    <span className="text-sm font-medium text-inotec-text">
                      {item.result_type}
                    </span>
                    <span className="ml-2 text-xs text-inotec-muted">
                      {item.count} Anfragen
                    </span>
                  </div>
                  <span className="font-mono text-sm text-inotec-body">
                    {item.tokens.toLocaleString("de-DE")} Tokens
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function AgentOverviewSection() {
  const { data, isLoading } = useAgentOverview();

  if (isLoading) {
    return (
      <Card title="Agent-Uebersicht">
        <Skeleton className="h-24 w-full" />
      </Card>
    );
  }

  if (!data) return null;

  const statusLabels: Record<string, string> = {
    pending: "Ausstehend",
    assigned: "Zugewiesen",
    in_progress: "In Bearbeitung",
    review: "Review",
    needs_input: "Eingabe noetig",
    completed: "Abgeschlossen",
    failed: "Fehlgeschlagen",
    cancelled: "Abgebrochen",
    idle: "Bereit",
    working: "Arbeitet",
    waiting: "Wartet",
    offline: "Offline",
  };

  const taskStatusVariant: Record<string, "success" | "warning" | "danger" | "info" | "brand" | "default"> = {
    completed: "success",
    in_progress: "brand",
    failed: "danger",
    cancelled: "default",
    pending: "warning",
    assigned: "info",
    review: "info",
    needs_input: "warning",
  };

  return (
    <div className="space-y-4">
      <Card title="Agent-Companies">
        {data.companies.length === 0 ? (
          <p className="text-sm text-inotec-muted">
            Keine Agent-Companies konfiguriert.
          </p>
        ) : (
          <div className="space-y-3">
            {data.companies.map((company) => (
              <div
                key={company.id}
                className="flex items-center justify-between rounded-md border border-gray-100 p-3"
              >
                <div>
                  <div className="text-sm font-medium text-inotec-text">
                    {company.name}
                  </div>
                  <div className="text-xs text-inotec-muted">
                    {company.user} &middot; {company.base_url}
                  </div>
                </div>
                <Badge variant={company.is_enabled ? "success" : "default"}>
                  {company.is_enabled ? "Aktiv" : "Inaktiv"}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title={`Tasks (${data.tasks.total} gesamt)`}>
          {Object.keys(data.tasks.by_status).length === 0 ? (
            <p className="text-sm text-inotec-muted">Keine Tasks vorhanden.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.tasks.by_status).map(
                ([taskStatus, count]) => (
                  <Badge
                    key={taskStatus}
                    variant={taskStatusVariant[taskStatus] ?? "default"}
                  >
                    {statusLabels[taskStatus] ?? taskStatus}: {count}
                  </Badge>
                )
              )}
            </div>
          )}
        </Card>

        <Card title={`Agents (${data.agents.total} gesamt)`}>
          {Object.keys(data.agents.by_status).length === 0 ? (
            <p className="text-sm text-inotec-muted">
              Keine Agents registriert.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.agents.by_status).map(
                ([agentStatus, count]) => (
                  <Badge
                    key={agentStatus}
                    variant={
                      agentStatus === "working"
                        ? "brand"
                        : agentStatus === "idle"
                          ? "success"
                          : agentStatus === "offline"
                            ? "danger"
                            : "warning"
                    }
                  >
                    {statusLabels[agentStatus] ?? agentStatus}: {count}
                  </Badge>
                )
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

export default function AIAgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">AI & Agents</h2>
        <p className="text-sm text-gray-500">
          AI-Nutzungsstatistiken und Agent-Uebersicht
        </p>
      </div>

      <AIStatsSection />
      <AgentOverviewSection />
    </div>
  );
}
