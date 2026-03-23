"use client";

import { Badge } from "@/components/ui/Badge";
import type { Issue } from "@/lib/types";
import { priorityColors, statusLabels, formatDate } from "@/lib/utils";

const issueTypeLabels: Record<string, string> = {
  epic: "Epic",
  story: "Story",
  task: "Aufgabe",
  bug: "Bug",
  subtask: "Unteraufgabe",
};

const priorityLabels: Record<string, string> = {
  highest: "Höchste",
  high: "Hoch",
  medium: "Mittel",
  low: "Niedrig",
  lowest: "Niedrigste",
};

const priorityBadgeColors: Record<string, string> = {
  highest: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-blue-100 text-blue-800",
  low: "bg-gray-100 text-gray-800",
  lowest: "bg-gray-50 text-gray-600",
};

interface IssueTableProps {
  issues: Issue[];
  onIssueClick?: (issue: Issue) => void;
}

export function IssueTable({ issues, onIssueClick }: IssueTableProps) {
  if (issues.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        Keine Issues gefunden.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Key
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Titel
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Typ
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Priorität
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Zugewiesen
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              Fällig
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {issues.map((issue) => (
            <tr
              key={issue.id}
              onClick={() => onIssueClick?.(issue)}
              className="cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <td className="whitespace-nowrap px-4 py-3 text-xs font-mono text-gray-500">
                {issue.key}
              </td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900 max-w-xs truncate">
                {issue.title}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {issueTypeLabels[issue.issue_type] || issue.issue_type}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <Badge>{statusLabels[issue.status] || issue.status}</Badge>
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <Badge className={priorityBadgeColors[issue.priority]}>
                  {priorityLabels[issue.priority] || issue.priority}
                </Badge>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {issue.assignee_name || "—"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {issue.due_date ? formatDate(issue.due_date) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
