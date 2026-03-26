"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  useRepoAnalyses,
  useCreateRepoAnalysis,
  useAnalyzeRepo,
} from "@/hooks/useGitHub";
import { formatDate } from "@/lib/utils";
import {
  CircleStackIcon,
  PlusIcon,
  SparklesIcon,
  StarIcon,
  CodeBracketIcon,
} from "@heroicons/react/24/outline";

export default function RepoAnalysesPage() {
  const { data: repos, isLoading } = useRepoAnalyses();
  const createRepo = useCreateRepoAnalysis();
  const analyzeRepo = useAnalyzeRepo();

  const [showAddForm, setShowAddForm] = useState(false);
  const [repoName, setRepoName] = useState("");

  const handleAdd = () => {
    if (!repoName.includes("/")) return;
    createRepo.mutate(repoName, {
      onSuccess: () => {
        setRepoName("");
        setShowAddForm(false);
      },
    });
  };

  const handleAnalyze = (id: number) => {
    analyzeRepo.mutate(id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Repository-Analyse
          </h2>
          <p className="text-sm text-gray-500">
            GitHub-Repositories per KI analysieren
          </p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <PlusIcon className="mr-1.5 h-4 w-4" />
          Repository hinzufuegen
        </Button>
      </div>

      {/* Add Repo Form */}
      {showAddForm && (
        <Card>
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Repository (owner/repo)
              </label>
              <input
                type="text"
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                placeholder="z.B. facebook/react"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
              />
            </div>
            <Button
              onClick={handleAdd}
              disabled={!repoName.includes("/") || createRepo.isPending}
            >
              {createRepo.isPending ? "Wird hinzugefuegt..." : "Hinzufuegen"}
            </Button>
          </div>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex gap-2">
        <Link
          href="/github"
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Aktivitaeten
        </Link>
        <Link
          href="/github/repos"
          className="rounded-lg bg-brand px-3 py-1.5 text-xs font-medium text-white"
        >
          Repository-Analyse
        </Link>
      </div>

      {/* Repo List */}
      {isLoading ? (
        <Card>
          <p className="text-gray-500">Lade Repositories...</p>
        </Card>
      ) : repos?.results?.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {repos.results.map((repo) => (
            <Link key={repo.id} href={`/github/repos/${repo.id}`}>
              <Card>
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <CircleStackIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                      <h3 className="text-sm font-semibold text-gray-900 truncate">
                        {repo.repo_full_name}
                      </h3>
                    </div>
                    {repo.ai_processed_at && (
                      <SparklesIcon className="h-4 w-4 text-amber-500 flex-shrink-0" />
                    )}
                  </div>

                  {repo.description && (
                    <p className="text-xs text-gray-500 line-clamp-2">
                      {repo.description}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-2">
                    {repo.primary_language && (
                      <Badge className="bg-blue-100 text-blue-700 text-[10px]">
                        {repo.primary_language}
                      </Badge>
                    )}
                    {repo.stars > 0 && (
                      <span className="flex items-center gap-0.5 text-[10px] text-gray-500">
                        <StarIcon className="h-3 w-3" />
                        {repo.stars}
                      </span>
                    )}
                  </div>

                  {repo.ai_summary ? (
                    <p className="text-xs text-gray-600 line-clamp-2">
                      {repo.ai_summary}
                    </p>
                  ) : (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={(e) => {
                        e.preventDefault();
                        handleAnalyze(repo.id);
                      }}
                      disabled={analyzeRepo.isPending}
                    >
                      <SparklesIcon className="mr-1 h-3.5 w-3.5" />
                      Analysieren
                    </Button>
                  )}

                  {repo.ai_processed_at && (
                    <p className="text-[10px] text-gray-400">
                      Analysiert am {formatDate(repo.ai_processed_at)}
                    </p>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<CodeBracketIcon className="h-12 w-12" />}
          title="Keine Repositories vorhanden"
          description="Fuege ein GitHub-Repository hinzu, um es per KI analysieren zu lassen."
        />
      )}
    </div>
  );
}
