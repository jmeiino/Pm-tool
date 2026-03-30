"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useDelegateTask } from "@/hooks/useAgents";
import { CpuChipIcon, XMarkIcon } from "@heroicons/react/24/outline";

const TASK_TYPES = [
  { value: "software", label: "Software / Code" },
  { value: "content", label: "Content / Text" },
  { value: "research", label: "Recherche" },
  { value: "design", label: "Design" },
  { value: "general", label: "Allgemein" },
];

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending: { label: "Wartend", color: "bg-gray-100 text-gray-700" },
  assigned: { label: "Zugewiesen", color: "bg-blue-100 text-blue-700" },
  in_progress: { label: "In Bearbeitung", color: "bg-yellow-100 text-yellow-700" },
  review: { label: "Im Review", color: "bg-purple-100 text-purple-700" },
  needs_input: { label: "Rueckfrage", color: "bg-orange-100 text-orange-700" },
  completed: { label: "Erledigt", color: "bg-green-100 text-green-700" },
  failed: { label: "Fehlgeschlagen", color: "bg-red-100 text-red-700" },
  cancelled: { label: "Abgebrochen", color: "bg-gray-100 text-gray-500" },
};

interface DelegateToAgentButtonProps {
  issueId: number;
  activeAgentTaskStatus?: string;
}

export function DelegateToAgentButton({
  issueId,
  activeAgentTaskStatus,
}: DelegateToAgentButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [taskType, setTaskType] = useState("general");
  const [instructions, setInstructions] = useState("");
  const [priority, setPriority] = useState(3);
  const delegate = useDelegateTask();

  const handleDelegate = () => {
    delegate.mutate(
      { issue_id: issueId, task_type: taskType, priority, instructions },
      { onSuccess: () => setIsOpen(false) }
    );
  };

  // Zeige Status-Badge wenn bereits delegiert
  if (activeAgentTaskStatus) {
    const config = STATUS_CONFIG[activeAgentTaskStatus] || STATUS_CONFIG.pending;
    return (
      <Badge className={config.color}>
        <CpuChipIcon className="mr-1 h-3.5 w-3.5" />
        AI: {config.label}
      </Badge>
    );
  }

  return (
    <>
      <Button
        variant="secondary"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="gap-1.5"
      >
        <CpuChipIcon className="h-4 w-4" />
        An AI-Agent delegieren
      </Button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">An AI-Agent delegieren</h3>
              <button onClick={() => setIsOpen(false)}>
                <XMarkIcon className="h-5 w-5 text-gray-400" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Aufgabentyp
                </label>
                <select
                  value={taskType}
                  onChange={(e) => setTaskType(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  {TASK_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Prioritaet (1-5)
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Niedrig</span>
                  <span>{priority}</span>
                  <span>Kritisch</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Instruktionen (optional)
                </label>
                <textarea
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="z.B. Verwende React + Tailwind CSS..."
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" size="sm" onClick={() => setIsOpen(false)}>
                Abbrechen
              </Button>
              <Button
                size="sm"
                onClick={handleDelegate}
                disabled={delegate.isPending}
              >
                {delegate.isPending ? "Delegiere..." : "Delegieren"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
