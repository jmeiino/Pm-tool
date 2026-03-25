"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAgentTask, useAgentProfiles, useReplyToAgent, useCancelTask, useAgentTaskStream } from "@/hooks/useAgents";
import { useToast } from "@/components/ui/Toast";
import { AgentOrgChart } from "./AgentOrgChart";
import { AgentTimeline } from "./AgentTimeline";
import { AgentChatInput } from "./AgentChatInput";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface AgentTaskPanelProps {
  taskId: number;
}

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

export function AgentTaskPanel({ taskId }: AgentTaskPanelProps) {
  const { data: task, isLoading } = useAgentTask(taskId);
  const { data: profilesData } = useAgentProfiles();
  const replyMutation = useReplyToAgent(taskId);
  const cancelMutation = useCancelTask(taskId);
  const { addToast } = useToast();

  // SSE Live-Updates
  useAgentTaskStream(taskId, !!task);

  const agents = profilesData?.results || [];
  const messages = task?.messages || [];
  const isActive = task && !["completed", "failed", "cancelled"].includes(task.status);

  const handleSend = (content: string) => {
    replyMutation.mutate(
      { content },
      {
        onError: () => addToast("error", "Nachricht konnte nicht gesendet werden."),
      }
    );
  };

  const handleDecision = (messageId: number, option: string) => {
    replyMutation.mutate(
      { content: option, decision_option: option },
      {
        onSuccess: () => addToast("success", `Entscheidung "${option}" gesendet.`),
      }
    );
  };

  const handleCancel = () => {
    cancelMutation.mutate(undefined, {
      onSuccess: () => addToast("info", "Aufgabe abgebrochen."),
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!task) {
    return <p className="text-sm text-gray-500">Task nicht gefunden.</p>;
  }

  return (
    <div className="flex h-[calc(100vh-12rem)] rounded-lg border border-gray-200 bg-white overflow-hidden">
      {/* Linke Spalte: Org-Chart */}
      <div className="w-56 flex-shrink-0 overflow-y-auto border-r border-gray-200 p-3">
        <AgentOrgChart agents={agents} activeAgentId={task.assigned_agent} />
      </div>

      {/* Rechte Spalte: Timeline + Chat */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <div className="flex items-center gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                {task.issue_key}: {task.issue_title}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant={statusVariant[task.status] || "default"}>
                  {task.status_display}
                </Badge>
                {task.assigned_agent_name && (
                  <span className="text-xs text-gray-500">
                    → {task.assigned_agent_name}
                  </span>
                )}
                {task.pending_decisions > 0 && (
                  <Badge variant="warning">{task.pending_decisions} Rückfrage(n)</Badge>
                )}
              </div>
            </div>
          </div>
          {isActive && (
            <Button variant="ghost" size="sm" onClick={handleCancel}>
              <XMarkIcon className="h-4 w-4" />
              Abbrechen
            </Button>
          )}
        </div>

        {/* Timeline */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <p className="text-center text-sm text-gray-400 py-8">
              Noch keine Nachrichten...
            </p>
          ) : (
            <AgentTimeline messages={messages} onDecision={handleDecision} />
          )}
        </div>

        {/* Deliverables */}
        {task.deliverables.length > 0 && (
          <div className="border-t border-gray-200 px-4 py-2">
            <span className="text-xs font-medium text-gray-500">Ergebnisse:</span>
            <div className="mt-1 flex flex-wrap gap-2">
              {task.deliverables.map((d, i) => (
                <a
                  key={i}
                  href={d.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-green-200 hover:bg-green-100"
                >
                  {d.name || d.type}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Chat Input */}
        {isActive && (
          <AgentChatInput
            onSend={handleSend}
            disabled={replyMutation.isPending}
          />
        )}
      </div>
    </div>
  );
}
