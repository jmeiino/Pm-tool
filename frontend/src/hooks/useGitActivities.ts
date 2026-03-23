import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, GitActivity } from "@/lib/types";

export function useGitActivities(projectId?: number) {
  const params = projectId ? `?project=${projectId}` : "";
  return useQuery({
    queryKey: ["git-activities", projectId],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<GitActivity>>(
        `/integrations/git-activities/${params}`
      );
      return data;
    },
  });
}
