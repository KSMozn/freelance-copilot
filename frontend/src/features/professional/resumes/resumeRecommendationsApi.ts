import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type { ResumeRecommendationsResponse } from "@/features/professional/apiTypes";

const KEY = (jobId: string) => ["resume-recommendations", jobId] as const;

export function useRecommendResume(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<ResumeRecommendationsResponse> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.post<ResumeRecommendationsResponse>(
        `/jobs/${jobId}/recommend-resume`,
      );
      return data;
    },
    onSuccess: (data) => {
      if (!jobId) return;
      qc.setQueryData(KEY(jobId), data);
    },
  });
}

export { KEY as RESUME_RECOMMENDATIONS_KEY };
