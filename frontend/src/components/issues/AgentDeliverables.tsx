"use client";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import {
  CodeBracketIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";

interface Deliverable {
  type: string;
  filename?: string;
  content: string;
  language?: string;
}

const TYPE_ICONS: Record<string, typeof CodeBracketIcon> = {
  code: CodeBracketIcon,
  document: DocumentTextIcon,
  analysis: MagnifyingGlassIcon,
};

interface AgentDeliverablesProps {
  deliverables: Deliverable[];
}

export function AgentDeliverables({ deliverables }: AgentDeliverablesProps) {
  if (!deliverables?.length) return null;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-gray-700">
        Ergebnisse vom AI-Agent ({deliverables.length})
      </h4>
      {deliverables.map((d, i) => {
        const Icon = TYPE_ICONS[d.type] || DocumentTextIcon;
        return (
          <Card key={i}>
            <div className="flex items-center gap-2 mb-2">
              <Icon className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-900">
                {d.filename || `Ergebnis ${i + 1}`}
              </span>
              <Badge className="bg-gray-100 text-gray-600 text-[10px]">
                {d.type}
              </Badge>
            </div>
            {d.type === "code" ? (
              <pre className="overflow-x-auto rounded-lg bg-gray-900 p-4 text-xs text-gray-100">
                <code>{d.content}</code>
              </pre>
            ) : (
              <div className="text-sm text-gray-700 whitespace-pre-line">
                {d.content}
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}
