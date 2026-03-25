"use client";

import { cn } from "@/lib/utils";
import { useIntegrations } from "@/hooks/useIntegrations";
import { useImportWizardStore, type ImportTab } from "@/stores/useImportWizardStore";
import { JiraImportStep } from "./JiraImportStep";
import { GitHubImportStep } from "./GitHubImportStep";
import { ConfluenceImportStep } from "./ConfluenceImportStep";
import Link from "next/link";

const tabs: { id: ImportTab; label: string; type: string; icon: string; color: string }[] = [
  { id: "jira", label: "Jira", type: "jira", icon: "J", color: "bg-blue-500" },
  { id: "github", label: "GitHub", type: "github", icon: "G", color: "bg-gray-800" },
  { id: "confluence", label: "Confluence", type: "confluence", icon: "C", color: "bg-blue-400" },
];

export function ImportWizard() {
  const { activeTab, setActiveTab } = useImportWizardStore();
  const { data: integrationsData } = useIntegrations();
  const integrations = integrationsData?.results || [];

  const getIntegration = (type: string) =>
    integrations.find((i) => i.integration_type === type && i.is_enabled);

  return (
    <div className="space-y-6">
      {/* Tab-Navigation */}
      <div className="flex gap-2 border-b border-gray-200">
        {tabs.map((tab) => {
          const connected = !!getIntegration(tab.type);
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                activeTab === tab.id
                  ? "border-primary-600 text-primary-600"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              )}
            >
              <div
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded text-xs font-bold text-white",
                  tab.color,
                  !connected && "opacity-40"
                )}
              >
                {tab.icon}
              </div>
              {tab.label}
              {!connected && (
                <span className="text-xs text-gray-400">(nicht verbunden)</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab-Inhalt */}
      {(() => {
        const currentTab = tabs.find((t) => t.id === activeTab)!;
        const connected = !!getIntegration(currentTab.type);

        if (!connected) {
          return (
            <div className="rounded-lg border border-dashed border-gray-300 py-16 text-center">
              <div
                className={cn(
                  "mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg text-white font-bold opacity-40",
                  currentTab.color
                )}
              >
                {currentTab.icon}
              </div>
              <h3 className="text-sm font-semibold text-gray-900">
                {currentTab.label} ist nicht verbunden
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Verbinde {currentTab.label} in den Einstellungen, um Daten zu importieren.
              </p>
              <Link
                href="/einstellungen"
                className="mt-4 inline-flex items-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
              >
                Zu den Einstellungen
              </Link>
            </div>
          );
        }

        switch (activeTab) {
          case "jira":
            return <JiraImportStep />;
          case "github":
            return <GitHubImportStep />;
          case "confluence":
            return <ConfluenceImportStep />;
        }
      })()}
    </div>
  );
}
