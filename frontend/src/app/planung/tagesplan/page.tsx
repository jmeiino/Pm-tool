"use client";

import { useState, useCallback } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  useDailyPlan,
  useAiDailyPlanSuggestion,
  useReorderDailyPlan,
  useTodos,
  useAddToDailyPlan,
} from "@/hooks/useTodos";
import type { DailyPlanItem } from "@/lib/types";
import {
  SparklesIcon,
  ClockIcon,
  Bars3Icon,
  PlusIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

function formatToday() {
  return new Date().toISOString().split("T")[0];
}

function SortableTimeBlock({ item }: { item: DailyPlanItem }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-start gap-3 rounded-lg border p-4 bg-white ${
        isDragging
          ? "border-brand shadow-lg opacity-90"
          : "border-gray-100 hover:border-gray-200"
      }`}
    >
      <button
        className="mt-1 cursor-grab text-gray-400 hover:text-gray-600 active:cursor-grabbing"
        {...attributes}
        {...listeners}
      >
        <Bars3Icon className="h-4 w-4" />
      </button>
      <div className="flex-shrink-0 text-center min-w-[60px]">
        {item.scheduled_start && (
          <div className="flex items-center gap-1 text-sm font-medium text-gray-900">
            <ClockIcon className="h-4 w-4 text-gray-400" />
            {item.scheduled_start}
          </div>
        )}
        {item.time_block_minutes && (
          <p className="text-xs text-gray-500">{item.time_block_minutes} Min.</p>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {item.todo_title}
        </p>
        {item.ai_reasoning && (
          <p className="mt-1 text-xs text-gray-500 italic line-clamp-2">
            {item.ai_reasoning}
          </p>
        )}
      </div>
    </div>
  );
}

export default function TagesplanPage() {
  const [date] = useState(formatToday);
  const { data: plan, isLoading } = useDailyPlan(date);
  const aiSuggest = useAiDailyPlanSuggestion(date);
  const reorder = useReorderDailyPlan(date);
  const addItem = useAddToDailyPlan(date);
  const { data: availableTodos } = useTodos({ status: "pending" });
  const [showAddDialog, setShowAddDialog] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const todayFormatted = new Date().toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id || !plan?.items) return;

      const oldIndex = plan.items.findIndex((i) => i.id === active.id);
      const newIndex = plan.items.findIndex((i) => i.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;

      const reordered = arrayMove(plan.items, oldIndex, newIndex);
      reorder.mutate(reordered.map((item, i) => ({ id: item.id, order: i })));
    },
    [plan?.items, reorder]
  );

  // Todos not yet in the plan
  const unplannedTodos =
    availableTodos?.results?.filter(
      (t) => !plan?.items?.some((item) => item.todo === t.id)
    ) || [];

  const handleAddTodo = (todoId: number) => {
    addItem.mutate({ todo: todoId });
    setShowAddDialog(false);
  };

  const totalPlannedMinutes =
    plan?.items?.reduce((sum, item) => sum + (item.time_block_minutes || 0), 0) || 0;
  const capacityMinutes = (plan?.capacity_hours || 8) * 60;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Tagesplan</h2>
          <p className="text-sm text-gray-500">{todayFormatted}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={() => setShowAddDialog(true)}
            disabled={!plan}
          >
            <PlusIcon className="h-4 w-4" />
            Aufgabe
          </Button>
          <Button
            onClick={() => aiSuggest.mutate()}
            disabled={aiSuggest.isPending}
          >
            <SparklesIcon className="h-4 w-4" />
            {aiSuggest.isPending ? "KI plant..." : "KI-Vorschlag"}
          </Button>
        </div>
      </div>

      {/* KI-Zusammenfassung */}
      {plan?.ai_reasoning && (
        <Card title="KI-Begründung">
          <p className="text-sm text-gray-700 whitespace-pre-line">
            {plan.ai_reasoning}
          </p>
        </Card>
      )}

      {/* Kapazitätsbalken */}
      {plan && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Kapazität</span>
            <span className="text-sm text-gray-500">
              {Math.round(totalPlannedMinutes / 60 * 10) / 10}h / {plan.capacity_hours}h
            </span>
          </div>
          <div className="h-2 rounded-full bg-gray-200">
            <div
              className={`h-2 rounded-full transition-all ${
                totalPlannedMinutes > capacityMinutes
                  ? "bg-red-500"
                  : "bg-brand"
              }`}
              style={{
                width: `${Math.min(
                  (totalPlannedMinutes / capacityMinutes) * 100,
                  100
                )}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Zeitblöcke mit Drag & Drop */}
      <Card title={`Zeitblöcke (${plan?.items?.length || 0})`}>
        {isLoading ? (
          <p className="text-gray-500">Lade Tagesplan...</p>
        ) : plan?.items?.length ? (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={plan.items.map((i) => i.id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-2">
                {plan.items.map((item) => (
                  <SortableTimeBlock key={item.id} item={item} />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">Noch kein Tagesplan erstellt.</p>
            <Button
              variant="secondary"
              onClick={() => aiSuggest.mutate()}
              disabled={aiSuggest.isPending}
            >
              <SparklesIcon className="h-4 w-4" />
              KI-Tagesplan generieren
            </Button>
          </div>
        )}
      </Card>

      {/* Add Task Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Aufgabe hinzufügen
              </h3>
              <button
                onClick={() => setShowAddDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            {unplannedTodos.length ? (
              <ul className="max-h-64 overflow-y-auto divide-y divide-gray-100">
                {unplannedTodos.map((todo) => (
                  <li
                    key={todo.id}
                    onClick={() => handleAddTodo(todo.id)}
                    className="flex items-center justify-between py-3 px-2 hover:bg-gray-50 cursor-pointer rounded-lg"
                  >
                    <span className="text-sm text-gray-900">{todo.title}</span>
                    <PlusIcon className="h-4 w-4 text-gray-400" />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500 py-4 text-center">
                Keine ungeplanten Aufgaben vorhanden.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
