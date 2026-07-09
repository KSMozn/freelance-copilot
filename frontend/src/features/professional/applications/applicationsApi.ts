import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";

import { api } from "@/app/apiClient";
import type {
  Application,
  ApplicationDetailsUpdate,
  ApplicationHistoryEntry,
  ApplicationListResponse,
  ApplicationStatus,
} from "@/features/professional/apiTypes";

const LIST_KEY = (params: Record<string, unknown>) => ["applications", "list", params] as const;
const ITEM_KEY = (id: string | undefined) => ["applications", "item", id ?? "none"] as const;
const HISTORY_KEY = (id: string | undefined) => ["applications", "history", id ?? "none"] as const;
const BY_JOB_KEY = (jobId: string | undefined) =>
  ["applications", "by-job", jobId ?? "none"] as const;

export function useApplicationList(params: { status?: ApplicationStatus; search?: string }) {
  const qParams = {
    status: params.status,
    search: params.search?.trim() || undefined,
  };
  return useQuery({
    queryKey: LIST_KEY(qParams),
    queryFn: async () => {
      const { data } = await api.get<ApplicationListResponse>("/applications", {
        params: qParams,
      });
      return data;
    },
  });
}

export function useApplication(id: string | undefined) {
  return useQuery({
    queryKey: ITEM_KEY(id),
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<Application>(`/applications/${id}`);
      return data;
    },
  });
}

export function useApplicationHistory(id: string | undefined) {
  return useQuery({
    queryKey: HISTORY_KEY(id),
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<ApplicationHistoryEntry[]>(`/applications/${id}/history`);
      return data;
    },
  });
}

export function useApplicationForJob(jobId: string | undefined) {
  /** Lightweight helper: fetch all applications for a job and return the
   * most recent active one (or the most recent overall if none active). */
  return useQuery({
    queryKey: BY_JOB_KEY(jobId),
    enabled: !!jobId,
    retry: false,
    queryFn: async (): Promise<Application | null> => {
      if (!jobId) return null;
      try {
        const { data } = await api.get<ApplicationListResponse>("/applications", {
          params: { limit: 100 },
        });
        const forJob = data.items.filter((a) => a.job_id === jobId);
        if (!forJob.length) return null;
        const active = forJob.find(
          (a) => !["rejected", "withdrawn", "completed"].includes(a.status),
        );
        return active ?? forJob[0];
      } catch (err) {
        if (isAxiosError(err) && err.response?.status === 401) return null;
        throw err;
      }
    },
  });
}

export function useCreateApplicationFromProposal(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (proposalId: string): Promise<Application> => {
      const { data } = await api.post<Application>(`/applications/from-proposal/${proposalId}`, {
        status: "applied",
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      if (jobId) qc.invalidateQueries({ queryKey: BY_JOB_KEY(jobId) });
    },
  });
}

export function useUpdateApplicationStatus(applicationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { to_status: ApplicationStatus; note?: string }) => {
      if (!applicationId) throw new Error("missing application id");
      const { data } = await api.patch<Application>(
        `/applications/${applicationId}/status`,
        payload,
      );
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.setQueryData(ITEM_KEY(data.id), data);
      qc.invalidateQueries({ queryKey: HISTORY_KEY(data.id) });
    },
  });
}

export function useUpdateApplicationDetails(applicationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ApplicationDetailsUpdate) => {
      if (!applicationId) throw new Error("missing application id");
      const { data } = await api.patch<Application>(`/applications/${applicationId}`, payload);
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.setQueryData(ITEM_KEY(data.id), data);
    },
  });
}

export function useDeleteApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (applicationId: string) => {
      await api.delete(`/applications/${applicationId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });
}
