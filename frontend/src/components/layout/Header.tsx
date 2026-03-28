"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  BellIcon,
  ArrowPathIcon,
  Bars3Icon,
  ArrowRightStartOnRectangleIcon,
} from "@heroicons/react/24/outline";
import { useNotifications, useMarkNotificationRead } from "@/hooks/useNotifications";
import { useIntegrations, useSyncIntegration } from "@/hooks/useIntegrations";
import { useAppStore } from "@/stores/useAppStore";
import { useAuthStore } from "@/stores/useAuthStore";
import { api } from "@/lib/api";

export function Header() {
  const { data: notifications } = useNotifications();
  const { data: integrations } = useIntegrations();
  const syncIntegration = useSyncIntegration();
  const markRead = useMarkNotificationRead();
  const [showNotifications, setShowNotifications] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const { toggleSidebar } = useAppStore();
  const { logout, refreshToken, user } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await api.post("/auth/logout/", { refresh: refreshToken });
    } catch {
      // Ignore errors - logout locally anyway
    }
    logout();
    router.push("/login");
  };

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
    <header className="flex h-14 items-center justify-between border-b-[3px] border-brand bg-dark-bg px-4 lg:px-6">
      <div className="flex items-center gap-3">
        {/* Mobile hamburger */}
        <button
          className="rounded-sm p-2 text-[rgba(255,255,255,0.55)] hover:bg-[rgba(0,158,227,0.10)] hover:text-white lg:hidden"
          onClick={toggleSidebar}
        >
          <Bars3Icon className="h-5 w-5" />
        </button>
        <h1 className="font-mono text-xs font-medium uppercase tracking-widest text-[rgba(255,255,255,0.55)]">
          Persönliches Projektmanagement
        </h1>
      </div>
      <div className="flex items-center gap-2 lg:gap-3">
        {user && (
          <span className="hidden text-xs text-[rgba(255,255,255,0.45)] lg:inline">
            {user.first_name} {user.last_name}
          </span>
        )}
        <button
          className={`rounded-sm p-2 text-[rgba(255,255,255,0.55)] hover:bg-[rgba(0,158,227,0.10)] hover:text-white transition-colors ${
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
            className="relative rounded-sm p-2 text-[rgba(255,255,255,0.55)] hover:bg-[rgba(0,158,227,0.10)] hover:text-white transition-colors"
            title="Benachrichtigungen"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <BellIcon className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#DC2626] text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Dropdown */}
          {showNotifications && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowNotifications(false)}
              />
              <div className="absolute right-0 top-12 z-50 w-80 rounded-md border border-[rgba(0,0,0,0.08)] bg-white shadow-lg">
                <div className="border-b border-[rgba(0,0,0,0.08)] px-4 py-3">
                  <h3 className="font-mono text-xs font-medium uppercase tracking-wider text-inotec-muted">
                    Benachrichtigungen
                  </h3>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications?.results?.length ? (
                    notifications.results.slice(0, 10).map((n) => (
                      <div
                        key={n.id}
                        className="border-b border-[rgba(0,0,0,0.04)] px-4 py-3 hover:bg-surface-up cursor-pointer transition-colors"
                        onClick={() => {
                          markRead.mutate(n.id);
                          setShowNotifications(false);
                        }}
                      >
                        <p className="text-sm font-medium text-inotec-text">
                          {n.title}
                        </p>
                        <p className="text-xs text-inotec-muted mt-0.5 line-clamp-2">
                          {n.message}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="px-4 py-6 text-center text-sm text-inotec-subtle">
                      Keine neuen Benachrichtigungen
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
        <button
          className="rounded-sm p-2 text-[rgba(255,255,255,0.55)] hover:bg-[rgba(0,158,227,0.10)] hover:text-white transition-colors"
          title="Abmelden"
          onClick={handleLogout}
        >
          <ArrowRightStartOnRectangleIcon className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
