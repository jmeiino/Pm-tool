"use client";

import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  useConfluencePage,
  useAnalyzeConfluencePage,
  useCreateTodosFromPage,
} from "@/hooks/useConfluence";
import { formatDate } from "@/lib/utils";
import {
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ClipboardDocumentListIcon,
} from "@heroicons/react/24/outline";

export default function ConfluenceDetailPage() {
  const params = useParams();
  const pageId = Number(params.id);
  const { data: page, isLoading } = useConfluencePage(pageId);
  const analyzePage = useAnalyzeConfluencePage();
  const createTodos = useCreateTodosFromPage();

  if (isLoading) return <p className="text-gray-500">Lade Seite...</p>;
  if (!page) return <p className="text-gray-500">Seite nicht gefunden.</p>;

  const hasAnalysis = !!page.ai_processed_at;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{page.title}</h2>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="info">{page.space_key}</Badge>
            <span className="text-xs text-gray-400">
              Aktualisiert: {formatDate(page.last_confluence_update)}
            </span>
            {hasAnalysis && (
              <Badge variant="success">
                Analysiert am {formatDate(page.ai_processed_at!)}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasAnalysis && page.ai_action_items?.length > 0 && (
            <Button
              variant="secondary"
              onClick={() => createTodos.mutate(pageId)}
              disabled={createTodos.isPending}
            >
              <ClipboardDocumentListIcon className="h-4 w-4" />
              {createTodos.isPending
                ? "Erstelle..."
                : `${page.ai_action_items.length} Aufgaben erstellen`}
            </Button>
          )}
          <Button
            onClick={() => analyzePage.mutate(pageId)}
            disabled={analyzePage.isPending}
          >
            <SparklesIcon className="h-4 w-4" />
            {analyzePage.isPending ? "Analysiert..." : "Analysieren"}
          </Button>
        </div>
      </div>

      {/* AI Analyse Cards */}
      {hasAnalysis && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Zusammenfassung */}
          {page.ai_summary && (
            <Card title="Zusammenfassung" className="lg:col-span-2">
              <p className="text-sm text-gray-700 whitespace-pre-line">
                {page.ai_summary}
              </p>
            </Card>
          )}

          {/* Aktionspunkte */}
          {page.ai_action_items?.length > 0 && (
            <Card
              title={`Aktionspunkte (${page.ai_action_items.length})`}
              action={
                <Badge variant="warning">{page.ai_action_items.length}</Badge>
              }
            >
              <ul className="space-y-2">
                {page.ai_action_items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircleIcon className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">
                      {typeof item === "string" ? item : (item as any).action || JSON.stringify(item)}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Entscheidungen */}
          {page.ai_decisions?.length > 0 && (
            <Card
              title={`Entscheidungen (${page.ai_decisions.length})`}
              action={
                <Badge variant="info">{page.ai_decisions.length}</Badge>
              }
            >
              <ul className="space-y-2">
                {page.ai_decisions.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <LightBulbIcon className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">
                      {typeof item === "string" ? item : JSON.stringify(item)}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Risiken */}
          {page.ai_risks?.length > 0 && (
            <Card
              title={`Risiken (${page.ai_risks.length})`}
              action={
                <Badge variant="danger">{page.ai_risks.length}</Badge>
              }
            >
              <ul className="space-y-2">
                {page.ai_risks.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">
                      {typeof item === "string" ? item : JSON.stringify(item)}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {/* Seiteninhalt */}
      <Card title="Seiteninhalt">
        {page.content_text ? (
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line">
            {page.content_text.slice(0, 5000)}
            {page.content_text.length > 5000 && (
              <p className="text-gray-400 italic mt-4">
                ... Inhalt gekürzt ({page.content_text.length} Zeichen gesamt)
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-400">Kein Inhalt verfügbar.</p>
        )}
      </Card>
    </div>
  );
}
