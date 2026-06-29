import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  Resume,
  ResumeCreate,
  ResumeListResponse,
  ResumeUpdate,
} from "@/types/api";

const LIST_KEY = (params: Record<string, unknown>) => ["resumes", "list", params] as const;
const ITEM_KEY = (id: string | undefined) => ["resumes", "item", id ?? "none"] as const;

export function useResumeList(params: { search?: string; domain?: string; skill?: string }) {
  const qParams = {
    search: params.search?.trim() || undefined,
    domain: params.domain?.trim() || undefined,
    skill: params.skill?.trim() || undefined,
  };
  return useQuery({
    queryKey: LIST_KEY(qParams),
    queryFn: async () => {
      const { data } = await api.get<ResumeListResponse>("/resumes", { params: qParams });
      return data;
    },
  });
}

export function useResume(id: string | undefined) {
  return useQuery({
    queryKey: ITEM_KEY(id),
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<Resume>(`/resumes/${id}`);
      return data;
    },
  });
}

export function useCreateResume() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ResumeCreate): Promise<Resume> => {
      const { data } = await api.post<Resume>("/resumes", _strip(payload));
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });
}

export function useUpdateResume(id: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ResumeUpdate): Promise<Resume> => {
      if (!id) throw new Error("missing resume id");
      const { data } = await api.put<Resume>(`/resumes/${id}`, _strip(payload));
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });
}

export function useDeleteResume() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/resumes/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });
}

function _strip<T extends Record<string, unknown>>(obj: T): T {
  const out = { ...obj } as Record<string, unknown>;
  for (const k of Object.keys(out)) {
    if (out[k] === "" || out[k] === undefined) delete out[k];
  }
  return out as T;
}
