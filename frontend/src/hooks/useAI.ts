import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AIProviderDetail {
  name: string;
  model: string;
  api_key_set: boolean;
  base_url?: string;
}

export interface AIProviderResponse {
  active_provider: string;
  active_model: string;
  providers: Record<string, AIProviderDetail>;
}

export interface AISettingsUpdate {
  active_provider?: string;
  claude?: { api_key?: string; model?: string };
  ollama?: { base_url?: string; model?: string };
  openrouter?: { api_key?: string; model?: string };
}

export function useAIProvider() {
  return useQuery({
    queryKey: ["ai-provider"],
    queryFn: async () => {
      const { data } = await api.get<AIProviderResponse>("/ai/provider/");
      return data;
    },
  });
}

export function useUpdateAIProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (update: AISettingsUpdate) => {
      const { data } = await api.patch<AIProviderResponse>(
        "/ai/provider/",
        update
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-provider"] });
    },
  });
}
