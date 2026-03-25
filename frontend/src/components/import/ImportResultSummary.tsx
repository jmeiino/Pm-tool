"use client";

import { CheckCircleIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/Button";
import type { ImportConfirmResponse } from "@/lib/types";

interface ImportResultSummaryProps {
  result: ImportConfirmResponse;
  onDismiss: () => void;
}

export function ImportResultSummary({ result, onDismiss }: ImportResultSummaryProps) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 p-6 text-center">
      <CheckCircleIcon className="mx-auto h-10 w-10 text-green-500" />
      <h3 className="mt-3 text-sm font-semibold text-green-900">Import erfolgreich</h3>
      <p className="mt-1 text-sm text-green-700">{result.detail}</p>
      <div className="mt-3 flex justify-center gap-4 text-sm">
        <span className="text-green-700">
          <strong>{result.created}</strong> erstellt
        </span>
        <span className="text-green-700">
          <strong>{result.updated}</strong> aktualisiert
        </span>
      </div>
      <Button variant="secondary" size="sm" className="mt-4" onClick={onDismiss}>
        Schliessen
      </Button>
    </div>
  );
}
