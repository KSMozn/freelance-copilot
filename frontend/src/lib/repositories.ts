import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  Repository,
  RepositoryImprovementsReport,
  RepositoryListResponse,
  RepositoryMatchesResponse,
} from "@/types/api";

const LIST_KEY = (search: string) => ["repositories", { search }] as const;
const MATCHES_KEY = (jobId: string) => ["repository-matches", jobId] as const;

export function useRepositoryList(args: { search?: string } = {}) {
  const search = args.search?.trim() ?? "";
  return useQuery({
    queryKey: LIST_KEY(search),
    queryFn: async () => {
      const params: Record<string, string | number> = { limit: 100 };
      if (search) params.search = search;
      const { data } = await api.get<RepositoryListResponse>("/repositories", { params });
      return data;
    },
  });
}

export function useRegisterRepository() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (github_url: string): Promise<Repository> => {
      const { data } = await api.post<Repository>("/repositories", {
        github_url,
        scan_now: true,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useRescanRepository() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<Repository> => {
      const { data } = await api.post<Repository>(`/repositories/${id}/rescan`);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useGenerateStarStory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<Repository> => {
      const { data } = await api.post<Repository>(`/repositories/${id}/star-story`);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useDeleteRepository() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/repositories/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useMatchRepositories(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<RepositoryMatchesResponse> => {
      if (!jobId) throw new Error("missing job id");
      const { data } = await api.post<RepositoryMatchesResponse>(
        `/jobs/${jobId}/match-repositories`,
      );
      return data;
    },
    onSuccess: (data) => {
      if (!jobId) return;
      qc.setQueryData(MATCHES_KEY(jobId), data);
    },
  });
}

export { MATCHES_KEY as REPOSITORY_MATCHES_KEY };

export function useRepositoryImprovements() {
  return useQuery({
    queryKey: ["repository-improvements"],
    queryFn: async (): Promise<RepositoryImprovementsReport> => {
      const { data } = await api.get<RepositoryImprovementsReport>(
        "/repositories/improvements",
      );
      return data;
    },
    staleTime: 0,
  });
}
