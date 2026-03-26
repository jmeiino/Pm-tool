"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { todoCreateSchema, type TodoCreateInput } from "@/lib/schemas";
import type { PersonalTodo } from "@/lib/types";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface TodoCreateDialogProps {
  open: boolean;
  onClose: () => void;
}

export function TodoCreateDialog({ open, onClose }: TodoCreateDialogProps) {
  const queryClient = useQueryClient();

  const createTodo = useMutation({
    mutationFn: async (input: TodoCreateInput) => {
      const { data } = await api.post<PersonalTodo>("/todos/", input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      reset();
      onClose();
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TodoCreateInput>({
    resolver: zodResolver(todoCreateSchema),
    defaultValues: { priority: 3 },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Neue Aufgabe</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit((data) => {
          const cleaned = {
            ...data,
            due_date: data.due_date || null,
            estimated_hours: data.estimated_hours && !Number.isNaN(data.estimated_hours) ? data.estimated_hours : null,
          };
          createTodo.mutate(cleaned);
        })} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Titel *</label>
            <input
              {...register("title")}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="Was muss erledigt werden?"
            />
            {errors.title && (
              <p className="mt-1 text-xs text-red-600">{errors.title.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Beschreibung</label>
            <textarea
              {...register("description")}
              rows={3}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Priorität</label>
              <select
                {...register("priority", { valueAsNumber: true })}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              >
                <option value={1}>Dringend</option>
                <option value={2}>Hoch</option>
                <option value={3}>Mittel</option>
                <option value={4}>Niedrig</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Fällig am</label>
              <input
                type="date"
                {...register("due_date")}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Geschätzte Stunden
            </label>
            <input
              type="number"
              step="0.5"
              {...register("estimated_hours", { valueAsNumber: true })}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="z.B. 2.5"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Abbrechen
            </Button>
            <Button type="submit" disabled={createTodo.isPending}>
              {createTodo.isPending ? "Erstelle..." : "Erstellen"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
