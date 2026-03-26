"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  useConfluenceSpacesPreview,
  useConfluencePagesPreview,
  useConfluenceConfirmImport,
  useConfluenceActionItems,
} from "@/hooks/useImport";
import { useImportWizardStore } from "@/stores/useImportWizardStore";
import { useToast } from "@/components/ui/Toast";
import { ImportConfirmDialog } from "./ImportConfirmDialog";
import type { ImportConfirmResponse, ConfluencePage } from "@/lib/types";

type WizardPhase = "select" | "action-items";

export function ConfluenceImportStep() {
  const store = useImportWizardStore();
  const { addToast } = useToast();
  const { data: spacesData, isLoading: spacesLoading, error: spacesError } =
    useConfluenceSpacesPreview();

  const selectedSpaceKey = Array.from(store.confluenceSelectedSpaces)[0] || "";
  const { data: pagesData, isLoading: pagesLoading } = useConfluencePagesPreview(
    selectedSpaceKey,
    store.confluenceMyPagesOnly,
    !!selectedSpaceKey
  );

  const confirmImport = useConfluenceConfirmImport();
  const [showConfirm, setShowConfirm] = useState(false);
  const [analyzePages, setAnalyzePages] = useState(true);
  const [phase, setPhase] = useState<WizardPhase>("select");
  const [importedPageDbIds, setImportedPageDbIds] = useState<number[]>([]);
  const [selectedActionItems, setSelectedActionItems] = useState<Set<string>>(new Set());

  // Action Items aus analysierten Seiten laden
  const { data: analyzedPages, isLoading: actionItemsLoading } =
    useConfluenceActionItems(importedPageDbIds, phase === "action-items");

  const toggleActionItem = (key: string) => {
    const next = new Set(selectedActionItems);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setSelectedActionItems(next);
  };

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
        addToast("success", `Confluence-Import: ${result.detail}`);
        setShowConfirm(false);

        if (analyzePages) {
          // IDs der importierten Seiten speichern für Action-Item-Phase
          // Die Confirm-Response enthält keine IDs, also müssen wir sie per API holen
          import("@/lib/api").then(({ api }) => {
            api.get("/integrations/confluence-pages/").then(({ data: pagesResp }) => {
              const importedIds = pages.map((p) => p.confluence_page_id);
              const dbIds = (pagesResp.results || [])
                .filter((dbPage: ConfluencePage) => importedIds.includes(dbPage.confluence_page_id))
                .map((dbPage: ConfluencePage) => dbPage.id);
              setImportedPageDbIds(dbIds);
              setPhase("action-items");
            });
          });
        }
      },
      onError: (err) => {
        addToast("error", `Confluence-Import fehlgeschlagen: ${(err as Error).message}`);
        setShowConfirm(false);
      },
    });
  };

  const handleCreateTodos = async () => {
    if (!analyzedPages) return;
    const { api } = await import("@/lib/api");

    let totalCreated = 0;
    for (const page of analyzedPages) {
      // Filtere ausgewählte Action Items für diese Seite
      const selectedIndices: number[] = [];
      page.ai_action_items.forEach((item: string, idx: number) => {
        if (selectedActionItems.has(`${page.id}-${idx}`)) {
          selectedIndices.push(idx);
        }
      });

      if (selectedIndices.length === 0) continue;

      try {
        const { data } = await api.post(
          `/integrations/confluence-pages/${page.id}/create-todos/`
        );
        totalCreated += data.count || 0;
      } catch {
        addToast("error", `Fehler beim Erstellen der Todos für "${page.title}"`);
      }
    }

    if (totalCreated > 0) {
      addToast("success", `${totalCreated} Todo(s) aus Action Items erstellt.`);
    }
    setPhase("select");
    setImportedPageDbIds([]);
    setSelectedActionItems(new Set());
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

  // Phase 2: Action Items auswählen
  if (phase === "action-items") {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h4 className="text-sm font-medium text-blue-900">
            Action Items aus KI-Analyse auswählen
          </h4>
          <p className="mt-1 text-xs text-blue-700">
            Die importierten Seiten werden analysiert. Wähle Action Items aus, die als Todos erstellt werden sollen.
          </p>
        </div>

        {actionItemsLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-24 w-full" />
            <p className="text-sm text-gray-500 text-center">
              KI-Analyse läuft... Seiten werden verarbeitet.
            </p>
          </div>
        ) : !analyzedPages || analyzedPages.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500">
              Noch keine Action Items verfügbar. Die KI-Analyse läuft noch...
            </p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => setPhase("select")}>
              Zurück zur Auswahl
            </Button>
          </div>
        ) : (
          <>
            {analyzedPages.map((page) => (
              <div key={page.id} className="rounded-lg border border-gray-200">
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                  <span className="text-sm font-medium text-gray-900">{page.title}</span>
                  <Badge variant="success" className="ml-2">
                    {page.ai_action_items.length} Action Items
                  </Badge>
                </div>
                <div className="divide-y divide-gray-100">
                  {page.ai_action_items.map((item: string, idx: number) => {
                    const key = `${page.id}-${idx}`;
                    const text = typeof item === "string" ? item : (item as Record<string, string>).action || "";
                    return (
                      <div key={key} className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={selectedActionItems.has(key)}
                          onChange={() => toggleActionItem(key)}
                          className="h-4 w-4 rounded border-gray-300 text-brand"
                        />
                        <span className="text-sm text-gray-700">{text}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">
                  {selectedActionItems.size} Action Item(s) ausgewählt
                </span>
                <Button variant="ghost" size="sm" onClick={() => setPhase("select")}>
                  Zurück
                </Button>
              </div>
              <Button
                onClick={handleCreateTodos}
                disabled={selectedActionItems.size === 0}
              >
                Als Todos erstellen
              </Button>
            </div>
          </>
        )}
      </div>
    );
  }

  // Phase 1: Spaces + Seiten auswählen
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
                    ? "border-brand bg-brand-muted"
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

      {/* Seiten-Liste */}
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
                className="h-4 w-4 rounded border-gray-300 text-brand"
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
                    className="h-4 w-4 rounded border-gray-300 text-brand"
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
              className="h-4 w-4 rounded border-gray-300 text-brand"
            />
            KI-Analyse + Action Items
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
          analyzePages ? "KI-Analyse wird gestartet. Danach können Action Items als Todos ausgewählt werden." : "",
        ].filter(Boolean)}
        isPending={confirmImport.isPending}
      />
    </div>
  );
}
