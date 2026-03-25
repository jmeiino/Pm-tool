"use client";

import { useState } from "react";
import { ImportWizard } from "@/components/import/ImportWizard";
import { ImportDashboard } from "@/components/import/ImportDashboard";

type ViewMode = "dashboard" | "wizard";

export default function ImportPage() {
  const [view, setView] = useState<ViewMode>("dashboard");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Import</h1>
          <p className="mt-1 text-sm text-gray-500">
            Integrationen verwalten und Daten selektiv importieren.
          </p>
        </div>
        <div className="flex rounded-lg border border-gray-200 bg-gray-50 p-0.5">
          <button
            onClick={() => setView("dashboard")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              view === "dashboard"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setView("wizard")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              view === "wizard"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Import-Wizard
          </button>
        </div>
      </div>

      {view === "dashboard" ? <ImportDashboard /> : <ImportWizard />}
    </div>
  );
}
