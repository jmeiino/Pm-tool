import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, Project } from "@/lib/types";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Project>>("/projects/");
      return data;
    },
  });
}

export function useProject(id: number) {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: async () => {
      const { data } = await api.get<Project>(`/projects/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}
