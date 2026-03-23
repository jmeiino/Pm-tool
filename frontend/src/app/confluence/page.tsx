"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SparklesIcon, DocumentTextIcon } from "@heroicons/react/24/outline";

export default function ConfluencePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Confluence</h2>
        <Button variant="secondary">
          <SparklesIcon className="h-4 w-4" />
          Seite analysieren
        </Button>
      </div>

      <Card title="Confluence-Seiten">
        <div className="text-center py-8">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4 text-sm text-gray-500">
            Verbinde Confluence in den Einstellungen, um Seiten hier anzuzeigen.
          </p>
        </div>
      </Card>
    </div>
  );
}
