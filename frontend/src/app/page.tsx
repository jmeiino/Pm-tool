"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useProjects } from "@/hooks/useProjects";
import {
  useTodos,
  useDailyPlan,
  useUpdateTodo,
  useAiDailyPlanSuggestion,
} from "@/hooks/useTodos";
import { useNotifications } from "@/hooks/useNotifications";
import { useCalendarEvents } from "@/hooks/useCalendar";
import { useGitActivities } from "@/hooks/useGitHub";
import { priorityLabels, priorityColors, formatDate } from "@/lib/utils";
import {
  SparklesIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  FolderIcon,
  CalendarDaysIcon,
  CodeBracketIcon,
} from "@heroicons/react/24/outline";

function formatToday() {
  return new Date().toISOString().split("T")[0];
}

const eventTypeIcons: Record<string, string> = {
  commit: "C",
  pr_opened: "PR",
  pr_merged: "M",
  pr_closed: "X",
};

export default function DashboardPage() {
  const router = useRouter();
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const { data: todos, isLoading: todosLoading } = useTodos({ status: "pending" });
  const { data: overdueTodos } = useTodos({ status: "pending" });
  const { data: notifications } = useNotifications();
  const { data: dailyPlan } = useDailyPlan(formatToday());
  const { data: gitActivities } = useGitActivities();
  const updateTodo = useUpdateTodo();
  const aiSuggest = useAiDailyPlanSuggestion(formatToday());

  // Calendar events for today + next 3 days
  const now = new Date();
  const in3Days = new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000);
  const { data: upcomingEvents } = useCalendarEvents(
    now.toISOString(),
    in3Days.toISOString()
  );

  const today = now.toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const todayPlannedCount = dailyPlan?.items?.length || 0;

  // Overdue todos (due_date < today)
  const todayStr = formatToday();
  const overdueTodoList =
    overdueTodos?.results?.filter(
      (t) => t.due_date && t.due_date < todayStr && t.status !== "done"
    ) || [];

  const handleCreateAIPlan = () => {
    aiSuggest.mutate(undefined, {
      onSuccess: () => router.push("/planung/tagesplan"),
    });
  };

  const handleToggleDone = (id: number, currentStatus: string) => {
    updateTodo.mutate({ id, status: currentStatus === "done" ? "pending" : "done" });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500">{today}</p>
        </div>
        <Button onClick={handleCreateAIPlan} disabled={aiSuggest.isPending}>
          <SparklesIcon className="h-4 w-4" />
          {aiSuggest.isPending ? "KI plant..." : "KI-Tagesplan erstellen"}
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
              <p className="text-2xl font-bold text-gray-900">{todayPlannedCount}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-red-50 p-2">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Überfällig</p>
              <p className="text-2xl font-bold text-gray-900">
                {overdueTodoList.length}
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
                      checked={todo.status === "done"}
                      onChange={() => handleToggleDone(todo.id, todo.status)}
                      className="h-4 w-4 rounded border-gray-300 text-brand"
                    />
                    <div>
                      <p
                        className={`text-sm font-medium ${
                          todo.status === "done"
                            ? "text-gray-400 line-through"
                            : "text-gray-900"
                        }`}
                      >
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

        {/* Rechte Spalte */}
        <div className="space-y-6">
          {/* Projekte */}
          <Card title="Projekte">
            {projectsLoading ? (
              <p className="text-sm text-gray-500">Lade...</p>
            ) : projects?.results?.length ? (
              <ul className="space-y-2">
                {projects.results.slice(0, 5).map((project) => (
                  <li key={project.id}>
                    <Link
                      href={`/projekte/${project.id}`}
                      className="flex items-center justify-between hover:bg-gray-50 rounded-lg p-1 -mx-1"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-900">{project.name}</p>
                        <p className="text-xs text-gray-500">{project.key}</p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {project.issue_count} Issues
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">Noch keine Projekte.</p>
            )}
          </Card>

          {/* Anstehende Termine */}
          {upcomingEvents?.results && upcomingEvents.results.length > 0 && (
            <Card title="Anstehende Termine">
              <ul className="space-y-2">
                {upcomingEvents.results.slice(0, 4).map((ev) => (
                  <li key={ev.id} className="flex items-center gap-2">
                    <CalendarDaysIcon className="h-4 w-4 text-blue-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm text-gray-900 truncate">{ev.title}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(ev.start_time).toLocaleString("de-DE", {
                          day: "2-digit",
                          month: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Letzte Git-Aktivitäten */}
          {gitActivities?.results && gitActivities.results.length > 0 && (
            <Card title="Letzte Aktivitäten">
              <ul className="space-y-2">
                {gitActivities.results.slice(0, 5).map((act) => (
                  <li key={act.id} className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded bg-gray-100 text-[10px] font-bold text-gray-600">
                      {eventTypeIcons[act.event_type] || "?"}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs text-gray-900 truncate">{act.title}</p>
                      <p className="text-[10px] text-gray-400">{act.author}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </div>

      {/* Überfällige Aufgaben */}
      {overdueTodoList.length > 0 && (
        <Card
          title={`Überfällige Aufgaben (${overdueTodoList.length})`}
          action={<Badge variant="danger">{overdueTodoList.length}</Badge>}
        >
          <ul className="divide-y divide-gray-100">
            {overdueTodoList.slice(0, 5).map((todo) => (
              <li key={todo.id} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    onChange={() => handleToggleDone(todo.id, todo.status)}
                    className="h-4 w-4 rounded border-gray-300 text-brand"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{todo.title}</p>
                    <p className="text-xs text-red-500">
                      Fällig: {formatDate(todo.due_date!)}
                    </p>
                  </div>
                </div>
                <Badge className={priorityColors[todo.priority]}>
                  {priorityLabels[todo.priority]}
                </Badge>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
