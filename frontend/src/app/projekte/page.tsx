"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useProjects } from "@/hooks/useProjects";
import { ProjectCreateDialog } from "@/components/projects/ProjectCreateDialog";
import { statusLabels } from "@/lib/utils";
import Link from "next/link";
import { PlusIcon } from "@heroicons/react/24/outline";

const statusFilters = [
  { value: "", label: "Alle" },
  { value: "active", label: "Aktiv" },
  { value: "paused", label: "Pausiert" },
  { value: "archived", label: "Archiviert" },
];

export default function ProjektePage() {
  const { data, isLoading } = useProjects();
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");

  const filteredProjects = data?.results?.filter(
    (p) => !statusFilter || p.status === statusFilter
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Projekte</h2>
        <Button onClick={() => setShowCreate(true)}>
          <PlusIcon className="h-4 w-4" />
          Neues Projekt
        </Button>
      </div>

      {/* Status Filter */}
      <div className="flex items-center gap-2">
        {statusFilters.map((filter) => (
          <button
            key={filter.value}
            onClick={() => setStatusFilter(filter.value)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === filter.value
                ? "bg-primary-100 text-primary-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-gray-500">Lade Projekte...</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects?.map((project) => (
            <Link key={project.id} href={`/projekte/${project.id}`}>
              <Card className="hover:border-primary-300 transition-colors cursor-pointer">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-gray-500">
                      {project.key}
                    </span>
                    <Badge variant={project.status === "active" ? "success" : "default"}>
                      {statusLabels[project.status] || project.status}
                    </Badge>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {project.name}
                  </h3>
                  {project.description && (
                    <p className="text-sm text-gray-500 line-clamp-2">
                      {project.description}
                    </p>
                  )}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{project.issue_count} Issues</span>
                    {project.is_synced && (
                      <Badge variant="info">Jira Sync</Badge>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <ProjectCreateDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
