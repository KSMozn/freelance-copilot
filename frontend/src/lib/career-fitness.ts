import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface MarketSkill {
  name: string;
  market_count: number;
  raw_required: number;
  raw_preferred: number;
  in_your_pot: boolean;
  your_proficiency: number | null;
  your_evidence_count: number;
}

export interface SkillGap {
  name: string;
  market_count: number;
  current_proficiency: number | null;
  severity: number;
}

export interface FeedbackRow {
  name: string;
  score: number;
}

export interface RecurringGap {
  name: string;
  count: number;
  avg_importance: number;
}

export interface RepoSuggestion {
  repository_id: string;
  repository_name: string;
  suggestion: string;
  skills_covered: string[];
}

export interface CareerFitness {
  total_jobs_analyzed: number;
  total_applications: number;
  market_skills: MarketSkill[];
  top_gaps: SkillGap[];
  feedback: FeedbackRow[];
  recurring_gaps: RecurringGap[];
  repo_suggestions: RepoSuggestion[];
  domain_demand: [string, number][];
}

export function useCareerFitness() {
  return useQuery({
    queryKey: ["career-fitness"],
    queryFn: async () => {
      const { data } = await api.get<CareerFitness>("/career-fitness");
      return data;
    },
    staleTime: 1000 * 60 * 5,
  });
}
