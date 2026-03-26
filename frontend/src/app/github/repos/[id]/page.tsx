"use client";

import { use } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  useRepoAnalysis,
  useAnalyzeRepo,
  useCreateTodosFromRepo,
} from "@/hooks/useGitHub";
import { formatDate } from "@/lib/utils";
import {
  ArrowLeftIcon,
  SparklesIcon,
  StarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon,
  WrenchScrewdriverIcon,
  ClipboardDocumentListIcon,
  CodeBracketIcon,
} from "@heroicons/react/24/outline";

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-orange-100 text-orange-700",
  low: "bg-blue-100 text-blue-700",
};

export default function RepoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const repoId = Number(id);
  const { data: repo, isLoading } = useRepoAnalysis(repoId);
  const analyzeRepo = useAnalyzeRepo();
  const createTodos = useCreateTodosFromRepo();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!repo) {
    return <p className="text-gray-500">Repository nicht gefunden.</p>;
  }

  const totalBytes = Object.values(repo.languages).reduce(
    (sum, v) => sum + v,
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/github/repos"
          className="rounded-lg p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-gray-900">
            {repo.repo_full_name}
          </h2>
          {repo.description && (
            <p className="text-sm text-gray-500">{repo.description}</p>
          )}
        </div>
        <Button
          onClick={() => analyzeRepo.mutate(repoId)}
          disabled={analyzeRepo.isPending}
        >
          <SparklesIcon className="mr-1.5 h-4 w-4" />
          {analyzeRepo.isPending
            ? "Wird analysiert..."
            : repo.ai_processed_at
              ? "Erneut analysieren"
              : "Analysieren"}
        </Button>
      </div>

      {/* Metadata Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <div className="flex items-center gap-2">
            <CodeBracketIcon className="h-5 w-5 text-blue-500" />
            <div>
              <p className="text-xs text-gray-500">Sprache</p>
              <p className="text-sm font-semibold">
                {repo.primary_language || "—"}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-2">
            <StarIcon className="h-5 w-5 text-amber-500" />
            <div>
              <p className="text-xs text-gray-500">Sterne</p>
              <p className="text-sm font-semibold">{repo.stars}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-2">
            <CodeBracketIcon className="h-5 w-5 text-purple-500" />
            <div>
              <p className="text-xs text-gray-500">Forks</p>
              <p className="text-sm font-semibold">{repo.forks}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
            <div>
              <p className="text-xs text-gray-500">Offene Issues</p>
              <p className="text-sm font-semibold">{repo.open_issues_count}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Language Breakdown */}
      {totalBytes > 0 && (
        <Card title="Sprachen">
          <div className="flex h-3 overflow-hidden rounded-full bg-gray-100">
            {Object.entries(repo.languages)
              .sort(([, a], [, b]) => b - a)
              .map(([lang, bytes], i) => {
                const pct = (bytes / totalBytes) * 100;
                const colors = [
                  "bg-blue-500",
                  "bg-green-500",
                  "bg-yellow-500",
                  "bg-purple-500",
                  "bg-red-500",
                  "bg-indigo-500",
                  "bg-pink-500",
                  "bg-orange-500",
                ];
                return (
                  <div
                    key={lang}
                    className={`${colors[i % colors.length]}`}
                    style={{ width: `${pct}%` }}
                    title={`${lang}: ${pct.toFixed(1)}%`}
                  />
                );
              })}
          </div>
          <div className="mt-2 flex flex-wrap gap-3">
            {Object.entries(repo.languages)
              .sort(([, a], [, b]) => b - a)
              .map(([lang, bytes]) => (
                <span key={lang} className="text-xs text-gray-600">
                  {lang}{" "}
                  <span className="font-medium">
                    {((bytes / totalBytes) * 100).toFixed(1)}%
                  </span>
                </span>
              ))}
          </div>
        </Card>
      )}

      {/* Topics */}
      {repo.topics.length > 0 && (
        <Card title="Themen">
          <div className="flex flex-wrap gap-2">
            {repo.topics.map((topic) => (
              <Badge key={topic} className="bg-gray-100 text-gray-700">
                {topic}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* AI Analysis Section */}
      {repo.ai_processed_at ? (
        <>
          {/* AI Summary */}
          <Card title="KI-Zusammenfassung">
            <div className="flex items-start gap-2">
              <SparklesIcon className="mt-0.5 h-5 w-5 text-amber-500 flex-shrink-0" />
              <p className="text-sm text-gray-700">{repo.ai_summary}</p>
            </div>
            <p className="mt-2 text-[10px] text-gray-400">
              Analysiert am {formatDate(repo.ai_processed_at)}
            </p>
          </Card>

          {/* Tech Stack */}
          {repo.ai_tech_stack.length > 0 && (
            <Card title="Erkannter Tech-Stack">
              <div className="flex flex-wrap gap-2">
                {repo.ai_tech_stack.map((tech, i) => (
                  <Badge
                    key={i}
                    className="bg-indigo-100 text-indigo-700"
                  >
                    {tech}
                  </Badge>
                ))}
              </div>
            </Card>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Strengths */}
            {repo.ai_strengths.length > 0 && (
              <Card title="Staerken">
                <ul className="space-y-2">
                  {repo.ai_strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircleIcon className="mt-0.5 h-4 w-4 text-green-500 flex-shrink-0" />
                      <span className="text-gray-700">{s}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Improvements */}
            {repo.ai_improvements.length > 0 && (
              <Card title="Verbesserungsvorschlaege">
                <ul className="space-y-2">
                  {repo.ai_improvements.map((imp, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <LightBulbIcon className="mt-0.5 h-4 w-4 text-amber-500 flex-shrink-0" />
                      <span className="text-gray-700">{imp}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>

          {/* Action Items */}
          {repo.ai_action_items.length > 0 && (
            <Card
              title="Naechste Schritte"
              action={
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => createTodos.mutate(repoId)}
                  disabled={createTodos.isPending}
                >
                  <ClipboardDocumentListIcon className="mr-1 h-3.5 w-3.5" />
                  {createTodos.isPending
                    ? "Erstelle..."
                    : createTodos.isSuccess
                      ? `${createTodos.data?.count} Aufgaben erstellt`
                      : "Als Aufgaben erstellen"}
                </Button>
              }
            >
              <ul className="space-y-3">
                {repo.ai_action_items.map((item, i) => {
                  const action =
                    typeof item === "string" ? item : item.action;
                  const priority =
                    typeof item === "string" ? "medium" : item.priority;
                  const reasoning =
                    typeof item === "string" ? "" : item.reasoning;

                  return (
                    <li key={i} className="flex items-start gap-2">
                      <WrenchScrewdriverIcon className="mt-0.5 h-4 w-4 text-brand flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900">
                            {action}
                          </span>
                          <Badge
                            className={`text-[10px] ${PRIORITY_COLORS[priority] || PRIORITY_COLORS.medium}`}
                          >
                            {priority}
                          </Badge>
                        </div>
                        {reasoning && (
                          <p className="mt-0.5 text-xs text-gray-500">
                            {reasoning}
                          </p>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <div className="py-8 text-center">
            <SparklesIcon className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-sm text-gray-500">
              Noch keine KI-Analyse vorhanden. Klicke auf
              &ldquo;Analysieren&rdquo;, um das Repository zu analysieren.
            </p>
          </div>
        </Card>
      )}

      {/* Recent Commits */}
      {repo.recent_commits_summary && (
        <Card title="Letzte Commits">
          <pre className="whitespace-pre-wrap text-xs text-gray-600 font-mono">
            {repo.recent_commits_summary}
          </pre>
        </Card>
      )}
    </div>
  );
}
