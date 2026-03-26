"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useGitHubPreview, useGitHubConfirmImport } from "@/hooks/useImport";
import { useProjects } from "@/hooks/useProjects";
import { useImportWizardStore } from "@/stores/useImportWizardStore";
import { ImportConfirmDialog } from "./ImportConfirmDialog";
import { useToast } from "@/components/ui/Toast";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/outline";

export function GitHubImportStep() {
  const store = useImportWizardStore();
  const { data, isLoading, error } = useGitHubPreview(store.githubMineOnly);
  const { data: projectsData } = useProjects();
  const confirmImport = useGitHubConfirmImport();
  const { addToast } = useToast();
  const [expandedRepos, setExpandedRepos] = useState<Set<string>>(new Set());
  const [showConfirm, setShowConfirm] = useState(false);

  const projects = projectsData?.results || [];

  const toggleExpand = (name: string) => {
    const next = new Set(expandedRepos);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setExpandedRepos(next);
  };

  const handleConfirm = () => {
    if (!data) return;
    const repos = data.repos
      .filter((r) => store.githubSelectedRepos.has(r.full_name))
      .map((r) => {
        const target = store.githubRepoTargets[r.full_name] || { createNew: true };
        const repoName = r.full_name.split("/").pop() || r.full_name;
        const selectedIssues = store.githubSelectedIssues[r.full_name];
        return {
          full_name: r.full_name,
          create_new_project: target.createNew,
          target_project_id: target.existingProjectId || null,
          project_name: target.projectName || repoName,
          selected_issue_ids: selectedIssues ? Array.from(selectedIssues) : [],
        };
      });

    confirmImport.mutate(repos, {
      onSuccess: (result) => {
        addToast("success", `GitHub-Import: ${result.detail}`);
        setShowConfirm(false);
      },
      onError: (err) => {
        addToast("error", `GitHub-Import fehlgeschlagen: ${(err as Error).message}`);
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
        Fehler beim Laden der GitHub-Daten: {(error as Error).message}
      </div>
    );
  }

  const selectedCount = store.githubSelectedRepos.size;

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={store.githubMineOnly}
            onChange={(e) => store.setGitHubMineOnly(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-brand"
          />
          Nur meine Daten
        </label>
        {data?.github_username && (
          <Badge variant="info">@{data.github_username}</Badge>
        )}
      </div>

      {/* Repo-Liste */}
      <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data?.repos.map((repo) => {
          const isSelected = store.githubSelectedRepos.has(repo.full_name);
          const isExpanded = expandedRepos.has(repo.full_name);
          const target = store.githubRepoTargets[repo.full_name] || { createNew: true };

          return (
            <div key={repo.full_name}>
              <div className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => store.toggleGitHubRepo(repo.full_name)}
                  className="h-4 w-4 rounded border-gray-300 text-brand"
                />
                <button
                  onClick={() => toggleExpand(repo.full_name)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {isExpanded ? (
                    <ChevronDownIcon className="h-4 w-4" />
                  ) : (
                    <ChevronRightIcon className="h-4 w-4" />
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <span className="font-medium text-gray-900">{repo.full_name}</span>
                  {repo.description && (
                    <p className="truncate text-xs text-gray-500">{repo.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {repo.language && <Badge>{repo.language}</Badge>}
                  <Badge variant="info">{repo.issues.length} Issues</Badge>
                </div>
              </div>

              {isExpanded && isSelected && (
                <div className="border-t border-gray-100 bg-gray-50 p-4 space-y-3">
                  {/* Ziel-Projekt Auswahl */}
                  <div className="flex items-center gap-3">
                    <label className="text-sm font-medium text-gray-700">Ziel:</label>
                    <select
                      className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
                      value={target.createNew ? "new" : String(target.existingProjectId || "")}
                      onChange={(e) => {
                        if (e.target.value === "new") {
                          store.setGitHubRepoTarget(repo.full_name, { createNew: true });
                        } else {
                          store.setGitHubRepoTarget(repo.full_name, {
                            createNew: false,
                            existingProjectId: Number(e.target.value),
                          });
                        }
                      }}
                    >
                      <option value="new">Neues Projekt erstellen</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.key})
                        </option>
                      ))}
                    </select>
                    {target.createNew && (
                      <input
                        type="text"
                        placeholder="Projektname"
                        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
                        value={target.projectName || repo.full_name.split("/").pop() || ""}
                        onChange={(e) =>
                          store.setGitHubRepoTarget(repo.full_name, {
                            ...target,
                            projectName: e.target.value,
                          })
                        }
                      />
                    )}
                  </div>

                  {/* Issues */}
                  {repo.issues.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-gray-500 uppercase">Issues</p>
                      {repo.issues.map((issue) => {
                        const repoIssues = store.githubSelectedIssues[repo.full_name];
                        const isIssueSelected = repoIssues?.has(issue.github_id) || false;
                        return (
                          <div
                            key={issue.github_id}
                            className="flex items-center gap-3 rounded px-2 py-1.5 hover:bg-gray-100"
                          >
                            <input
                              type="checkbox"
                              checked={isIssueSelected}
                              onChange={() =>
                                store.toggleGitHubIssue(repo.full_name, issue.github_id)
                              }
                              className="h-4 w-4 rounded border-gray-300 text-brand"
                            />
                            <span className="text-xs font-mono text-gray-500">#{issue.number}</span>
                            <span className="flex-1 text-sm text-gray-700">{issue.title}</span>
                            <Badge variant={issue.state === "open" ? "success" : "default"}>
                              {issue.state}
                            </Badge>
                            {issue.assignee && (
                              <span className="text-xs text-gray-500">@{issue.assignee}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
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
          {selectedCount} Repository(s) ausgewählt
        </span>
        <Button onClick={() => setShowConfirm(true)} disabled={selectedCount === 0}>
          Importieren
        </Button>
      </div>

      <ImportConfirmDialog
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleConfirm}
        title="GitHub-Import bestätigen"
        summary={[`${selectedCount} Repository(s) werden importiert.`]}
        isPending={confirmImport.isPending}
      />
    </div>
  );
}
