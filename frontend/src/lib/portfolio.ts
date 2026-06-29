import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  Portfolio,
  PortfolioCreate,
  PortfolioListResponse,
  PortfolioUpdate,
} from "@/types/api";

const LIST_KEY = (params: Record<string, unknown>) => ["portfolio", "list", params] as const;
const ITEM_KEY = (id: string | undefined) =>
  ["portfolio", "item", id ?? "none"] as const;

export function usePortfolioList(params: { search?: string; domain?: string }) {
  const qParams = {
    search: params.search?.trim() || undefined,
    domain: params.domain?.trim() || undefined,
  };
  return useQuery({
    queryKey: LIST_KEY(qParams),
    queryFn: async () => {
      const { data } = await api.get<PortfolioListResponse>("/portfolio", { params: qParams });
      return data;
    },
  });
}

export function usePortfolio(id: string | undefined) {
  return useQuery({
    queryKey: ITEM_KEY(id),
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<Portfolio>(`/portfolio/${id}`);
      return data;
    },
  });
}

export function useCreatePortfolio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PortfolioCreate): Promise<Portfolio> => {
      const { data } = await api.post<Portfolio>(
        "/portfolio",
        _strip(payload as unknown as Record<string, unknown>),
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useUpdatePortfolio(id: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PortfolioUpdate): Promise<Portfolio> => {
      if (!id) throw new Error("missing portfolio id");
      const { data } = await api.put<Portfolio>(`/portfolio/${id}`, _strip(payload));
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useDeletePortfolio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/portfolio/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

function _strip<T extends Record<string, unknown>>(obj: T): T {
  const out = { ...obj } as Record<string, unknown>;
  for (const k of Object.keys(out)) {
    if (out[k] === "" || out[k] === undefined) delete out[k];
  }
  return out as T;
}
