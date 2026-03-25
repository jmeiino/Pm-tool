"use client";

import { ImportWizard } from "@/components/import/ImportWizard";

export default function ImportPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Import-Wizard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Daten aus Jira, GitHub und Confluence selektiv importieren.
          Wähle aus, welche Projekte, Issues und Seiten übernommen werden sollen.
        </p>
      </div>
      <ImportWizard />
    </div>
  );
}
