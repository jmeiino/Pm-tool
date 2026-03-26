"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  useConfluencePages,
  useAnalyzeConfluencePage,
} from "@/hooks/useConfluence";
import { formatDate } from "@/lib/utils";
import {
  SparklesIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";

export default function ConfluenceListPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useConfluencePages(
    search ? { search } : undefined
  );
  const analyzePage = useAnalyzeConfluencePage();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Confluence</h2>
      </div>

      {/* Suche */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Seiten durchsuchen..."
          className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />
      </div>

      {/* Seitenliste */}
      {isLoading ? (
        <p className="text-gray-500">Lade Confluence-Seiten...</p>
      ) : data?.results?.length ? (
        <div className="space-y-3">
          {data.results.map((page) => (
            <Link
              key={page.id}
              href={`/confluence/${page.id}`}
            >
              <Card className="hover:border-brand transition-colors cursor-pointer mb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <DocumentTextIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      <h3 className="text-sm font-semibold text-gray-900 truncate">
                        {page.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="info">{page.space_key}</Badge>
                      <span className="text-xs text-gray-400">
                        Aktualisiert: {formatDate(page.last_confluence_update)}
                      </span>
                    </div>
                    {page.ai_summary && (
                      <p className="mt-2 text-xs text-gray-500 line-clamp-2">
                        {page.ai_summary}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                    {page.ai_processed_at ? (
                      <Badge variant="success">Analysiert</Badge>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault();
                          analyzePage.mutate(page.id);
                        }}
                      >
                        <SparklesIcon className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-8">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-sm text-gray-500">
              {search
                ? "Keine Seiten gefunden."
                : "Verbinde Confluence in den Einstellungen, um Seiten hier anzuzeigen."}
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
