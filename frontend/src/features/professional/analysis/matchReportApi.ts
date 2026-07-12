import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";

export type InterviewChance = "low" | "medium" | "high";
export type RecommendationKind =
  | "project_to_build"
  | "certification"
  | "learning_resource"
  | "github_enhancement"
  | "experience_to_emphasize";

export interface GapRecommendation {
  skill: string;
  kind: RecommendationKind;
  suggestion: string;
  effort_estimate: string;
  priority: number;
}

export interface MatchReport {
  id: string;
  user_id: string;
  job_id: string;
  persona_id: string | null;
  overall_match: number;
  technical_fit: number;
  architecture_fit: number;
  domain_fit: number;
  leadership_fit: number | null;
  soft_skills_fit: number | null;
  interview_chance: InterviewChance;
  missing_critical_skills: Array<{
    name: string;
    importance: number;
    status: string;
  }>;
  missing_recommendations: GapRecommendation[];
  rationale: string[];
  profile_version: string | null;
  computed_at: string | null;
}

export function useMatchReport(jobId: string | undefined, personaId?: string | null) {
  return useQuery({
    queryKey: ["match-report", jobId, personaId ?? "default"],
    queryFn: async () => {
      const params = personaId ? `?persona_id=${personaId}` : "";
      const { data } = await api.post<MatchReport>(`/jobs/${jobId}/match-report${params}`);
      return data;
    },
    enabled: !!jobId,
    // The endpoint is POST-as-GET (it computes-or-returns) — let it run once
    // per (job, persona) per session.
    staleTime: 1000 * 60 * 10,
  });
}

export function useRebuildMatchReport(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (personaId?: string | null) => {
      const params = personaId ? `?persona_id=${personaId}&force=true` : `?force=true`;
      const { data } = await api.post<MatchReport>(`/jobs/${jobId}/match-report${params}`);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["match-report", jobId] });
    },
  });
}
