"use client";

import { useState, useMemo } from "react";
import { addDays, startOfWeek, format, isSameDay } from "date-fns";
import { de } from "date-fns/locale";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useDailyPlan, useTodos } from "@/hooks/useTodos";
import { priorityColors, priorityLabels } from "@/lib/utils";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
} from "@heroicons/react/24/outline";

const WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];

function DayColumn({ date, dayName }: { date: Date; dayName: string }) {
  const dateStr = format(date, "yyyy-MM-dd");
  const { data: plan } = useDailyPlan(dateStr);
  const isToday = isSameDay(date, new Date());

  return (
    <div
      className={`rounded-xl border bg-white ${
        isToday ? "border-primary-300 ring-1 ring-primary-200" : "border-gray-200"
      }`}
    >
      <div
        className={`px-3 py-2 border-b text-center ${
          isToday ? "bg-primary-50" : "bg-gray-50"
        }`}
      >
        <p className="text-xs font-medium text-gray-500">{dayName}</p>
        <p
          className={`text-sm font-semibold ${
            isToday ? "text-primary-700" : "text-gray-900"
          }`}
        >
          {format(date, "d. MMM", { locale: de })}
        </p>
      </div>
      <div className="p-2 min-h-[200px] space-y-1.5">
        {plan?.items?.length ? (
          plan.items.map((item) => (
            <div
              key={item.id}
              className="rounded-lg border border-gray-100 bg-gray-50 p-2 text-xs hover:bg-gray-100 transition-colors"
            >
              <p className="font-medium text-gray-900 truncate">
                {item.todo_title}
              </p>
              {item.scheduled_start && (
                <p className="text-gray-400 mt-0.5">
                  {item.scheduled_start}
                  {item.time_block_minutes
                    ? ` · ${item.time_block_minutes}m`
                    : ""}
                </p>
              )}
            </div>
          ))
        ) : (
          <p className="text-xs text-gray-300 text-center py-6">Leer</p>
        )}
      </div>
      {plan && (
        <div className="border-t px-3 py-1.5 text-center">
          <span className="text-[10px] text-gray-400">
            {plan.items?.length || 0} Aufgaben
          </span>
        </div>
      )}
    </div>
  );
}

export default function WochenplanPage() {
  const [weekOffset, setWeekOffset] = useState(0);

  const weekStart = useMemo(() => {
    const today = new Date();
    const start = startOfWeek(today, { weekStartsOn: 1 }); // Monday
    return addDays(start, weekOffset * 7);
  }, [weekOffset]);

  const weekDates = useMemo(
    () => WEEKDAYS.map((_, i) => addDays(weekStart, i)),
    [weekStart]
  );

  const weekLabel = `${format(weekDates[0], "d. MMM", { locale: de })} – ${format(
    weekDates[4],
    "d. MMM yyyy",
    { locale: de }
  )}`;

  // Load todos summary for sidebar
  const { data: pendingTodos } = useTodos({ status: "pending" });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Wochenplan</h2>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setWeekOffset((o) => o - 1)}
          >
            <ChevronLeftIcon className="h-4 w-4" />
          </Button>
          <button
            onClick={() => setWeekOffset(0)}
            className="text-sm font-medium text-gray-700 hover:text-primary-600 min-w-[180px] text-center"
          >
            {weekOffset === 0 ? "Diese Woche" : weekLabel}
          </button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setWeekOffset((o) => o + 1)}
          >
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Week Grid */}
      <div className="grid grid-cols-5 gap-3">
        {weekDates.map((date, i) => (
          <DayColumn key={date.toISOString()} date={date} dayName={WEEKDAYS[i]} />
        ))}
      </div>

      {/* Ungeplante Aufgaben */}
      <Card title={`Ungeplante Aufgaben (${pendingTodos?.count || 0})`}>
        {pendingTodos?.results?.length ? (
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-3">
            {pendingTodos.results.slice(0, 12).map((todo) => (
              <div
                key={todo.id}
                className="rounded-lg border border-gray-100 p-3 text-sm hover:bg-gray-50"
              >
                <p className="font-medium text-gray-900 truncate">
                  {todo.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={`${priorityColors[todo.priority]} text-[10px]`}>
                    {priorityLabels[todo.priority]}
                  </Badge>
                  {todo.estimated_hours && (
                    <span className="text-xs text-gray-400">
                      ~{todo.estimated_hours}h
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 text-center py-4">
            Alle Aufgaben sind erledigt oder geplant.
          </p>
        )}
      </Card>
    </div>
  );
}
