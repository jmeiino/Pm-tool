"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useDailyPlan, useAiDailyPlanSuggestion } from "@/hooks/useTodos";
import { priorityLabels, priorityColors } from "@/lib/utils";
import { SparklesIcon, ClockIcon } from "@heroicons/react/24/outline";

function formatToday() {
  return new Date().toISOString().split("T")[0];
}

export default function TagesplanPage() {
  const [date] = useState(formatToday);
  const { data: plan, isLoading } = useDailyPlan(date);
  const aiSuggest = useAiDailyPlanSuggestion(date);

  const todayFormatted = new Date().toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Tagesplan</h2>
          <p className="text-sm text-gray-500">{todayFormatted}</p>
        </div>
        <Button
          onClick={() => aiSuggest.mutate()}
          disabled={aiSuggest.isPending}
        >
          <SparklesIcon className="h-4 w-4" />
          {aiSuggest.isPending ? "KI plant..." : "KI-Vorschlag"}
        </Button>
      </div>

      {/* KI-Zusammenfassung */}
      {plan?.ai_reasoning && (
        <Card title="KI-Begründung">
          <p className="text-sm text-gray-700 whitespace-pre-line">
            {plan.ai_reasoning}
          </p>
        </Card>
      )}

      {/* Zeitblöcke */}
      <Card title="Zeitblöcke">
        {isLoading ? (
          <p className="text-gray-500">Lade Tagesplan...</p>
        ) : plan?.items?.length ? (
          <div className="space-y-3">
            {plan.items.map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-4 rounded-lg border border-gray-100 p-4 hover:bg-gray-50"
              >
                <div className="flex-shrink-0 text-center">
                  {item.scheduled_start && (
                    <div className="flex items-center gap-1 text-sm font-medium text-gray-900">
                      <ClockIcon className="h-4 w-4 text-gray-400" />
                      {item.scheduled_start}
                    </div>
                  )}
                  {item.time_block_minutes && (
                    <p className="text-xs text-gray-500">
                      {item.time_block_minutes} Min.
                    </p>
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {item.todo_title}
                  </p>
                  {item.ai_reasoning && (
                    <p className="mt-1 text-xs text-gray-500 italic">
                      {item.ai_reasoning}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">
              Noch kein Tagesplan erstellt.
            </p>
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

      {/* Kapazität */}
      {plan && (
        <Card title="Kapazität">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-sm text-gray-500">Verfügbare Stunden</p>
              <p className="text-2xl font-bold text-gray-900">
                {plan.capacity_hours}h
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
