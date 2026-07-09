import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type { JobImportResponse } from "@/types/api";

export function useImportJobFromImage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      file: File;
      sourceUrl?: string;
    }): Promise<JobImportResponse> => {
      const form = new FormData();
      form.append("image", input.file);
      if (input.sourceUrl) form.append("source_url", input.sourceUrl);

      const { data } = await api.post<JobImportResponse>(
        "/jobs/import-image",
        form,
        // axios will fill the boundary itself when given a FormData payload
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}
