"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useGitHubProjects } from "@/hooks/useGitHub";
import {
  RectangleStackIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from "@heroicons/react/24/outline";

export default function GitHubProjectsPage() {
  const { data, isLoading } = useGitHubProjects();
  const [expandedProject, setExpandedProject] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">GitHub Projects</h2>
        <p className="text-sm text-gray-500">
          Uebersicht ueber GitHub Projects v2 (read-only)
        </p>
      </div>

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
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Repository-Analyse
        </Link>
        <Link
          href="/github/projects"
          className="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white"
        >
          Projects
        </Link>
      </div>

      {/* Projects List */}
      <Card title={`Projects (${data?.projects?.length || 0})`}>
        {isLoading ? (
          <p className="text-gray-500">Lade GitHub Projects...</p>
        ) : data?.projects?.length ? (
          <div className="space-y-3">
            {data.projects.map((project) => {
              const isExpanded = expandedProject === project.id;
              const items = project.items?.nodes || [];
              const issueItems = items.filter((item) => item.content);

              return (
                <div
                  key={project.id}
                  className="rounded-lg border border-gray-200"
                >
                  <button
                    onClick={() =>
                      setExpandedProject(isExpanded ? null : project.id)
                    }
                    className="flex w-full items-center justify-between p-4 text-left hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <RectangleStackIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {project.title}
                        </p>
                        {project.shortDescription && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {project.shortDescription}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={
                          project.closed
                            ? "bg-gray-100 text-gray-600"
                            : "bg-green-100 text-green-700"
                        }
                      >
                        {project.closed ? "Geschlossen" : "Offen"}
                      </Badge>
                      <span className="text-xs text-gray-400">
                        {project.items?.totalCount || 0} Items
                      </span>
                      {isExpanded ? (
                        <ChevronDownIcon className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronRightIcon className="h-4 w-4 text-gray-400" />
                      )}
                    </div>
                  </button>

                  {isExpanded && issueItems.length > 0 && (
                    <div className="border-t border-gray-100 divide-y divide-gray-50">
                      {issueItems.map((item) => {
                        if (!item.content) return null;
                        const { content } = item;
                        return (
                          <div
                            key={item.id}
                            className="flex items-center gap-3 px-4 py-2.5"
                          >
                            <Badge
                              className={`text-[10px] ${
                                content.state === "OPEN"
                                  ? "bg-green-100 text-green-700"
                                  : content.state === "MERGED"
                                  ? "bg-purple-100 text-purple-700"
                                  : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              {content.state}
                            </Badge>
                            <a
                              href={content.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-gray-900 hover:text-primary-600 truncate"
                            >
                              {content.title}
                            </a>
                            {content.repository && (
                              <span className="text-[10px] text-gray-400 flex-shrink-0">
                                {content.repository.nameWithOwner}#
                                {content.number}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {isExpanded && issueItems.length === 0 && (
                    <div className="border-t border-gray-100 p-4">
                      <p className="text-sm text-gray-400 text-center">
                        Keine Items in diesem Project
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-sm text-gray-500">
              Keine GitHub Projects gefunden. Verbinde GitHub in den Einstellungen.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
