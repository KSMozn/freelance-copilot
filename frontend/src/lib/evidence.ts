import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { EvidenceReport } from "@/types/api";

const EVIDENCE_KEY = (jobId: string) => ["evidence", jobId] as const;

export function useJobEvidence(jobId: string | undefined, enabled: boolean = true) {
  return useQuery({
    queryKey: jobId ? EVIDENCE_KEY(jobId) : ["evidence", "none"],
    queryFn: async (): Promise<EvidenceReport> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.get<EvidenceReport>(`/jobs/${jobId}/evidence`);
      return data;
    },
    enabled: !!jobId && enabled,
    // Cheap, pure computation on the server — refetch on every Job Detail
    // mount so freshly-added portfolios/repos show up without a manual nudge.
    staleTime: 0,
  });
}

export { EVIDENCE_KEY };
