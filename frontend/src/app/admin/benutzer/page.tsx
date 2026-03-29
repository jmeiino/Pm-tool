"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { PlusIcon, PencilSquareIcon } from "@heroicons/react/24/outline";
import { useAdminUsers, useDeactivateUser } from "@/hooks/useAdmin";
import { UserCreateDialog } from "@/components/admin/UserCreateDialog";
import { UserEditDialog } from "@/components/admin/UserEditDialog";
import { formatDate } from "@/lib/utils";
import type { AdminUser } from "@/lib/types";

export default function BenutzerverwaltungPage() {
  const { data, isLoading } = useAdminUsers();
  const deactivate = useDeactivateUser();
  const [showCreate, setShowCreate] = useState(false);
  const [editUser, setEditUser] = useState<AdminUser | null>(null);
  const [search, setSearch] = useState("");

  const users = data?.results ?? [];
  const filtered = search
    ? users.filter(
        (u) =>
          u.username.toLowerCase().includes(search.toLowerCase()) ||
          u.full_name.toLowerCase().includes(search.toLowerCase()) ||
          u.email.toLowerCase().includes(search.toLowerCase())
      )
    : users;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Benutzerverwaltung
          </h2>
          <p className="text-sm text-gray-500">
            Benutzer verwalten, erstellen und bearbeiten
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <PlusIcon className="h-4 w-4" />
          Neuer Benutzer
        </Button>
      </div>

      <Card>
        <div className="mb-4">
          <input
            type="text"
            placeholder="Benutzer suchen..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-xs font-semibold uppercase tracking-wide text-inotec-muted">
                  <th className="px-3 py-2">Benutzer</th>
                  <th className="px-3 py-2">E-Mail</th>
                  <th className="px-3 py-2">Rolle</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Projekte</th>
                  <th className="px-3 py-2">Erstellt</th>
                  <th className="px-3 py-2">Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-gray-100 hover:bg-surface-up"
                  >
                    <td className="px-3 py-3">
                      <div className="font-medium text-inotec-text">
                        {user.full_name}
                      </div>
                      <div className="text-xs text-inotec-muted">
                        @{user.username}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-inotec-body">
                      {user.email}
                    </td>
                    <td className="px-3 py-3">
                      <Badge variant={user.is_staff ? "brand" : "default"}>
                        {user.is_staff ? "Admin" : "Benutzer"}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge
                        variant={user.is_active ? "success" : "danger"}
                      >
                        {user.is_active ? "Aktiv" : "Inaktiv"}
                      </Badge>
                    </td>
                    <td className="px-3 py-3 text-inotec-body">
                      {user.project_count}
                    </td>
                    <td className="px-3 py-3 text-inotec-muted">
                      {formatDate(user.date_joined)}
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditUser(user)}
                          className="rounded p-1 text-inotec-muted hover:bg-brand-muted hover:text-brand"
                          title="Bearbeiten"
                        >
                          <PencilSquareIcon className="h-4 w-4" />
                        </button>
                        {user.is_active && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => {
                              if (
                                confirm(
                                  `Benutzer "${user.full_name}" wirklich deaktivieren?`
                                )
                              ) {
                                deactivate.mutate(user.id);
                              }
                            }}
                          >
                            Deaktivieren
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-3 py-8 text-center text-inotec-muted"
                    >
                      Keine Benutzer gefunden.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <UserCreateDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
      />
      <UserEditDialog
        open={!!editUser}
        onClose={() => setEditUser(null)}
        user={editUser}
      />
    </div>
  );
}
