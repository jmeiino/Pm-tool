"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/Button";
import { useCreateIssue } from "@/hooks/useIssues";
import { issueCreateSchema, type IssueCreateInput } from "@/lib/schemas";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface IssueCreateDialogProps {
  projectId: number;
  open: boolean;
  onClose: () => void;
}

export function IssueCreateDialog({
  projectId,
  open,
  onClose,
}: IssueCreateDialogProps) {
  const createIssue = useCreateIssue();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<IssueCreateInput>({
    resolver: zodResolver(issueCreateSchema),
    defaultValues: { project: projectId, issue_type: "task", priority: "medium" },
  });

  const onSubmit = (data: IssueCreateInput) => {
    const cleaned = {
      ...data,
      due_date: data.due_date || null,
      story_points: data.story_points && !Number.isNaN(data.story_points) ? data.story_points : null,
    };
    createIssue.mutate(cleaned as IssueCreateInput, {
      onSuccess: () => {
        reset();
        onClose();
      },
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-md bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Neues Issue</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Titel *
            </label>
            <input
              {...register("title")}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="Issue-Titel"
            />
            {errors.title && (
              <p className="mt-1 text-xs text-red-600">{errors.title.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Beschreibung
            </label>
            <textarea
              {...register("description")}
              rows={3}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="Beschreibung..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Typ
              </label>
              <select
                {...register("issue_type")}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              >
                <option value="task">Aufgabe</option>
                <option value="story">Story</option>
                <option value="bug">Bug</option>
                <option value="epic">Epic</option>
                <option value="subtask">Unteraufgabe</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Priorität
              </label>
              <select
                {...register("priority")}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              >
                <option value="highest">Höchste</option>
                <option value="high">Hoch</option>
                <option value="medium">Mittel</option>
                <option value="low">Niedrig</option>
                <option value="lowest">Niedrigste</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Story Points
              </label>
              <input
                type="number"
                {...register("story_points", { valueAsNumber: true })}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Fällig am
              </label>
              <input
                type="date"
                {...register("due_date")}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Abbrechen
            </Button>
            <Button type="submit" disabled={createIssue.isPending}>
              {createIssue.isPending ? "Erstelle..." : "Erstellen"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
