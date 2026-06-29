import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CompanyResearch } from "@/types/api";

export function useResearchClient(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (url: string): Promise<CompanyResearch> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.post<CompanyResearch>(
        `/jobs/${jobId}/research`,
        { url },
      );
      return data;
    },
    onSuccess: () => {
      if (!jobId) return;
      // Job-level fields refresh so the new client_research lands on the card.
      qc.invalidateQueries({ queryKey: ["job", jobId] });
    },
  });
}
