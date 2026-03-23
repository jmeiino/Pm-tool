"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useProjects } from "@/hooks/useProjects";
import { useTodos } from "@/hooks/useTodos";
import { useNotifications } from "@/hooks/useNotifications";
import {
  priorityLabels,
  priorityColors,
  statusLabels,
  formatDate,
} from "@/lib/utils";
import {
  SparklesIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  FolderIcon,
} from "@heroicons/react/24/outline";

export default function DashboardPage() {
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const { data: todos, isLoading: todosLoading } = useTodos({
    status: "pending",
  });
  const { data: notifications } = useNotifications();

  const today = new Date().toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500">{today}</p>
        </div>
        <Button>
          <SparklesIcon className="h-4 w-4" />
          KI-Tagesplan erstellen
        </Button>
      </div>

      {/* Statistik-Karten */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-50 p-2">
              <CheckCircleIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Offene Aufgaben</p>
              <p className="text-2xl font-bold text-gray-900">
                {todosLoading ? "..." : todos?.count || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-purple-50 p-2">
              <FolderIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Aktive Projekte</p>
              <p className="text-2xl font-bold text-gray-900">
                {projectsLoading ? "..." : projects?.count || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-orange-50 p-2">
              <ClockIcon className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Heute geplant</p>
              <p className="text-2xl font-bold text-gray-900">0</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-red-50 p-2">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Benachrichtigungen</p>
              <p className="text-2xl font-bold text-gray-900">
                {notifications?.count || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Tages-To-Dos */}
        <Card title="Heutige Aufgaben" className="lg:col-span-2">
          {todosLoading ? (
            <p className="text-sm text-gray-500">Lade Aufgaben...</p>
          ) : todos?.results?.length ? (
            <ul className="divide-y divide-gray-100">
              {todos.results.slice(0, 8).map((todo) => (
                <li key={todo.id} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-gray-300 text-primary-600"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {todo.title}
                      </p>
                      {todo.due_date && (
                        <p className="text-xs text-gray-500">
                          Fällig: {formatDate(todo.due_date)}
                        </p>
                      )}
                    </div>
                  </div>
                  <Badge className={priorityColors[todo.priority]}>
                    {priorityLabels[todo.priority]}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              Keine offenen Aufgaben. Erstelle einen KI-Tagesplan!
            </p>
          )}
        </Card>

        {/* Projektübersicht */}
        <Card title="Projekte">
          {projectsLoading ? (
            <p className="text-sm text-gray-500">Lade Projekte...</p>
          ) : projects?.results?.length ? (
            <ul className="space-y-3">
              {projects.results.slice(0, 6).map((project) => (
                <li key={project.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {project.name}
                    </p>
                    <p className="text-xs text-gray-500">{project.key}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={project.is_synced ? "success" : "default"}>
                      {project.is_synced ? "Sync" : "Lokal"}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {project.issue_count} Issues
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              Noch keine Projekte. Verbinde Jira in den Einstellungen.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}

