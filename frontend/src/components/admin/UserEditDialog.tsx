"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useUpdateAdminUser } from "@/hooks/useAdmin";
import type { AdminUser } from "@/lib/types";

const schema = z.object({
  first_name: z.string().min(1, "Vorname erforderlich"),
  last_name: z.string().min(1, "Nachname erforderlich"),
  email: z.string().email("Ungueltige E-Mail"),
  is_staff: z.boolean(),
  is_active: z.boolean(),
  timezone: z.string(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  user: AdminUser | null;
}

export function UserEditDialog({ open, onClose, user }: Props) {
  const mutation = useUpdateAdminUser();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: user
      ? {
          first_name: user.first_name,
          last_name: user.last_name,
          email: user.email,
          is_staff: user.is_staff,
          is_active: user.is_active,
          timezone: user.timezone,
        }
      : undefined,
  });

  if (!open || !user) return null;

  const onSubmit = (data: FormData) => {
    mutation.mutate(
      { id: user.id, ...data },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Benutzer bearbeiten
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Vorname
              </label>
              <input
                {...register("first_name")}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              />
              {errors.first_name && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.first_name.message}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Nachname
              </label>
              <input
                {...register("last_name")}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              />
              {errors.last_name && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.last_name.message}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              E-Mail
            </label>
            <input
              {...register("email")}
              type="email"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-500">
                {errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Zeitzone
            </label>
            <input
              {...register("timezone")}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <input
                {...register("is_staff")}
                type="checkbox"
                id="edit_is_staff"
                className="h-4 w-4 rounded border-gray-300 text-brand focus:ring-brand"
              />
              <label htmlFor="edit_is_staff" className="text-sm text-gray-700">
                Admin-Rechte
              </label>
            </div>
            <div className="flex items-center gap-2">
              <input
                {...register("is_active")}
                type="checkbox"
                id="edit_is_active"
                className="h-4 w-4 rounded border-gray-300 text-brand focus:ring-brand"
              />
              <label
                htmlFor="edit_is_active"
                className="text-sm text-gray-700"
              >
                Aktiv
              </label>
            </div>
          </div>

          {mutation.isError && (
            <p className="text-sm text-red-500">
              Fehler beim Speichern.
            </p>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Abbrechen
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Speichere..." : "Speichern"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
