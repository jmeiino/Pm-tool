"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useIssue } from "@/hooks/useIssues";
import { statusLabels, formatDate } from "@/lib/utils";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { DelegateToAgentButton } from "./DelegateToAgentButton";
import { AgentDeliverables } from "./AgentDeliverables";

const priorityLabels: Record<string, string> = {
  highest: "Höchste",
  high: "Hoch",
  medium: "Mittel",
  low: "Niedrig",
  lowest: "Niedrigste",
};

const priorityColors: Record<string, string> = {
  highest: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-blue-100 text-blue-800",
  low: "bg-gray-100 text-gray-800",
  lowest: "bg-gray-50 text-gray-600",
};

interface IssueDetailPanelProps {
  issueId: number;
  open: boolean;
  onClose: () => void;
}

export function IssueDetailPanel({
  issueId,
  open,
  onClose,
}: IssueDetailPanelProps) {
  const { data: issue, isLoading } = useIssue(issueId);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30">
      <div className="w-full max-w-xl bg-white shadow-xl overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {issue?.key || "Lade..."}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="p-6">
            <p className="text-sm text-gray-500">Lade Issue-Details...</p>
          </div>
        ) : issue ? (
          <div className="p-6 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {issue.title}
              </h2>
              {issue.description && (
                <p className="mt-2 text-sm text-gray-600 whitespace-pre-line">
                  {issue.description}
                </p>
              )}
            </div>

            {/* Metadaten */}
            <div className="grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-4">
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <Badge>{statusLabels[issue.status] || issue.status}</Badge>
              </div>
              <div>
                <p className="text-xs text-gray-500">Priorität</p>
                <Badge className={priorityColors[issue.priority]}>
                  {priorityLabels[issue.priority] || issue.priority}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-gray-500">Story Points</p>
                <p className="text-sm font-medium">{issue.story_points ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Fällig</p>
                <p className="text-sm font-medium">
                  {issue.due_date ? formatDate(issue.due_date) : "—"}
                </p>
              </div>
            </div>

            {/* Labels */}
            {issue.labels?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Labels</p>
                <div className="flex flex-wrap gap-1">
                  {issue.labels.map((label) => (
                    <span
                      key={label.id}
                      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: label.color + "20",
                        color: label.color,
                      }}
                    >
                      {label.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Subtasks */}
            {issue.subtasks?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">
                  Unteraufgaben ({issue.subtasks.length})
                </p>
                <ul className="divide-y divide-gray-100 rounded-lg border">
                  {issue.subtasks.map((sub) => (
                    <li key={sub.id} className="flex items-center justify-between px-3 py-2">
                      <span className="text-sm text-gray-900">{sub.title}</span>
                      <Badge>{statusLabels[sub.status] || sub.status}</Badge>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI-Agent Delegation */}
            <div className="flex items-center justify-between rounded-lg border border-dashed border-gray-200 p-3">
              <span className="text-xs text-gray-500">AI-Agent</span>
              <DelegateToAgentButton
                issueId={issue.id}
                activeAgentTaskStatus={issue.agent_tasks?.[0]?.status}
              />
            </div>

            {/* Agent Deliverables */}
            {issue.agent_tasks?.[0]?.deliverables?.length > 0 && (
              <AgentDeliverables deliverables={issue.agent_tasks[0].deliverables} />
            )}

            {/* Kommentare */}
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">
                Kommentare ({issue.comments?.length || 0})
              </p>
              {issue.comments?.length ? (
                <div className="space-y-3">
                  {issue.comments.map((comment) => (
                    <div key={comment.id} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-700">
                          {comment.author_name}
                        </span>
                        <span className="text-xs text-gray-400">
                          {formatDate(comment.created_at)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 whitespace-pre-line">
                        {comment.body}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">Keine Kommentare.</p>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
