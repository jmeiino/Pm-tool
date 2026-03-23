import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const priorityLabels: Record<number, string> = {
  1: "Dringend",
  2: "Hoch",
  3: "Mittel",
  4: "Niedrig",
};

export const priorityColors: Record<number, string> = {
  1: "bg-red-100 text-red-800",
  2: "bg-orange-100 text-orange-800",
  3: "bg-blue-100 text-blue-800",
  4: "bg-gray-100 text-gray-800",
};

export const statusLabels: Record<string, string> = {
  pending: "Offen",
  in_progress: "In Bearbeitung",
  done: "Erledigt",
  cancelled: "Abgebrochen",
  to_do: "Zu erledigen",
  active: "Aktiv",
  archived: "Archiviert",
  paused: "Pausiert",
};

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatTime(timeStr: string): string {
  return new Date(timeStr).toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
