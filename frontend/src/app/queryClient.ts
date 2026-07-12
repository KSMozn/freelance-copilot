import { QueryClient } from "@tanstack/react-query";

import { advanceSessionBoundary } from "@/app/sessionBoundary";
import { advancePendingSaveBoundary } from "@/shared/lib/pendingSaves";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export function clearSessionCache(): void {
  advanceSessionBoundary();
  advancePendingSaveBoundary();
  queryClient.clear();
}
