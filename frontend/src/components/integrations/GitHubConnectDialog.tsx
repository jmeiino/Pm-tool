"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { useCreateIntegration } from "@/hooks/useIntegrations";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface GitHubConnectDialogProps {
  open: boolean;
  onClose: () => void;
}

export function GitHubConnectDialog({ open, onClose }: GitHubConnectDialogProps) {
  const [token, setToken] = useState("");
  const createIntegration = useCreateIntegration();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createIntegration.mutate(
      {
        integration_type: "github",
        credentials: { token },
        is_enabled: true,
        settings: { repos: [] },
      },
      {
        onSuccess: () => {
          setToken("");
          onClose();
        },
      }
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">GitHub verbinden</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Personal Access Token
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="ghp_xxxxxxxxxxxx"
              required
            />
            <p className="mt-1 text-xs text-gray-400">
              Erstelle einen Token unter github.com/settings/tokens mit repo-Berechtigung.
            </p>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Abbrechen
            </Button>
            <Button type="submit" disabled={createIntegration.isPending}>
              {createIntegration.isPending ? "Verbinde..." : "Verbinden"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
