"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Pagination } from "@/components/ui/Pagination";
import { useGitActivities } from "@/hooks/useGitHub";
import { useProjects } from "@/hooks/useProjects";
import { formatDate } from "@/lib/utils";
import {
  CodeBracketIcon,
  ArrowsRightLeftIcon,
  CheckCircleIcon,
  XCircleIcon,
  FunnelIcon,
} from "@heroicons/react/24/outline";

const EVENT_TYPE_CONFIG: Record<
  string,
  { label: string; color: string; icon: typeof CodeBracketIcon }
> = {
  commit: { label: "Commit", color: "bg-gray-100 text-gray-700", icon: CodeBracketIcon },
  pr_opened: { label: "PR geöffnet", color: "bg-blue-100 text-blue-700", icon: ArrowsRightLeftIcon },
  pr_merged: { label: "PR gemerged", color: "bg-purple-100 text-purple-700", icon: CheckCircleIcon },
  pr_closed: { label: "PR geschlossen", color: "bg-red-100 text-red-700", icon: XCircleIcon },
};

const EVENT_FILTERS = [
  { value: "", label: "Alle" },
  { value: "commit", label: "Commits" },
  { value: "pr_opened", label: "PRs geöffnet" },
  { value: "pr_merged", label: "PRs gemerged" },
  { value: "pr_closed", label: "PRs geschlossen" },
];

export default function GitHubPage() {
  const [eventFilter, setEventFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState<number | undefined>();
  const [page, setPage] = useState(1);

  const { data: activities, isLoading } = useGitActivities({
    event_type: eventFilter || undefined,
    project: projectFilter,
  });
  const { data: projects } = useProjects();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">GitHub</h2>
          <p className="text-sm text-gray-500">
            Commits, Pull Requests und Code-Aktivität
          </p>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-2">
        <Link
          href="/github"
          className="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white"
        >
          Aktivitaeten
        </Link>
        <Link
          href="/github/repos"
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Repository-Analyse
        </Link>
      </div>

      {/* Statistik */}
      {activities && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Object.entries(EVENT_TYPE_CONFIG).map(([type, config]) => {
            const count =
              activities.results?.filter((a) => a.event_type === type).length || 0;
            const Icon = config.icon;
            return (
              <Card key={type}>
                <div className="flex items-center gap-3">
                  <div className={`rounded-lg p-2 ${config.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">{config.label}</p>
                    <p className="text-xl font-bold text-gray-900">{count}</p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Filter */}
      <div className="flex flex-wrap items-center gap-3">
        <FunnelIcon className="h-4 w-4 text-gray-400" />
        {/* Event Type Filter */}
        <div className="flex rounded-lg border border-gray-300 overflow-hidden">
          {EVENT_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => {
                setEventFilter(f.value);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                eventFilter === f.value
                  ? "bg-primary-600 text-white"
                  : "bg-white text-gray-700 hover:bg-gray-50"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Project Filter */}
        {projects?.results && projects.results.length > 0 && (
          <select
            value={projectFilter || ""}
            onChange={(e) => {
              setProjectFilter(
                e.target.value ? Number(e.target.value) : undefined
              );
              setPage(1);
            }}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs focus:border-primary-500 focus:outline-none"
          >
            <option value="">Alle Projekte</option>
            {projects.results.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Aktivitäten-Liste */}
      <Card title={`Aktivitäten (${activities?.count || 0})`}>
        {isLoading ? (
          <p className="text-gray-500">Lade Aktivitäten...</p>
        ) : activities?.results?.length ? (
          <div className="divide-y divide-gray-100">
            {activities.results.map((activity) => {
              const config = EVENT_TYPE_CONFIG[activity.event_type] || {
                label: activity.event_type,
                color: "bg-gray-100 text-gray-600",
                icon: CodeBracketIcon,
              };
              const Icon = config.icon;

              return (
                <div
                  key={activity.id}
                  className="flex items-start gap-3 py-3"
                >
                  <div
                    className={`mt-0.5 flex-shrink-0 rounded-lg p-1.5 ${config.color}`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {activity.url ? (
                        <a
                          href={activity.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-gray-900 hover:text-primary-600 truncate"
                        >
                          {activity.title}
                        </a>
                      ) : (
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {activity.title}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-500">
                        {activity.author}
                      </span>
                      <span className="text-gray-300">·</span>
                      <span className="text-xs text-gray-400">
                        {formatDate(activity.event_date)}
                      </span>
                      <Badge className={`${config.color} text-[10px]`}>
                        {config.label}
                      </Badge>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <CodeBracketIcon className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-sm text-gray-500">
              Keine Git-Aktivitäten vorhanden. Verbinde GitHub in den
              Einstellungen.
            </p>
          </div>
        )}

        {activities && activities.count > 25 && (
          <Pagination
            count={activities.count}
            currentPage={page}
            onPageChange={setPage}
          />
        )}
      </Card>
    </div>
  );
}
