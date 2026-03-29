"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useCreateAdminUser } from "@/hooks/useAdmin";

const schema = z.object({
  username: z.string().min(3, "Mind. 3 Zeichen"),
  email: z.string().email("Ungueltige E-Mail"),
  first_name: z.string().min(1, "Vorname erforderlich"),
  last_name: z.string().min(1, "Nachname erforderlich"),
  password: z.string().min(8, "Mind. 8 Zeichen"),
  is_staff: z.boolean().default(false),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
}

export function UserCreateDialog({ open, onClose }: Props) {
  const mutation = useCreateAdminUser();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { is_staff: false },
  });

  if (!open) return null;

  const onSubmit = (data: FormData) => {
    mutation.mutate(data, {
      onSuccess: () => {
        reset();
        onClose();
      },
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Neuer Benutzer
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
              Benutzername
            </label>
            <input
              {...register("username")}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
            {errors.username && (
              <p className="mt-1 text-xs text-red-500">
                {errors.username.message}
              </p>
            )}
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
              Passwort
            </label>
            <input
              {...register("password")}
              type="password"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              {...register("is_staff")}
              type="checkbox"
              id="is_staff"
              className="h-4 w-4 rounded border-gray-300 text-brand focus:ring-brand"
            />
            <label htmlFor="is_staff" className="text-sm text-gray-700">
              Admin-Rechte
            </label>
          </div>

          {mutation.isError && (
            <p className="text-sm text-red-500">
              Fehler beim Erstellen des Benutzers.
            </p>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Abbrechen
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Erstelle..." : "Erstellen"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
