import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AnalyticsDashboardResponse } from "@/types/api";

const KEY = (params: Record<string, unknown>) => ["analytics", "dashboard", params] as const;

export function useAnalyticsDashboard(params: { from_date?: string; to_date?: string }) {
  const qParams = {
    from_date: params.from_date || undefined,
    to_date: params.to_date || undefined,
  };
  return useQuery({
    queryKey: KEY(qParams),
    queryFn: async () => {
      const { data } = await api.get<AnalyticsDashboardResponse>("/analytics/dashboard", {
        params: qParams,
      });
      return data;
    },
  });
}
