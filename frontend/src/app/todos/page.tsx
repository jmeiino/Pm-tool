"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useTodos, useUpdateTodo } from "@/hooks/useTodos";
import { TodoCreateDialog } from "@/components/todos/TodoCreateDialog";
import { priorityLabels, priorityColors, statusLabels, formatDate } from "@/lib/utils";
import { PlusIcon, FunnelIcon } from "@heroicons/react/24/outline";

const statusFilters = [
  { value: "", label: "Alle" },
  { value: "pending", label: "Offen" },
  { value: "in_progress", label: "In Bearbeitung" },
  { value: "done", label: "Erledigt" },
];

export default function TodosPage() {
  const [statusFilter, setStatusFilter] = useState("pending");
  const [showCreate, setShowCreate] = useState(false);
  const filters = statusFilter ? { status: statusFilter } : {};
  const { data, isLoading } = useTodos(filters);
  const updateTodo = useUpdateTodo();

  const handleToggleDone = (id: number, currentStatus: string) => {
    const newStatus = currentStatus === "done" ? "pending" : "done";
    updateTodo.mutate({ id, status: newStatus });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Aufgaben</h2>
        <Button onClick={() => setShowCreate(true)}>
          <PlusIcon className="h-4 w-4" />
          Neue Aufgabe
        </Button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <FunnelIcon className="h-4 w-4 text-gray-500" />
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

      {/* Aufgaben-Liste */}
      <Card>
        {isLoading ? (
          <p className="text-gray-500">Lade Aufgaben...</p>
        ) : data?.results?.length ? (
          <ul className="divide-y divide-gray-100">
            {data.results.map((todo) => (
              <li key={todo.id} className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={todo.status === "done"}
                    onChange={() => handleToggleDone(todo.id, todo.status)}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600"
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
                    <div className="flex items-center gap-2 mt-1">
                      {todo.due_date && (
                        <span className="text-xs text-gray-500">
                          Fällig: {formatDate(todo.due_date)}
                        </span>
                      )}
                      {todo.source !== "manual" && (
                        <Badge variant="info">{todo.source}</Badge>
                      )}
                      {todo.estimated_hours && (
                        <span className="text-xs text-gray-400">
                          ~{todo.estimated_hours}h
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={priorityColors[todo.priority]}>
                    {priorityLabels[todo.priority]}
                  </Badge>
                  <Badge>{statusLabels[todo.status] || todo.status}</Badge>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">Keine Aufgaben gefunden.</p>
        )}
      </Card>

      <TodoCreateDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
