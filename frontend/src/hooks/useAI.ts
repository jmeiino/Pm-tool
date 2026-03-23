import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AIProviderInfo {
  name: string;
  model: string;
  configured: boolean;
  base_url?: string;
}

export interface AIProviderResponse {
  active_provider: string;
  active_model: string;
  providers: Record<string, AIProviderInfo>;
}

export function useAIProvider() {
  return useQuery({
    queryKey: ["ai-provider"],
    queryFn: async () => {
      const { data } = await api.get<AIProviderResponse>("/ai/ai/provider/");
      return data;
    },
  });
}
