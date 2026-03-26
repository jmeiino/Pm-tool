"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useIntegrations, useSyncIntegration, useDeleteIntegration } from "@/hooks/useIntegrations";
import { useAIProvider, useUpdateAIProvider } from "@/hooks/useAI";
import { useCurrentUser, useUpdateUser } from "@/hooks/useUser";
import { JiraConnectDialog } from "@/components/integrations/JiraConnectDialog";
import { ConfluenceConnectDialog } from "@/components/integrations/ConfluenceConnectDialog";
import { GitHubConnectDialog } from "@/components/integrations/GitHubConnectDialog";
import { MicrosoftConnectDialog } from "@/components/integrations/MicrosoftConnectDialog";
import { SyncStatusIndicator } from "@/components/integrations/SyncStatusIndicator";
import {
  ArrowDownTrayIcon,
  CheckIcon,
  EyeIcon,
  EyeSlashIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Integration metadata
// ---------------------------------------------------------------------------
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
    description: "Commits, Pull Requests und Code-Aktivitaet",
    icon: "G",
    color: "bg-gray-800",
  },
};
const allIntegrationTypes = ["jira", "confluence", "microsoft_calendar", "github"];

// ---------------------------------------------------------------------------
// AI provider metadata
// ---------------------------------------------------------------------------
const providerOptions = [
  {
    key: "claude",
    name: "Claude (Anthropic)",
    icon: "A",
    color: "bg-amber-600",
    description: "Leistungsstarke KI fuer komplexe Analysen",
  },
  {
    key: "ollama",
    name: "Ollama (Lokal)",
    icon: "O",
    color: "bg-green-600",
    description: "Laeuft lokal — keine Cloud, keine Kosten",
  },
  {
    key: "openrouter",
    name: "OpenRouter",
    icon: "R",
    color: "bg-violet-600",
    description: "Zugang zu 100+ Modellen ueber eine API",
  },
];

// ---------------------------------------------------------------------------
// Timezone options
// ---------------------------------------------------------------------------
const TIMEZONES = [
  "Europe/Berlin",
  "Europe/Vienna",
  "Europe/Zurich",
  "Europe/London",
  "Europe/Paris",
  "Europe/Amsterdam",
  "America/New_York",
  "America/Chicago",
  "America/Los_Angeles",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "UTC",
];

// ---------------------------------------------------------------------------
// Reusable components
// ---------------------------------------------------------------------------
function SectionHeading({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-1">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      {description && <p className="text-sm text-gray-500">{description}</p>}
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-gray-700 mb-1">{children}</label>;
}

function TextInput({
  value,
  onChange,
  placeholder,
  type = "text",
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
}) {
  const [showPassword, setShowPassword] = useState(false);
  const isSecret = type === "password";

  return (
    <div className="relative">
      <input
        type={isSecret && !showPassword ? "password" : "text"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand disabled:bg-gray-50 disabled:text-gray-400 pr-10"
      />
      {isSecret && value && (
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          {showPassword ? (
            <EyeSlashIcon className="h-4 w-4" />
          ) : (
            <EyeIcon className="h-4 w-4" />
          )}
        </button>
      )}
    </div>
  );
}

function SaveButton({
  onClick,
  isPending,
  isSuccess,
  label = "Speichern",
}: {
  onClick: () => void;
  isPending: boolean;
  isSuccess: boolean;
  label?: string;
}) {
  return (
    <Button onClick={onClick} disabled={isPending} size="sm">
      {isPending ? (
        "Speichert..."
      ) : isSuccess ? (
        <>
          <CheckIcon className="h-4 w-4" />
          Gespeichert
        </>
      ) : (
        label
      )}
    </Button>
  );
}

// ---------------------------------------------------------------------------
// Profile Section
// ---------------------------------------------------------------------------
function ProfileSection() {
  const { data: user, isLoading } = useCurrentUser();
  const updateUser = useUpdateUser();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [timezone, setTimezone] = useState("Europe/Berlin");
  const [capacity, setCapacity] = useState("8");

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name);
      setLastName(user.last_name);
      setEmail(user.email);
      setTimezone(user.timezone);
      setCapacity(String(user.daily_capacity_hours));
    }
  }, [user]);

  const handleSave = () => {
    updateUser.mutate({
      first_name: firstName,
      last_name: lastName,
      email,
      timezone,
      daily_capacity_hours: parseFloat(capacity) || 8,
    });
  };

  if (isLoading) {
    return (
      <Card title="Profil">
        <p className="text-sm text-gray-400">Lade Profil...</p>
      </Card>
    );
  }

  return (
    <Card
      title="Profil"
      action={
        <SaveButton
          onClick={handleSave}
          isPending={updateUser.isPending}
          isSuccess={updateUser.isSuccess}
        />
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <FieldLabel>Vorname</FieldLabel>
          <TextInput value={firstName} onChange={setFirstName} placeholder="Max" />
        </div>
        <div>
          <FieldLabel>Nachname</FieldLabel>
          <TextInput value={lastName} onChange={setLastName} placeholder="Mustermann" />
        </div>
        <div>
          <FieldLabel>E-Mail</FieldLabel>
          <TextInput value={email} onChange={setEmail} placeholder="max@beispiel.de" />
        </div>
        <div>
          <FieldLabel>Benutzername</FieldLabel>
          <TextInput value={user?.username || ""} onChange={() => {}} disabled />
        </div>
        <div>
          <FieldLabel>Zeitzone</FieldLabel>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
        </div>
        <div>
          <FieldLabel>Tageskapazitaet (Stunden)</FieldLabel>
          <input
            type="number"
            min={1}
            max={16}
            step={0.5}
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// AI Provider Section
// ---------------------------------------------------------------------------
function AIProviderSection() {
  const { data: aiData, isLoading } = useAIProvider();
  const updateAI = useUpdateAIProvider();

  const [activeProvider, setActiveProvider] = useState("claude");

  // Claude fields
  const [claudeApiKey, setClaudeApiKey] = useState("");
  const [claudeModel, setClaudeModel] = useState("claude-sonnet-4-20250514");

  // Ollama fields
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [ollamaModel, setOllamaModel] = useState("llama3.1");

  // OpenRouter fields
  const [openrouterApiKey, setOpenrouterApiKey] = useState("");
  const [openrouterModel, setOpenrouterModel] = useState("anthropic/claude-sonnet-4");

  useEffect(() => {
    if (aiData) {
      setActiveProvider(aiData.active_provider);
      if (aiData.providers.claude) {
        setClaudeModel(aiData.providers.claude.model);
      }
      if (aiData.providers.ollama) {
        setOllamaModel(aiData.providers.ollama.model);
        if (aiData.providers.ollama.base_url) {
          setOllamaUrl(aiData.providers.ollama.base_url);
        }
      }
      if (aiData.providers.openrouter) {
        setOpenrouterModel(aiData.providers.openrouter.model);
      }
    }
  }, [aiData]);

  const handleSave = () => {
    updateAI.mutate({
      active_provider: activeProvider,
      claude: { api_key: claudeApiKey || undefined, model: claudeModel },
      ollama: { base_url: ollamaUrl, model: ollamaModel },
      openrouter: { api_key: openrouterApiKey || undefined, model: openrouterModel },
    });
  };

  if (isLoading) {
    return (
      <Card title="KI-Provider">
        <p className="text-sm text-gray-400">Lade KI-Einstellungen...</p>
      </Card>
    );
  }

  return (
    <Card
      title="KI-Provider"
      action={
        <SaveButton
          onClick={handleSave}
          isPending={updateAI.isPending}
          isSuccess={updateAI.isSuccess}
        />
      }
    >
      <div className="space-y-6">
        {/* Provider selection */}
        <div>
          <FieldLabel>Aktiver Provider</FieldLabel>
          <div className="grid gap-3 sm:grid-cols-3">
            {providerOptions.map((p) => {
              const isActive = activeProvider === p.key;
              const providerInfo = aiData?.providers[p.key];
              const isConfigured = providerInfo?.api_key_set;

              return (
                <button
                  key={p.key}
                  onClick={() => setActiveProvider(p.key)}
                  className={`relative rounded-lg border-2 p-4 text-left transition-all ${
                    isActive
                      ? "border-brand bg-brand-muted ring-1 ring-brand"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-9 w-9 items-center justify-center rounded-lg ${p.color} text-white text-sm font-bold`}
                    >
                      {p.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900">{p.name}</p>
                      <p className="text-[11px] text-gray-500 truncate">{p.description}</p>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-1.5">
                    {isConfigured ? (
                      <Badge variant="success">Konfiguriert</Badge>
                    ) : (
                      <Badge>Nicht konfiguriert</Badge>
                    )}
                    {isActive && <Badge variant="info">Aktiv</Badge>}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Provider-specific settings */}
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-4">
          {activeProvider === "claude" && (
            <>
              <SectionHeading
                title="Claude (Anthropic)"
                description="API-Key von console.anthropic.com"
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <FieldLabel>API-Key</FieldLabel>
                  <TextInput
                    type="password"
                    value={claudeApiKey}
                    onChange={setClaudeApiKey}
                    placeholder={
                      aiData?.providers.claude?.api_key_set
                        ? "••••••••  (bereits gesetzt)"
                        : "sk-ant-..."
                    }
                  />
                  <p className="mt-1 text-[11px] text-gray-400">
                    Leer lassen, um den bestehenden Key beizubehalten.
                  </p>
                </div>
                <div>
                  <FieldLabel>Modell</FieldLabel>
                  <select
                    value={claudeModel}
                    onChange={(e) => setClaudeModel(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                  >
                    <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
                    <option value="claude-opus-4-20250514">Claude Opus 4</option>
                    <option value="claude-haiku-4-20250514">Claude Haiku 4</option>
                    <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {activeProvider === "ollama" && (
            <>
              <SectionHeading
                title="Ollama (Lokal)"
                description="Verbindung zu einer lokalen Ollama-Instanz"
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <FieldLabel>Server-URL</FieldLabel>
                  <TextInput
                    value={ollamaUrl}
                    onChange={setOllamaUrl}
                    placeholder="http://localhost:11434"
                  />
                </div>
                <div>
                  <FieldLabel>Modell</FieldLabel>
                  <TextInput
                    value={ollamaModel}
                    onChange={setOllamaModel}
                    placeholder="z.B. llama3.1, mistral, codellama"
                  />
                  <p className="mt-1 text-[11px] text-gray-400">
                    Das Modell muss lokal installiert sein (ollama pull).
                  </p>
                </div>
              </div>
            </>
          )}

          {activeProvider === "openrouter" && (
            <>
              <SectionHeading
                title="OpenRouter"
                description="API-Key von openrouter.ai"
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <FieldLabel>API-Key</FieldLabel>
                  <TextInput
                    type="password"
                    value={openrouterApiKey}
                    onChange={setOpenrouterApiKey}
                    placeholder={
                      aiData?.providers.openrouter?.api_key_set
                        ? "••••••••  (bereits gesetzt)"
                        : "sk-or-..."
                    }
                  />
                  <p className="mt-1 text-[11px] text-gray-400">
                    Leer lassen, um den bestehenden Key beizubehalten.
                  </p>
                </div>
                <div>
                  <FieldLabel>Modell</FieldLabel>
                  <TextInput
                    value={openrouterModel}
                    onChange={setOpenrouterModel}
                    placeholder="z.B. anthropic/claude-sonnet-4, openai/gpt-4o"
                  />
                  <p className="mt-1 text-[11px] text-gray-400">
                    Modellliste: openrouter.ai/models
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Integration Section
// ---------------------------------------------------------------------------
type DialogType = "jira" | "confluence" | "github" | "microsoft" | null;

function IntegrationSection() {
  const { data: integrations } = useIntegrations();
  const syncIntegration = useSyncIntegration();
  const deleteIntegration = useDeleteIntegration();
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
    <>
      <Card title="Integrationen">
        <div className="space-y-3">
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
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => {
                          if (confirm(`${meta.name}-Integration wirklich trennen?`)) {
                            deleteIntegration.mutate(integration.id);
                          }
                        }}
                        disabled={deleteIntegration.isPending}
                      >
                        Trennen
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
        <div className="mt-4 border-t border-gray-100 pt-4">
          <Link
            href="/import"
            className="flex items-center gap-2 rounded-lg bg-brand-muted px-4 py-3 text-sm font-medium text-brand-deeper transition-colors hover:bg-brand-glow"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Import-Wizard — Daten aus Integrationen selektiv importieren
          </Link>
        </div>
      </Card>

      <JiraConnectDialog open={openDialog === "jira"} onClose={() => setOpenDialog(null)} />
      <ConfluenceConnectDialog open={openDialog === "confluence"} onClose={() => setOpenDialog(null)} />
      <GitHubConnectDialog open={openDialog === "github"} onClose={() => setOpenDialog(null)} />
      <MicrosoftConnectDialog open={openDialog === "microsoft"} onClose={() => setOpenDialog(null)} />
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function EinstellungenPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Einstellungen</h2>
        <p className="text-sm text-gray-500">
          Profil, KI-Provider und Integrationen konfigurieren
        </p>
      </div>

      <ProfileSection />
      <AIProviderSection />
      <IntegrationSection />
    </div>
  );
}
