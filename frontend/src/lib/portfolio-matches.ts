import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type { PortfolioMatchesResponse } from "@/types/api";

const MATCHES_KEY = (jobId: string) => ["portfolio-matches", jobId] as const;

export function useMatchPortfolio(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<PortfolioMatchesResponse> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.post<PortfolioMatchesResponse>(
        `/jobs/${jobId}/match-portfolio`,
      );
      return data;
    },
    onSuccess: (data) => {
      if (!jobId) return;
      qc.setQueryData(MATCHES_KEY(jobId), data);
    },
  });
}

export { MATCHES_KEY };
