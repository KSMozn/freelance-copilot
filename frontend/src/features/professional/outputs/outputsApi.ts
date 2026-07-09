import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";

export type OutputKind =
  | "upwork_proposal"
  | "cover_letter"
  | "recruiter_reply"
  | "linkedin_message"
  | "consulting_proposal"
  | "screening_answer"
  | "resume_tailored";

export type EvidenceType =
  "experience" | "project" | "repository" | "certificate" | "content_item" | "skill";

export interface Citation {
  claim: string;
  evidence_type: EvidenceType;
  evidence_id: string | null;
  evidence_label: string;
  snippet: string | null;
}

export interface Output {
  id: string;
  user_id: string;
  persona_id: string | null;
  job_id: string | null;
  kind: OutputKind;
  title: string | null;
  content_markdown: string;
  content_html: string | null;
  citations: Citation[];
  metadata: Record<string, unknown>;
  tone: string | null;
  ai_provider: string | null;
  ai_model: string | null;
  created_at: string | null;
}

export const OUTPUT_KIND_LABELS: Record<OutputKind, string> = {
  upwork_proposal: "Upwork proposal",
  cover_letter: "Cover letter",
  recruiter_reply: "Recruiter reply",
  linkedin_message: "LinkedIn message",
  consulting_proposal: "Consulting proposal",
  screening_answer: "Screening answer",
  resume_tailored: "Tailored resume",
};

export function useOutputsForJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["outputs", "job", jobId],
    queryFn: async () => {
      const { data } = await api.get<Output[]>("/outputs", {
        params: { job_id: jobId },
      });
      return data;
    },
    enabled: !!jobId,
  });
}

export function useGenerateOutput(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ kind, personaId }: { kind: OutputKind; personaId?: string | null }) => {
      const { data } = await api.post<Output>("/outputs", {
        kind,
        job_id: jobId,
        persona_id: personaId ?? null,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["outputs", "job", jobId] });
    },
  });
}

export function useDeleteOutput(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/outputs/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["outputs", "job", jobId] });
    },
  });
}
