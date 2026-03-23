"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useProjects } from "@/hooks/useProjects";
import { statusLabels } from "@/lib/utils";
import Link from "next/link";
import { PlusIcon } from "@heroicons/react/24/outline";

export default function ProjektePage() {
  const { data, isLoading } = useProjects();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Projekte</h2>
        <Button>
          <PlusIcon className="h-4 w-4" />
          Neues Projekt
        </Button>
      </div>

      {isLoading ? (
        <p className="text-gray-500">Lade Projekte...</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.results?.map((project) => (
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
    </div>
  );
}
