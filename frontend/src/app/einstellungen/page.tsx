"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useIntegrations, useSyncIntegration } from "@/hooks/useIntegrations";
import { useAIProvider } from "@/hooks/useAI";
import { JiraConnectDialog } from "@/components/integrations/JiraConnectDialog";
import { ConfluenceConnectDialog } from "@/components/integrations/ConfluenceConnectDialog";
import { GitHubConnectDialog } from "@/components/integrations/GitHubConnectDialog";
import { MicrosoftConnectDialog } from "@/components/integrations/MicrosoftConnectDialog";
import { SyncStatusIndicator } from "@/components/integrations/SyncStatusIndicator";

const integrationMeta: Record<
  string,
  { name: string; description: string; icon: string; color: string }
> = {
  jira: {
    name: "Jira",
    description: "Bidirektionale Synchronisation von Projekten und Issues",
    icon: "J",
    color: "bg-blue-500",
  },
  confluence: {
    name: "Confluence",
    description: "Seiten lesen, analysieren und erstellen",
    icon: "C",
    color: "bg-blue-400",
  },
  microsoft_calendar: {
    name: "Microsoft 365",
    description: "Outlook Kalender, E-Mails, Teams und To-Do",
    icon: "M",
    color: "bg-orange-500",
  },
  github: {
    name: "GitHub",
    description: "Commits, Pull Requests und Code-Aktivität",
    icon: "G",
    color: "bg-gray-800",
  },
};

const allIntegrationTypes = ["jira", "confluence", "microsoft_calendar", "github"];

type DialogType = "jira" | "confluence" | "github" | "microsoft" | null;

const providerMeta: Record<string, { icon: string; color: string; description: string }> = {
  claude: {
    icon: "A",
    color: "bg-amber-600",
    description: "Anthropic Claude — leistungsstarke KI fuer komplexe Analysen",
  },
  ollama: {
    icon: "O",
    color: "bg-green-600",
    description: "Lokale KI — laeuft auf deinem Rechner, keine Cloud noetig",
  },
  openrouter: {
    icon: "R",
    color: "bg-violet-600",
    description: "OpenRouter — Zugang zu vielen Modellen ueber eine API",
  },
};

export default function EinstellungenPage() {
  const { data: integrations } = useIntegrations();
  const syncIntegration = useSyncIntegration();
  const { data: aiProvider } = useAIProvider();
  const [openDialog, setOpenDialog] = useState<DialogType>(null);

  const getIntegration = (type: string) =>
    integrations?.results?.find((i) => i.integration_type === type);

  const handleConnect = (type: string) => {
    if (type === "jira") setOpenDialog("jira");
    else if (type === "confluence") setOpenDialog("confluence");
    else if (type === "github") setOpenDialog("github");
    else if (type === "microsoft_calendar") setOpenDialog("microsoft");
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Einstellungen</h2>

      <Card title="Integrationen">
        <div className="space-y-4">
          {allIntegrationTypes.map((type) => {
            const meta = integrationMeta[type];
            const integration = getIntegration(type);

            if (!meta) return null;

            return (
              <div
                key={type}
                className="flex items-center justify-between rounded-lg border border-gray-100 p-4"
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-lg ${meta.color} text-white font-bold`}
                  >
                    {meta.icon}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{meta.name}</p>
                    <p className="text-sm text-gray-500">{meta.description}</p>
                    {integration && (
                      <SyncStatusIndicator
                        status={integration.sync_status}
                        lastSyncedAt={integration.last_synced_at}
                      />
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {integration ? (
                    <>
                      <Badge variant="success">Verbunden</Badge>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => syncIntegration.mutate(integration.id)}
                        disabled={
                          syncIntegration.isPending ||
                          integration.sync_status === "syncing"
                        }
                      >
                        {integration.sync_status === "syncing"
                          ? "Synchronisiert..."
                          : "Sync"}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Badge>Nicht verbunden</Badge>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleConnect(type)}
                      >
                        Verbinden
                      </Button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="KI-Provider">
        <div className="space-y-4">
          {aiProvider
            ? Object.entries(aiProvider.providers).map(([key, info]) => {
                const meta = providerMeta[key];
                const isActive = aiProvider.active_provider === key;

                return (
                  <div
                    key={key}
                    className={`flex items-center justify-between rounded-lg border p-4 ${
                      isActive
                        ? "border-primary-200 bg-primary-50"
                        : "border-gray-100"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg ${meta?.color || "bg-gray-500"} text-white font-bold`}
                      >
                        {meta?.icon || key[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-gray-900">
                            {info.name}
                          </p>
                          {isActive && (
                            <Badge variant="success">Aktiv</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">
                          {meta?.description}
                        </p>
                        <p className="mt-0.5 text-xs text-gray-400">
                          Modell: {info.model}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {info.configured ? (
                        <Badge variant="success">Konfiguriert</Badge>
                      ) : (
                        <Badge>Nicht konfiguriert</Badge>
                      )}
                    </div>
                  </div>
                );
              })
            : (
              <div className="space-y-3">
                {["claude", "ollama", "openrouter"].map((key) => {
                  const meta = providerMeta[key];
                  return (
                    <div
                      key={key}
                      className="flex items-center gap-4 rounded-lg border border-gray-100 p-4"
                    >
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg ${meta.color} text-white font-bold`}
                      >
                        {meta.icon}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{key}</p>
                        <p className="text-sm text-gray-500">{meta.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          <p className="text-xs text-gray-400">
            Der aktive Provider wird ueber die Umgebungsvariable{" "}
            <code className="rounded bg-gray-100 px-1 py-0.5 font-mono text-gray-600">
              AI_PROVIDER
            </code>{" "}
            konfiguriert.
          </p>
        </div>
      </Card>

      <JiraConnectDialog open={openDialog === "jira"} onClose={() => setOpenDialog(null)} />
      <ConfluenceConnectDialog open={openDialog === "confluence"} onClose={() => setOpenDialog(null)} />
      <GitHubConnectDialog open={openDialog === "github"} onClose={() => setOpenDialog(null)} />
      <MicrosoftConnectDialog open={openDialog === "microsoft"} onClose={() => setOpenDialog(null)} />
    </div>
  );
}
