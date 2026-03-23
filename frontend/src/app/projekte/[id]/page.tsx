"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useProject } from "@/hooks/useProjects";
import { useIssues, useProjectStats } from "@/hooks/useIssues";
import { useSprints } from "@/hooks/useSprints";
import { IssueTable } from "@/components/issues/IssueTable";
import { IssueDetailPanel } from "@/components/issues/IssueDetailPanel";
import { IssueCreateDialog } from "@/components/issues/IssueCreateDialog";
import { statusLabels, formatDate } from "@/lib/utils";
import type { Issue } from "@/lib/types";
import {
  PlusIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

type Tab = "overview" | "issues" | "sprints";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [selectedIssueId, setSelectedIssueId] = useState<number | null>(null);
  const [showCreateIssue, setShowCreateIssue] = useState(false);
  const [issueFilters, setIssueFilters] = useState<Record<string, string>>({});

  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: stats } = useProjectStats(projectId);
  const { data: issues, isLoading: issuesLoading } = useIssues(
    projectId,
    issueFilters
  );
  const { data: sprints } = useSprints(projectId);

  const tabs = [
    { key: "overview" as Tab, label: "Übersicht" },
    { key: "issues" as Tab, label: `Issues (${stats?.total || 0})` },
    { key: "sprints" as Tab, label: "Sprints" },
  ];

  if (projectLoading) {
    return <p className="text-gray-500">Lade Projekt...</p>;
  }

  if (!project) {
    return <p className="text-gray-500">Projekt nicht gefunden.</p>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
            <Badge variant={project.status === "active" ? "success" : "default"}>
              {statusLabels[project.status] || project.status}
            </Badge>
            {project.is_synced && <Badge variant="info">Jira Sync</Badge>}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {project.key} &middot; {project.issue_count} Issues
          </p>
        </div>
        <Button onClick={() => setShowCreateIssue(true)}>
          <PlusIcon className="h-4 w-4" />
          Neues Issue
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`border-b-2 pb-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-primary-600 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {project.description && (
            <Card title="Beschreibung">
              <p className="text-sm text-gray-700 whitespace-pre-line">
                {project.description}
              </p>
            </Card>
          )}

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <Card>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.total}
                  </p>
                  <p className="text-xs text-gray-500">Gesamt Issues</p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {stats.by_status?.done || 0}
                  </p>
                  <p className="text-xs text-gray-500">Erledigt</p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {stats.by_status?.in_progress || 0}
                  </p>
                  <p className="text-xs text-gray-500">In Bearbeitung</p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <p className="text-2xl font-bold text-red-600">
                    {stats.overdue_count}
                  </p>
                  <p className="text-xs text-gray-500">Überfällig</p>
                </div>
              </Card>
            </div>
          )}

          {/* Sprint Info */}
          {stats?.sprint_info && (
            <Card title={`Aktiver Sprint: ${stats.sprint_info.name}`}>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Fortschritt</span>
                  <span className="font-medium">
                    {stats.sprint_info.done_issues} / {stats.sprint_info.total_issues}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-gray-200">
                  <div
                    className="h-2 rounded-full bg-primary-600 transition-all"
                    style={{
                      width: `${
                        stats.sprint_info.total_issues
                          ? (stats.sprint_info.done_issues / stats.sprint_info.total_issues) * 100
                          : 0
                      }%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>
                    {stats.sprint_info.start_date
                      ? formatDate(stats.sprint_info.start_date)
                      : "—"}
                  </span>
                  <span>
                    {stats.sprint_info.end_date
                      ? formatDate(stats.sprint_info.end_date)
                      : "—"}
                  </span>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {activeTab === "issues" && (
        <div className="space-y-4">
          {/* Status-Filter */}
          <div className="flex items-center gap-2">
            {["", "to_do", "in_progress", "in_review", "done"].map((s) => (
              <button
                key={s}
                onClick={() =>
                  setIssueFilters(s ? { status: s } : {})
                }
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  (issueFilters.status || "") === s
                    ? "bg-primary-100 text-primary-700"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {s ? statusLabels[s] || s : "Alle"}
              </button>
            ))}
          </div>

          <Card>
            {issuesLoading ? (
              <p className="text-gray-500">Lade Issues...</p>
            ) : (
              <IssueTable
                issues={issues?.results || []}
                onIssueClick={(issue: Issue) => setSelectedIssueId(issue.id)}
              />
            )}
          </Card>
        </div>
      )}

      {activeTab === "sprints" && (
        <div className="space-y-4">
          {sprints?.results?.length ? (
            sprints.results.map((sprint) => (
              <Card key={sprint.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{sprint.name}</h4>
                    {sprint.goal && (
                      <p className="text-sm text-gray-500 mt-1">{sprint.goal}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      {sprint.start_date && (
                        <span>Start: {formatDate(sprint.start_date)}</span>
                      )}
                      {sprint.end_date && (
                        <span>Ende: {formatDate(sprint.end_date)}</span>
                      )}
                    </div>
                  </div>
                  <Badge
                    variant={
                      sprint.status === "active"
                        ? "success"
                        : sprint.status === "closed"
                        ? "default"
                        : "info"
                    }
                  >
                    {statusLabels[sprint.status] || sprint.status}
                  </Badge>
                </div>
              </Card>
            ))
          ) : (
            <p className="text-gray-500">Keine Sprints vorhanden.</p>
          )}
        </div>
      )}

      {/* Issue Detail Panel */}
      {selectedIssueId && (
        <IssueDetailPanel
          issueId={selectedIssueId}
          open={!!selectedIssueId}
          onClose={() => setSelectedIssueId(null)}
        />
      )}

      {/* Create Issue Dialog */}
      <IssueCreateDialog
        projectId={projectId}
        open={showCreateIssue}
        onClose={() => setShowCreateIssue(false)}
      />
    </div>
  );
}
