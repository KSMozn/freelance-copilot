import { useQuery } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type { JobConfidenceReport } from "@/features/professional/apiTypes";

const CONFIDENCE_KEY = (jobId: string) => ["confidence", jobId] as const;

export function useJobConfidence(jobId: string | undefined, enabled: boolean = true) {
  return useQuery({
    queryKey: jobId ? CONFIDENCE_KEY(jobId) : ["confidence", "none"],
    queryFn: async (): Promise<JobConfidenceReport> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.get<JobConfidenceReport>(`/jobs/${jobId}/confidence`);
      return data;
    },
    enabled: !!jobId && enabled,
    staleTime: 0,
  });
}

export { CONFIDENCE_KEY };
