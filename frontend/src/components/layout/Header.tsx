"use client";

import { useState } from "react";
import { BellIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { useNotifications, useMarkNotificationRead } from "@/hooks/useNotifications";
import { useIntegrations, useSyncIntegration } from "@/hooks/useIntegrations";

export function Header() {
  const { data: notifications } = useNotifications();
  const { data: integrations } = useIntegrations();
  const syncIntegration = useSyncIntegration();
  const markRead = useMarkNotificationRead();
  const [showNotifications, setShowNotifications] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const unreadCount = notifications?.count || 0;

  const handleSyncAll = async () => {
    setSyncing(true);
    const enabled = integrations?.results?.filter((i) => i.is_enabled) || [];
    for (const integration of enabled) {
      try {
        await syncIntegration.mutateAsync(integration.id);
      } catch {
        // ignore individual failures
      }
    }
    setSyncing(false);
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">
          Persönliches Projektmanagement
        </h1>
      </div>
      <div className="flex items-center gap-4">
        <button
          className={`rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 ${
            syncing ? "animate-spin" : ""
          }`}
          title="Synchronisieren"
          onClick={handleSyncAll}
          disabled={syncing}
        >
          <ArrowPathIcon className="h-5 w-5" />
        </button>
        <div className="relative">
          <button
            className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            title="Benachrichtigungen"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <BellIcon className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 top-12 z-50 w-80 rounded-xl border bg-white shadow-lg">
              <div className="border-b px-4 py-3">
                <h3 className="text-sm font-semibold text-gray-900">
                  Benachrichtigungen
                </h3>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications?.results?.length ? (
                  notifications.results.slice(0, 10).map((n) => (
                    <div
                      key={n.id}
                      className="border-b border-gray-50 px-4 py-3 hover:bg-gray-50 cursor-pointer"
                      onClick={() => {
                        markRead.mutate(n.id);
                        setShowNotifications(false);
                      }}
                    >
                      <p className="text-sm font-medium text-gray-900">
                        {n.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                        {n.message}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="px-4 py-6 text-center text-sm text-gray-400">
                    Keine neuen Benachrichtigungen
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
