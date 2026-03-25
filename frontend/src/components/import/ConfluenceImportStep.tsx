"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  useConfluenceSpacesPreview,
  useConfluencePagesPreview,
  useConfluenceConfirmImport,
} from "@/hooks/useImport";
import { useImportWizardStore } from "@/stores/useImportWizardStore";
import { ImportConfirmDialog } from "./ImportConfirmDialog";
import { ImportResultSummary } from "./ImportResultSummary";
import type { ImportConfirmResponse } from "@/lib/types";

export function ConfluenceImportStep() {
  const store = useImportWizardStore();
  const { data: spacesData, isLoading: spacesLoading, error: spacesError } =
    useConfluenceSpacesPreview();

  // Hole Seiten für den ersten ausgewählten Space
  const selectedSpaceKey = Array.from(store.confluenceSelectedSpaces)[0] || "";
  const { data: pagesData, isLoading: pagesLoading } = useConfluencePagesPreview(
    selectedSpaceKey,
    store.confluenceMyPagesOnly,
    !!selectedSpaceKey
  );

  const confirmImport = useConfluenceConfirmImport();
  const [showConfirm, setShowConfirm] = useState(false);
  const [importResult, setImportResult] = useState<ImportConfirmResponse | null>(null);
  const [analyzePages, setAnalyzePages] = useState(true);

  const handleConfirm = () => {
    const pages = (pagesData?.pages || [])
      .filter((p) => store.confluenceSelectedPages.has(p.confluence_page_id))
      .map((p) => ({
        confluence_page_id: p.confluence_page_id,
        space_key: p.space_key,
        title: p.title,
        analyze: analyzePages,
      }));

    confirmImport.mutate({ pages }, {
      onSuccess: (result) => {
        setImportResult(result);
        setShowConfirm(false);
      },
    });
  };

  if (spacesLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (spacesError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Fehler beim Laden der Confluence-Spaces: {(spacesError as Error).message}
      </div>
    );
  }

  if (importResult) {
    return <ImportResultSummary result={importResult} onDismiss={() => setImportResult(null)} />;
  }

  const spaces = spacesData?.spaces || [];
  const pages = pagesData?.pages || [];
  const selectedPageCount = store.confluenceSelectedPages.size;

  return (
    <div className="space-y-4">
      {/* Space-Auswahl */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Spaces auswählen</h4>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {spaces.map((space) => {
            const isSelected = store.confluenceSelectedSpaces.has(space.key);
            return (
              <button
                key={space.key}
                onClick={() => store.toggleConfluenceSpace(space.key)}
                className={`rounded-lg border p-3 text-left transition-colors ${
                  isSelected
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm text-gray-900">{space.name}</span>
                  <Badge variant={isSelected ? "info" : "default"}>{space.key}</Badge>
                </div>
                {space.description && (
                  <p className="mt-1 text-xs text-gray-500 line-clamp-2">{space.description}</p>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Seiten-Liste (wenn Space gewählt) */}
      {selectedSpaceKey && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-900">
              Seiten in {selectedSpaceKey}
            </h4>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={store.confluenceMyPagesOnly}
                onChange={(e) => store.setConfluenceMyPagesOnly(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary-600"
              />
              Nur meine Seiten
            </label>
          </div>

          {pagesLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : pages.length === 0 ? (
            <p className="text-sm text-gray-500 py-4">Keine Seiten gefunden.</p>
          ) : (
            <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
              {pages.map((page) => (
                <div
                  key={page.confluence_page_id}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={store.confluenceSelectedPages.has(page.confluence_page_id)}
                    onChange={() => store.toggleConfluencePage(page.confluence_page_id)}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-gray-900">{page.title}</span>
                    {page.author && (
                      <p className="text-xs text-gray-500">von {page.author}</p>
                    )}
                  </div>
                  {page.last_updated && (
                    <span className="text-xs text-gray-400">
                      {new Date(page.last_updated).toLocaleDateString("de-DE")}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Optionen + Aktions-Leiste */}
      <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {selectedPageCount} Seite(n) ausgewählt
          </span>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={analyzePages}
              onChange={(e) => setAnalyzePages(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-primary-600"
            />
            KI-Analyse starten
          </label>
        </div>
        <Button onClick={() => setShowConfirm(true)} disabled={selectedPageCount === 0}>
          Importieren
        </Button>
      </div>

      <ImportConfirmDialog
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleConfirm}
        title="Confluence-Import bestätigen"
        summary={[
          `${selectedPageCount} Seite(n) werden importiert.`,
          analyzePages ? "KI-Analyse wird gestartet." : "",
        ].filter(Boolean)}
        isPending={confirmImport.isPending}
      />
    </div>
  );
}
