import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";

import { api } from "@/app/apiClient";
import type { JobAnalysisResponse } from "@/features/professional/apiTypes";

const QUERY_KEY = (jobId: string) => ["job-analysis", jobId] as const;

export function useJobAnalysis(jobId: string | undefined) {
  return useQuery({
    queryKey: jobId ? QUERY_KEY(jobId) : ["job-analysis", "none"],
    enabled: !!jobId,
    queryFn: async (): Promise<JobAnalysisResponse | null> => {
      if (!jobId) return null;
      try {
        const { data } = await api.get<JobAnalysisResponse>(`/jobs/${jobId}/analysis`);
        return data;
      } catch (err) {
        if (isAxiosError(err) && err.response?.status === 404) return null;
        throw err;
      }
    },
    retry: false,
  });
}

export function useAnalyzeJob(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<JobAnalysisResponse> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.post<JobAnalysisResponse>(`/jobs/${jobId}/analyze`);
      return data;
    },
    onSuccess: (data) => {
      if (!jobId) return;
      qc.setQueryData(QUERY_KEY(jobId), data);
    },
  });
}
