"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useRegisterWebhook } from "@/hooks/useIntegrations";
import {
  BoltIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";

interface GitHubWebhookStatusProps {
  integrationId: number;
  settings: Record<string, unknown>;
}

export function GitHubWebhookStatus({
  integrationId,
  settings,
}: GitHubWebhookStatusProps) {
  const [callbackUrl, setCallbackUrl] = useState("");
  const registerWebhook = useRegisterWebhook();
  const hasWebhookSecret = !!settings?.webhook_secret;

  const handleRegister = () => {
    if (!callbackUrl.trim()) return;
    registerWebhook.mutate({ id: integrationId, callback_url: callbackUrl });
  };

  return (
    <Card title="Webhook-Status">
      <div className="space-y-4">
        {/* Status-Anzeige */}
        <div className="flex items-center gap-3">
          <BoltIcon className="h-5 w-5 text-gray-400" />
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">
              Echtzeit-Sync via Webhooks
            </p>
            <p className="text-xs text-gray-500">
              {hasWebhookSecret
                ? "Webhook ist registriert und aktiv"
                : "Kein Webhook registriert — Sync erfolgt per Polling"}
            </p>
          </div>
          <Badge
            className={
              hasWebhookSecret
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-600"
            }
          >
            {hasWebhookSecret ? "Aktiv" : "Inaktiv"}
          </Badge>
        </div>

        {/* Registrierung */}
        {!hasWebhookSecret && (
          <div className="space-y-2">
            <label className="block text-xs font-medium text-gray-700">
              Callback-URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={callbackUrl}
                onChange={(e) => setCallbackUrl(e.target.value)}
                placeholder="https://example.com/api/v1/integrations/github/webhook/"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
              />
              <Button
                size="sm"
                onClick={handleRegister}
                disabled={!callbackUrl.trim() || registerWebhook.isPending}
              >
                {registerWebhook.isPending ? "..." : "Registrieren"}
              </Button>
            </div>
            <p className="text-[11px] text-gray-400">
              Die URL muss oeffentlich erreichbar sein, damit GitHub Events senden kann.
            </p>
          </div>
        )}

        {/* Ergebnis */}
        {registerWebhook.isSuccess && registerWebhook.data?.webhooks && (
          <div className="space-y-1.5">
            {registerWebhook.data.webhooks.map((wh) => (
              <div
                key={wh.repo}
                className="flex items-center gap-2 text-xs"
              >
                {wh.success ? (
                  <CheckCircleIcon className="h-4 w-4 text-green-500" />
                ) : (
                  <ExclamationCircleIcon className="h-4 w-4 text-red-500" />
                )}
                <span className="text-gray-700">{wh.repo}</span>
                <span className="text-gray-400">
                  {wh.success ? `Hook #${wh.hook_id}` : "Fehlgeschlagen"}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Neu registrieren wenn bereits vorhanden */}
        {hasWebhookSecret && (
          <div className="pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-2">
              Events: issues, issue_comment, push, pull_request, pull_request_review
            </p>
            <div className="flex gap-2">
              <input
                type="url"
                value={callbackUrl}
                onChange={(e) => setCallbackUrl(e.target.value)}
                placeholder="Neue Callback-URL (optional)"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-xs focus:border-primary-500 focus:outline-none"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRegister}
                disabled={!callbackUrl.trim() || registerWebhook.isPending}
              >
                Neu registrieren
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
