"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useJiraPreview, useJiraConfirmImport } from "@/hooks/useImport";
import { useImportWizardStore } from "@/stores/useImportWizardStore";
import { ImportConfirmDialog } from "./ImportConfirmDialog";
import { ImportResultSummary } from "./ImportResultSummary";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/outline";
import type { JiraPreviewIssue, ImportConfirmResponse } from "@/lib/types";

export function JiraImportStep() {
  const { data, isLoading, error } = useJiraPreview();
  const confirmImport = useJiraConfirmImport();
  const store = useImportWizardStore();
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [showConfirm, setShowConfirm] = useState(false);
  const [importResult, setImportResult] = useState<ImportConfirmResponse | null>(null);

  const toggleExpand = (key: string) => {
    const next = new Set(expandedProjects);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setExpandedProjects(next);
  };

  // Gefilterte Issues pro Projekt
  const filteredIssuesMap = useMemo(() => {
    if (!data) return {};
    const map: Record<string, JiraPreviewIssue[]> = {};
    for (const project of data.projects) {
      map[project.jira_id] = project.issues.filter((issue) => {
        if (store.jiraFilters.assignee && issue.assignee !== store.jiraFilters.assignee)
          return false;
        if (store.jiraFilters.status && issue.status !== store.jiraFilters.status)
          return false;
        if (store.jiraFilters.sprint && issue.sprint !== store.jiraFilters.sprint)
          return false;
        return true;
      });
    }
    return map;
  }, [data, store.jiraFilters]);

  const handleConfirm = () => {
    if (!data) return;
    const projects = data.projects
      .filter((p) => store.jiraSelectedProjects.has(p.jira_id))
      .map((p) => ({
        jira_project_id: p.jira_id,
        jira_project_key: p.key,
        name: p.name,
        issue_ids: (filteredIssuesMap[p.jira_id] || [])
          .filter((i) => store.jiraSelectedIssues.has(i.jira_id))
          .map((i) => i.jira_id),
      }));

    confirmImport.mutate(projects, {
      onSuccess: (result) => {
        setImportResult(result);
        setShowConfirm(false);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Fehler beim Laden der Jira-Daten: {(error as Error).message}
      </div>
    );
  }

  if (importResult) {
    return <ImportResultSummary result={importResult} onDismiss={() => setImportResult(null)} />;
  }

  const selectedCount = store.jiraSelectedProjects.size;
  const selectedIssueCount = store.jiraSelectedIssues.size;

  return (
    <div className="space-y-4">
      {/* Filter-Leiste */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <span className="text-xs font-medium text-gray-500 uppercase">Filter:</span>
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={store.jiraFilters.assignee}
          onChange={(e) => store.setJiraFilter("assignee", e.target.value)}
        >
          <option value="">Alle Bearbeiter</option>
          {data?.available_assignees.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={store.jiraFilters.status}
          onChange={(e) => store.setJiraFilter("status", e.target.value)}
        >
          <option value="">Alle Status</option>
          {data?.available_statuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={store.jiraFilters.sprint}
          onChange={(e) => store.setJiraFilter("sprint", e.target.value)}
        >
          <option value="">Alle Sprints</option>
          {data?.available_sprints.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Projekt-Liste */}
      <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data?.projects.map((project) => {
          const isSelected = store.jiraSelectedProjects.has(project.jira_id);
          const isExpanded = expandedProjects.has(project.jira_id);
          const filteredIssues = filteredIssuesMap[project.jira_id] || [];

          return (
            <div key={project.jira_id}>
              <div className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {
                    store.toggleJiraProject(project.jira_id);
                    // Alle gefilterten Issues des Projekts selektieren/deselektieren
                    const issueIds = filteredIssues.map((i) => i.jira_id);
                    if (!isSelected) {
                      store.selectAllJiraIssues(issueIds);
                    } else {
                      store.deselectAllJiraIssues(issueIds);
                    }
                  }}
                  className="h-4 w-4 rounded border-gray-300 text-primary-600"
                />
                <button
                  onClick={() => toggleExpand(project.jira_id)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {isExpanded ? (
                    <ChevronDownIcon className="h-4 w-4" />
                  ) : (
                    <ChevronRightIcon className="h-4 w-4" />
                  )}
                </button>
                <div className="flex-1">
                  <span className="font-medium text-gray-900">{project.name}</span>
                  <span className="ml-2 text-xs text-gray-500">{project.key}</span>
                </div>
                <Badge>{filteredIssues.length} Issues</Badge>
              </div>

              {isExpanded && (
                <div className="border-t border-gray-100 bg-gray-50">
                  {filteredIssues.length === 0 ? (
                    <p className="px-12 py-3 text-sm text-gray-500">
                      Keine Issues mit den aktuellen Filtern.
                    </p>
                  ) : (
                    filteredIssues.map((issue) => (
                      <div
                        key={issue.jira_id}
                        className="flex items-center gap-3 px-12 py-2 hover:bg-gray-100"
                      >
                        <input
                          type="checkbox"
                          checked={store.jiraSelectedIssues.has(issue.jira_id)}
                          onChange={() => store.toggleJiraIssue(issue.jira_id)}
                          className="h-4 w-4 rounded border-gray-300 text-primary-600"
                        />
                        <span className="text-xs font-mono text-gray-500">{issue.key}</span>
                        <span className="flex-1 text-sm text-gray-700">{issue.summary}</span>
                        {issue.status && (
                          <Badge variant="info">{issue.status}</Badge>
                        )}
                        {issue.assignee && (
                          <span className="text-xs text-gray-500">{issue.assignee}</span>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Aktions-Leiste */}
      <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
        <span className="text-sm text-gray-600">
          {selectedCount} Projekt(e), {selectedIssueCount} Issue(s) ausgewählt
        </span>
        <Button
          onClick={() => setShowConfirm(true)}
          disabled={selectedCount === 0}
        >
          Importieren
        </Button>
      </div>

      <ImportConfirmDialog
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleConfirm}
        title="Jira-Import bestätigen"
        summary={[
          `${selectedCount} Projekt(e) werden importiert.`,
          `${selectedIssueCount} Issue(s) werden synchronisiert.`,
        ]}
        isPending={confirmImport.isPending}
      />
    </div>
  );
}
