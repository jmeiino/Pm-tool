import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, GitActivity } from "@/lib/types";

export function useGitActivities(filters?: {
  project?: number;
  event_type?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.project) params.set("project", String(filters.project));
  if (filters?.event_type) params.set("event_type", filters.event_type);

  return useQuery({
    queryKey: ["git-activities", filters],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<GitActivity>>(
        `/integrations/git-activities/?${params.toString()}`
      );
      return data;
    },
  });
}
