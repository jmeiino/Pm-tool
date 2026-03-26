"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAgentTasks, useAgentCompanyStatus } from "@/hooks/useAgents";
import { AgentTaskPanel } from "@/components/agents/AgentTaskPanel";
import { AgentOrgChart } from "@/components/agents/AgentOrgChart";
import type { AgentTask } from "@/lib/types";

const statusVariant: Record<string, "default" | "success" | "warning" | "danger" | "info"> = {
  pending: "default",
  assigned: "info",
  in_progress: "info",
  review: "warning",
  needs_input: "warning",
  completed: "success",
  failed: "danger",
  cancelled: "default",
};

export default function AgentsPage() {
  const { data: tasksData, isLoading: tasksLoading } = useAgentTasks();
  const { data: companyStatus } = useAgentCompanyStatus();
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);

  const tasks = tasksData?.results || [];
  const activeTasks = tasks.filter((t) =>
    ["assigned", "in_progress", "review", "needs_input"].includes(t.status)
  );
  const completedTasks = tasks.filter((t) =>
    ["completed", "failed", "cancelled"].includes(t.status)
  );

  if (selectedTaskId) {
    return (
      <div className="mx-auto max-w-6xl space-y-4">
        <button
          onClick={() => setSelectedTaskId(null)}
          className="text-sm text-brand hover:text-brand-deeper"
        >
          &larr; Zurück zur Übersicht
        </button>
        <AgentTaskPanel taskId={selectedTaskId} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agentische Firma</h1>
        <p className="mt-1 text-sm text-gray-500">
          Delegiere Aufgaben an AI-Agents und verfolge den Fortschritt in Echtzeit.
        </p>
      </div>

      {/* Status-Übersicht */}
      {companyStatus && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs font-medium text-gray-500">Aktive Aufgaben</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">
              {companyStatus.active_task_count}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs font-medium text-gray-500">Offene Rückfragen</p>
            <p className="mt-1 text-2xl font-bold text-yellow-600">
              {companyStatus.pending_decisions}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs font-medium text-gray-500">Agents</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">
              {companyStatus.agents.length}
            </p>
          </div>
        </div>
      )}

      {/* Org-Chart + Task-Liste nebeneinander */}
      <div className="flex gap-6">
        {/* Org-Chart */}
        {companyStatus && companyStatus.agents.length > 0 && (
          <div className="w-56 flex-shrink-0 rounded-lg border border-gray-200 bg-white p-3">
            <AgentOrgChart agents={companyStatus.agents} />
          </div>
        )}

        {/* Task-Liste */}
        <div className="flex-1 space-y-4">
          {tasksLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : tasks.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-300 py-12 text-center">
              <p className="text-sm text-gray-500">
                Noch keine Aufgaben delegiert. Öffne ein Issue und klicke &quot;An Agents delegieren&quot;.
              </p>
            </div>
          ) : (
            <>
              {/* Aktive Tasks */}
              {activeTasks.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Aktive Aufgaben</h3>
                  <div className="space-y-2">
                    {activeTasks.map((task) => (
                      <TaskCard key={task.id} task={task} onClick={() => setSelectedTaskId(task.id)} />
                    ))}
                  </div>
                </div>
              )}

              {/* Abgeschlossene Tasks */}
              {completedTasks.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Abgeschlossen</h3>
                  <div className="space-y-2">
                    {completedTasks.map((task) => (
                      <TaskCard key={task.id} task={task} onClick={() => setSelectedTaskId(task.id)} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function TaskCard({ task, onClick }: { task: AgentTask; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full rounded-lg border border-gray-200 bg-white p-4 text-left transition-colors hover:border-brand hover:bg-brand-muted/30"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-500">{task.issue_key}</span>
          <span className="text-sm font-medium text-gray-900">{task.issue_title}</span>
        </div>
        <div className="flex items-center gap-2">
          {task.pending_decisions > 0 && (
            <Badge variant="warning">{task.pending_decisions} Rückfrage(n)</Badge>
          )}
          <Badge variant={statusVariant[task.status] || "default"}>
            {task.status_display}
          </Badge>
        </div>
      </div>
      <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
        {task.assigned_agent_name && <span>→ {task.assigned_agent_name}</span>}
        <span>{task.message_count} Nachrichten</span>
        <span>{new Date(task.created_at).toLocaleDateString("de-DE")}</span>
      </div>
    </button>
  );
}
