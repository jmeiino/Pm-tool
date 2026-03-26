"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { useCreateIntegration } from "@/hooks/useIntegrations";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface ConfluenceConnectDialogProps {
  open: boolean;
  onClose: () => void;
}

export function ConfluenceConnectDialog({ open, onClose }: ConfluenceConnectDialogProps) {
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [apiToken, setApiToken] = useState("");
  const [spaces, setSpaces] = useState("");
  const createIntegration = useCreateIntegration();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createIntegration.mutate(
      {
        integration_type: "confluence",
        credentials: { url, email, api_token: apiToken },
        is_enabled: true,
        settings: {
          spaces: spaces.split(",").map((s) => s.trim()).filter(Boolean),
        },
      },
      {
        onSuccess: () => {
          setUrl("");
          setEmail("");
          setApiToken("");
          setSpaces("");
          onClose();
        },
      }
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Confluence verbinden</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Atlassian URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="https://dein-team.atlassian.net"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">E-Mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">API-Token</label>
            <input
              type="password"
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Spaces (kommagetrennt)</label>
            <input
              type="text"
              value={spaces}
              onChange={(e) => setSpaces(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="DEV, TEAM, DOCS"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>Abbrechen</Button>
            <Button type="submit" disabled={createIntegration.isPending}>
              {createIntegration.isPending ? "Verbinde..." : "Verbinden"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
