import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, CalendarEvent } from "@/lib/types";

export function useCalendarEvents(start?: string, end?: string) {
  const params = new URLSearchParams();
  if (start) params.set("start", start);
  if (end) params.set("end", end);

  return useQuery({
    queryKey: ["calendar-events", start, end],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<CalendarEvent>>(
        `/integrations/calendar-events/?${params.toString()}`
      );
      return data;
    },
    enabled: !!(start && end),
  });
}
