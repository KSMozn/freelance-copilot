import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";

import { api } from "@/app/apiClient";
import type { Proposal, ProposalReviewResult, ProposalUpdateRequest } from "@/features/professional/apiTypes";

const LATEST_KEY = (jobId: string) => ["proposals", "latest", jobId] as const;

export function useLatestProposal(jobId: string | undefined) {
  return useQuery({
    queryKey: jobId ? LATEST_KEY(jobId) : ["proposals", "latest", "none"],
    enabled: !!jobId,
    retry: false,
    queryFn: async (): Promise<Proposal | null> => {
      if (!jobId) return null;
      try {
        const { data } = await api.get<Proposal>(`/jobs/${jobId}/proposals/latest`);
        return data;
      } catch (err) {
        if (isAxiosError(err) && err.response?.status === 404) return null;
        throw err;
      }
    },
  });
}

export function useGenerateProposal(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<Proposal> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.post<Proposal>(`/jobs/${jobId}/proposals/generate`, {});
      return data;
    },
    onSuccess: (data) => {
      if (!jobId) return;
      qc.setQueryData(LATEST_KEY(jobId), data);
    },
  });
}

export function useUpdateProposal(jobId: string | undefined, proposalId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ProposalUpdateRequest): Promise<Proposal> => {
      if (!proposalId) throw new Error("missing proposal id");
      const { data } = await api.put<Proposal>(`/proposals/${proposalId}`, payload);
      return data;
    },
    onSuccess: (data) => {
      if (jobId) qc.setQueryData(LATEST_KEY(jobId), data);
    },
  });
}

export function useReviewProposal(jobId: string | undefined, proposalId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<ProposalReviewResult> => {
      if (!proposalId) throw new Error("missing proposal id");
      const { data } = await api.post<ProposalReviewResult>(
        `/proposals/${proposalId}/review`,
      );
      return data;
    },
    onSuccess: (review) => {
      if (!jobId) return;
      const cache = qc.getQueryData<Proposal | null>(LATEST_KEY(jobId));
      if (cache) {
        qc.setQueryData(LATEST_KEY(jobId), {
          ...cache,
          quality_score: review.quality_score,
          quality_breakdown: review.quality_breakdown,
          quality_warnings: review.warnings,
        });
      }
    },
  });
}

export function useDeleteProposal(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (proposalId: string): Promise<void> => {
      await api.delete(`/proposals/${proposalId}`);
    },
    onSuccess: () => {
      if (jobId) qc.removeQueries({ queryKey: LATEST_KEY(jobId) });
    },
  });
}
