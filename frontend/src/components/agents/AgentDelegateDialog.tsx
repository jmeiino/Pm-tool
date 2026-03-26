"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { useDelegateTask } from "@/hooks/useAgents";
import { useToast } from "@/components/ui/Toast";

interface AgentDelegateDialogProps {
  open: boolean;
  onClose: () => void;
  issueId: number;
  issueTitle: string;
}

export function AgentDelegateDialog({ open, onClose, issueId, issueTitle }: AgentDelegateDialogProps) {
  const delegate = useDelegateTask();
  const { addToast } = useToast();
  const [taskType, setTaskType] = useState("general");
  const [priority, setPriority] = useState(3);
  const [instructions, setInstructions] = useState("");

  if (!open) return null;

  const handleSubmit = () => {
    delegate.mutate(
      { issue_id: issueId, task_type: taskType, priority, instructions },
      {
        onSuccess: () => {
          addToast("success", "Aufgabe an die agentische Firma delegiert.");
          onClose();
        },
        onError: (err) => {
          addToast("error", `Delegation fehlgeschlagen: ${(err as Error).message}`);
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-md bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">An Agents delegieren</h3>
        <p className="mt-1 text-sm text-gray-500">{issueTitle}</p>

        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Aufgabentyp</label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="general">Allgemein</option>
              <option value="software">Software-Entwicklung</option>
              <option value="content">Content-Erstellung</option>
              <option value="design">Design & UX</option>
              <option value="research">Research & Analyse</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Priorität</label>
            <select
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value={1}>1 — Kritisch</option>
              <option value={2}>2 — Hoch</option>
              <option value={3}>3 — Normal</option>
              <option value={4}>4 — Niedrig</option>
              <option value={5}>5 — Minimal</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Anweisungen (optional)</label>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Zusätzliche Hinweise für die Agents..."
              rows={3}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Abbrechen
          </Button>
          <Button onClick={handleSubmit} disabled={delegate.isPending}>
            {delegate.isPending ? "Delegiert..." : "Delegieren"}
          </Button>
        </div>
      </div>
    </div>
  );
}
