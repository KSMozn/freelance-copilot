import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type { PortfolioStory } from "@/features/professional/apiTypes";

const STORY_KEY = (jobId: string) => ["portfolio-story", jobId] as const;

export function usePortfolioStory(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<PortfolioStory | null> => {
      if (!jobId) throw new Error("missing job id");
      const resp = await api.post<PortfolioStory>(
        `/jobs/${jobId}/portfolio-story`,
        undefined,
        { validateStatus: (s) => s === 200 || s === 204 },
      );
      if (resp.status === 204) return null;
      return resp.data;
    },
    onSuccess: (data) => {
      if (!jobId) return;
      qc.setQueryData(STORY_KEY(jobId), data);
    },
  });
}

export { STORY_KEY as PORTFOLIO_STORY_KEY };
