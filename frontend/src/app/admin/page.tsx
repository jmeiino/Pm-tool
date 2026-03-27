"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAdminDashboard } from "@/hooks/useAdmin";

function StatCard({
  label,
  value,
  sub,
  variant = "default",
}: {
  label: string;
  value: number | string;
  sub?: string;
  variant?: "default" | "success" | "warning" | "danger" | "brand";
}) {
  return (
    <Card>
      <div className="text-sm font-medium text-inotec-muted">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-inotec-text">{value}</span>
        {sub && <Badge variant={variant}>{sub}</Badge>}
      </div>
    </Card>
  );
}

export default function AdminDashboardPage() {
  const { data, isLoading } = useAdminDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Admin Dashboard</h2>
          <p className="text-sm text-gray-500">
            Systemweite Statistiken und Kennzahlen
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <Skeleton className="h-4 w-24" />
              <Skeleton className="mt-2 h-8 w-16" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Admin Dashboard</h2>
        <p className="text-sm text-gray-500">
          Systemweite Statistiken und Kennzahlen
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Benutzer"
          value={data.users.active}
          sub={`${data.users.total} gesamt`}
          variant="brand"
        />
        <StatCard
          label="Projekte"
          value={data.projects.active}
          sub={`${data.projects.total} gesamt`}
          variant="brand"
        />
        <StatCard
          label="Offene Issues"
          value={data.issues.open}
          sub={`${data.issues.total} gesamt`}
          variant="info"
        />
        <StatCard
          label="Offene Aufgaben"
          value={data.todos.pending}
          sub={`${data.todos.total} gesamt`}
          variant="info"
        />
        <StatCard
          label="Integrationen aktiv"
          value={data.integrations.active}
          sub={
            data.integrations.error > 0
              ? `${data.integrations.error} Fehler`
              : "Keine Fehler"
          }
          variant={data.integrations.error > 0 ? "danger" : "success"}
        />
        <StatCard
          label="Sync-Fehler (24h)"
          value={data.sync.errors_24h}
          sub={data.sync.errors_24h === 0 ? "Alles OK" : "Achtung"}
          variant={data.sync.errors_24h === 0 ? "success" : "danger"}
        />
        <StatCard
          label="AI Tokens (30 Tage)"
          value={data.ai.tokens_30d.toLocaleString("de-DE")}
          sub={`${data.ai.results_30d} Anfragen`}
          variant="brand"
        />
        <StatCard
          label="Agent-Tasks"
          value={data.agents.active_tasks}
          sub={`${data.agents.total_tasks} gesamt`}
          variant="brand"
        />
      </div>
    </div>
  );
}
