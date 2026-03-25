"use client";

import { Button } from "@/components/ui/Button";

interface ImportConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  summary: string[];
  isPending: boolean;
}

export function ImportConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  summary,
  isPending,
}: ImportConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="mt-4 space-y-2">
          {summary.map((line, i) => (
            <p key={i} className="text-sm text-gray-600">
              {line}
            </p>
          ))}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={isPending}>
            Abbrechen
          </Button>
          <Button onClick={onConfirm} disabled={isPending}>
            {isPending ? "Importiert..." : "Importieren"}
          </Button>
        </div>
      </div>
    </div>
  );
}
