"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface MicrosoftConnectDialogProps {
  open: boolean;
  onClose: () => void;
}

export function MicrosoftConnectDialog({
  open,
  onClose,
}: MicrosoftConnectDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [authWindow, setAuthWindow] = useState<Window | null>(null);

  const handleConnect = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get<{ auth_url: string }>(
        "/integrations/microsoft/auth/"
      );
      // Open OAuth popup
      const popup = window.open(
        data.auth_url,
        "microsoft-oauth",
        "width=600,height=700,scrollbars=yes"
      );
      setAuthWindow(popup);
    } catch (err) {
      setError("Fehler beim Starten der Authentifizierung. Sind die MS-Umgebungsvariablen konfiguriert?");
    } finally {
      setLoading(false);
    }
  };

  // Listen for popup closing (OAuth callback)
  useEffect(() => {
    if (!authWindow) return;

    const timer = setInterval(() => {
      if (authWindow.closed) {
        clearInterval(timer);
        setAuthWindow(null);
        onClose();
        // Trigger a page reload to refresh integration status
        window.location.reload();
      }
    }, 500);

    return () => clearInterval(timer);
  }, [authWindow, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Microsoft 365 verbinden
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Verbinde dein Microsoft-365-Konto, um Kalender-Termine, E-Mails und
            Teams-Nachrichten zu synchronisieren.
          </p>

          <div className="rounded-lg border border-gray-200 p-4 space-y-2">
            <p className="text-sm font-medium text-gray-900">
              Folgende Berechtigungen werden angefragt:
            </p>
            <ul className="space-y-1">
              {[
                { scope: "Calendars.Read", label: "Kalender lesen" },
                { scope: "Mail.Read", label: "E-Mails lesen" },
                { scope: "Tasks.Read", label: "Aufgaben lesen" },
                {
                  scope: "ChannelMessage.Read.All",
                  label: "Teams-Nachrichten lesen",
                },
              ].map((perm) => (
                <li
                  key={perm.scope}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-gray-700">{perm.label}</span>
                  <Badge variant="info">{perm.scope}</Badge>
                </li>
              ))}
            </ul>
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {authWindow && (
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
              <p className="text-sm text-blue-700">
                Bitte schließe die Anmeldung im geöffneten Fenster ab...
              </p>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Abbrechen
            </Button>
            <Button
              onClick={handleConnect}
              disabled={loading || !!authWindow}
            >
              {loading
                ? "Lade..."
                : authWindow
                ? "Warte auf Anmeldung..."
                : "Mit Microsoft anmelden"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
