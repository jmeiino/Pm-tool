import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, Sprint } from "@/lib/types";

export function useSprints(projectId?: number) {
  const params = projectId ? `?project=${projectId}` : "";
  return useQuery({
    queryKey: ["sprints", projectId],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Sprint>>(
        `/sprints/${params}`
      );
      return data;
    },
    enabled: !!projectId,
  });
}
