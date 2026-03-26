"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useJiraPreview, useJiraProjectIssues, useJiraConfirmImport } from "@/hooks/useImport";
import { useImportWizardStore } from "@/stores/useImportWizardStore";
import { useToast } from "@/components/ui/Toast";
import { ImportConfirmDialog } from "./ImportConfirmDialog";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/outline";
import type { JiraPreviewIssue, ImportConfirmResponse } from "@/lib/types";

function ProjectIssues({ projectKey, projectId }: { projectKey: string; projectId: string }) {
  const { data, isLoading } = useJiraProjectIssues(projectKey);
  const store = useImportWizardStore();

  const filteredIssues = useMemo(() => {
    if (!data?.projects?.[0]?.issues) return [];
    return data.projects[0].issues.filter((issue: JiraPreviewIssue) => {
      if (store.jiraFilters.assignee && issue.assignee !== store.jiraFilters.assignee)
        return false;
      if (store.jiraFilters.status && issue.status !== store.jiraFilters.status)
        return false;
      if (store.jiraFilters.sprint && issue.sprint !== store.jiraFilters.sprint)
        return false;
      return true;
    });
  }, [data, store.jiraFilters]);

  // Filter-Werte aus geladenen Issues extrahieren
  const filterValues = useMemo(() => {
    if (!data?.projects?.[0]?.issues) return { assignees: [], statuses: [], sprints: [] };
    const issues = data.projects[0].issues;
    return {
      assignees: [...new Set(issues.map((i: JiraPreviewIssue) => i.assignee).filter(Boolean))] as string[],
      statuses: [...new Set(issues.map((i: JiraPreviewIssue) => i.status).filter(Boolean))] as string[],
      sprints: [...new Set(issues.map((i: JiraPreviewIssue) => i.sprint).filter(Boolean))] as string[],
    };
  }, [data]);

  if (isLoading) {
    return (
      <div className="border-t border-gray-100 bg-gray-50 p-4">
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  return (
    <div className="border-t border-gray-100 bg-gray-50">
      {/* Inline-Filter für dieses Projekt */}
      {filterValues.assignees.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 px-12 py-2 border-b border-gray-100">
          <select
            className="rounded border border-gray-300 px-2 py-1 text-xs"
            value={store.jiraFilters.assignee}
            onChange={(e) => store.setJiraFilter("assignee", e.target.value)}
          >
            <option value="">Alle Bearbeiter</option>
            {filterValues.assignees.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <select
            className="rounded border border-gray-300 px-2 py-1 text-xs"
            value={store.jiraFilters.status}
            onChange={(e) => store.setJiraFilter("status", e.target.value)}
          >
            <option value="">Alle Status</option>
            {filterValues.statuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            className="rounded border border-gray-300 px-2 py-1 text-xs"
            value={store.jiraFilters.sprint}
            onChange={(e) => store.setJiraFilter("sprint", e.target.value)}
          >
            <option value="">Alle Sprints</option>
            {filterValues.sprints.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              const ids = filteredIssues.map((i: JiraPreviewIssue) => i.jira_id);
              store.selectAllJiraIssues(ids);
            }}
          >
            Alle auswählen
          </Button>
        </div>
      )}

      {filteredIssues.length === 0 ? (
        <p className="px-12 py-3 text-sm text-gray-500">
          Keine Issues mit den aktuellen Filtern.
        </p>
      ) : (
        filteredIssues.map((issue: JiraPreviewIssue) => (
          <div
            key={issue.jira_id}
            className="flex items-center gap-3 px-12 py-2 hover:bg-gray-100"
          >
            <input
              type="checkbox"
              checked={store.jiraSelectedIssues.has(issue.jira_id)}
              onChange={() => store.toggleJiraIssue(issue.jira_id)}
              className="h-4 w-4 rounded border-gray-300 text-brand"
            />
            <span className="text-xs font-mono text-gray-500">{issue.key}</span>
            <span className="flex-1 text-sm text-gray-700">{issue.summary}</span>
            {issue.status && <Badge variant="info">{issue.status}</Badge>}
            {issue.assignee && (
              <span className="text-xs text-gray-500">{issue.assignee}</span>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export function JiraImportStep() {
  const { data, isLoading, error } = useJiraPreview();
  const confirmImport = useJiraConfirmImport();
  const store = useImportWizardStore();
  const { addToast } = useToast();
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [showConfirm, setShowConfirm] = useState(false);

  const toggleExpand = (key: string) => {
    const next = new Set(expandedProjects);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setExpandedProjects(next);
  };

  const handleConfirm = () => {
    if (!data) return;
    const projects = data.projects
      .filter((p) => store.jiraSelectedProjects.has(p.jira_id))
      .map((p) => ({
        jira_project_id: p.jira_id,
        jira_project_key: p.key,
        name: p.name,
        issue_ids: Array.from(store.jiraSelectedIssues),
      }));

    confirmImport.mutate(projects, {
      onSuccess: (result) => {
        addToast("success", `Jira-Import: ${result.detail}`);
        setShowConfirm(false);
      },
      onError: (err) => {
        addToast("error", `Jira-Import fehlgeschlagen: ${(err as Error).message}`);
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

  const selectedCount = store.jiraSelectedProjects.size;
  const selectedIssueCount = store.jiraSelectedIssues.size;

  return (
    <div className="space-y-4">
      {/* Projekt-Liste */}
      <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data?.projects.map((project) => {
          const isSelected = store.jiraSelectedProjects.has(project.jira_id);
          const isExpanded = expandedProjects.has(project.jira_id);

          return (
            <div key={project.jira_id}>
              <div className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => store.toggleJiraProject(project.jira_id)}
                  className="h-4 w-4 rounded border-gray-300 text-brand"
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
                <span className="text-xs text-gray-400">
                  Aufklappen um Issues zu laden
                </span>
              </div>

              {/* Lazy Loading: Issues werden erst beim Aufklappen geladen */}
              {isExpanded && (
                <ProjectIssues projectKey={project.key} projectId={project.jira_id} />
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
