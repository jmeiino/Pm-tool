"use client";

import { useState, useMemo } from "react";
import {
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  addDays,
  addWeeks,
  addMonths,
  format,
  isSameDay,
  isSameMonth,
  parseISO,
  isWithinInterval,
} from "date-fns";
import { de } from "date-fns/locale";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useCalendarEvents } from "@/hooks/useCalendar";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  CalendarDaysIcon,
} from "@heroicons/react/24/outline";

type ViewMode = "month" | "week";

export default function KalenderPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>("week");

  const range = useMemo(() => {
    if (viewMode === "month") {
      const start = startOfMonth(currentDate);
      const end = endOfMonth(currentDate);
      return { start, end };
    }
    const start = startOfWeek(currentDate, { weekStartsOn: 1 });
    const end = endOfWeek(currentDate, { weekStartsOn: 1 });
    return { start, end };
  }, [currentDate, viewMode]);

  const { data: events } = useCalendarEvents(
    range.start.toISOString(),
    range.end.toISOString()
  );

  const navigate = (dir: -1 | 1) => {
    if (viewMode === "month") {
      setCurrentDate((d) => addMonths(d, dir));
    } else {
      setCurrentDate((d) => addWeeks(d, dir));
    }
  };

  const headerLabel =
    viewMode === "month"
      ? format(currentDate, "MMMM yyyy", { locale: de })
      : `${format(range.start, "d. MMM", { locale: de })} – ${format(
          range.end,
          "d. MMM yyyy",
          { locale: de }
        )}`;

  // Generate week days (Mon-Sun)
  const weekDays = useMemo(() => {
    const start = startOfWeek(
      viewMode === "week" ? currentDate : range.start,
      { weekStartsOn: 1 }
    );
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [currentDate, viewMode, range.start]);

  // Generate month grid
  const monthDays = useMemo(() => {
    if (viewMode !== "month") return [];
    const monthStart = startOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
    return Array.from({ length: 42 }, (_, i) => addDays(calendarStart, i));
  }, [currentDate, viewMode]);

  const getEventsForDay = (day: Date) =>
    events?.results?.filter((ev) => {
      const evStart = parseISO(ev.start_time);
      return isSameDay(evStart, day);
    }) || [];

  const hours = Array.from({ length: 12 }, (_, i) => i + 7); // 07:00 - 18:00

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Kalender</h2>
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            {(["week", "month"] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1.5 text-xs font-medium ${
                  viewMode === mode
                    ? "bg-primary-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                {mode === "week" ? "Woche" : "Monat"}
              </button>
            ))}
          </div>
          {/* Navigation */}
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ChevronLeftIcon className="h-4 w-4" />
          </Button>
          <button
            onClick={() => setCurrentDate(new Date())}
            className="text-sm font-medium text-gray-700 hover:text-primary-600 min-w-[180px] text-center"
          >
            {headerLabel}
          </button>
          <Button variant="ghost" size="sm" onClick={() => navigate(1)}>
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Week View */}
      {viewMode === "week" && (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
          {/* Day Headers */}
          <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b bg-gray-50">
            <div className="p-2" />
            {weekDays.map((day) => {
              const isToday = isSameDay(day, new Date());
              return (
                <div
                  key={day.toISOString()}
                  className={`p-2 text-center border-l ${
                    isToday ? "bg-primary-50" : ""
                  }`}
                >
                  <p className="text-xs text-gray-500">
                    {format(day, "EEE", { locale: de })}
                  </p>
                  <p
                    className={`text-sm font-semibold ${
                      isToday ? "text-primary-700" : "text-gray-900"
                    }`}
                  >
                    {format(day, "d")}
                  </p>
                </div>
              );
            })}
          </div>
          {/* Time Grid */}
          <div className="grid grid-cols-[60px_repeat(7,1fr)]">
            {hours.map((hour) => (
              <div key={hour} className="contents">
                <div className="p-1 text-right pr-2 text-[10px] text-gray-400 border-t h-16">
                  {String(hour).padStart(2, "0")}:00
                </div>
                {weekDays.map((day) => {
                  const dayEvents = getEventsForDay(day).filter((ev) => {
                    const h = parseISO(ev.start_time).getHours();
                    return h === hour;
                  });
                  return (
                    <div
                      key={`${day.toISOString()}-${hour}`}
                      className="border-l border-t h-16 p-0.5 relative"
                    >
                      {dayEvents.map((ev) => (
                        <div
                          key={ev.id}
                          className="rounded bg-blue-100 text-blue-800 px-1 py-0.5 text-[10px] truncate mb-0.5"
                          title={ev.title}
                        >
                          {ev.title}
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Month View */}
      {viewMode === "month" && (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
          {/* Day Headers */}
          <div className="grid grid-cols-7 bg-gray-50 border-b">
            {["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"].map((d) => (
              <div key={d} className="p-2 text-center text-xs font-medium text-gray-500">
                {d}
              </div>
            ))}
          </div>
          {/* Day Cells */}
          <div className="grid grid-cols-7">
            {monthDays.map((day) => {
              const isToday = isSameDay(day, new Date());
              const inMonth = isSameMonth(day, currentDate);
              const dayEvents = getEventsForDay(day);

              return (
                <div
                  key={day.toISOString()}
                  className={`min-h-[80px] border-b border-r p-1 ${
                    !inMonth ? "bg-gray-50" : ""
                  }`}
                >
                  <p
                    className={`text-xs font-medium mb-0.5 ${
                      isToday
                        ? "text-primary-700 font-bold"
                        : inMonth
                        ? "text-gray-900"
                        : "text-gray-400"
                    }`}
                  >
                    {format(day, "d")}
                  </p>
                  {dayEvents.slice(0, 2).map((ev) => (
                    <div
                      key={ev.id}
                      className="rounded bg-blue-50 text-blue-700 px-1 py-0.5 text-[10px] truncate mb-0.5"
                    >
                      {ev.title}
                    </div>
                  ))}
                  {dayEvents.length > 2 && (
                    <p className="text-[10px] text-gray-400">
                      +{dayEvents.length - 2} mehr
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!events?.results?.length && (
        <Card>
          <div className="text-center py-4">
            <CalendarDaysIcon className="mx-auto h-8 w-8 text-gray-300" />
            <p className="mt-2 text-sm text-gray-500">
              Keine Termine im ausgewählten Zeitraum. Verbinde Microsoft 365 in den Einstellungen.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
