import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import { useAuthStore } from "@/features/auth/authStore";

export type ProposalTone =
  | "pragmatic"
  | "technical_deep"
  | "executive"
  | "consultative"
  | "empathetic";

export interface PersonaArchetype {
  id: string;
  slug: string;
  name: string;
  description: string;
  default_weights: Record<string, number>;
  default_skill_category_weights: Record<string, number>;
  default_proposal_tone: ProposalTone;
  default_target_roles: string[];
  default_seniority_band: string | null;
  sort_order: number;
}

export interface Persona {
  id: string;
  user_id: string;
  archetype_id: string;
  name: string;
  target_role: string | null;
  target_seniority: string | null;
  weights: Record<string, number>;
  skill_category_weights: Record<string, number>;
  proposal_tone: ProposalTone | null;
  strategic_priorities: string[];
  pinned_experience_ids: string[];
  pinned_project_ids: string[];
  pinned_skill_ids: string[];
  accent_color: string | null;
  is_default: boolean;
  is_archived: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface PersonaCreatePayload {
  archetype_slug: string;
  name?: string | null;
  target_role?: string | null;
  is_default?: boolean;
}

export function usePersonaArchetypes() {
  return useQuery({
    queryKey: ["persona-archetypes"],
    queryFn: async () => {
      const { data } = await api.get<PersonaArchetype[]>("/personas/archetypes");
      return data;
    },
    staleTime: 1000 * 60 * 60, // archetypes are seeded, change rarely
  });
}

export function usePersonas() {
  return useQuery({
    queryKey: ["personas"],
    queryFn: async () => {
      const { data } = await api.get<Persona[]>("/personas");
      return data;
    },
  });
}

export function useCurrentPersona() {
  const setActivePersonaId = useAuthStore((s) => s.setActivePersonaId);
  const query = useQuery({
    queryKey: ["personas", "current"],
    queryFn: async () => {
      const { data } = await api.get<Persona>("/personas/current");
      return data;
    },
  });

  // Mirror the server-resolved default into the auth store so any other
  // component can pick it up synchronously.
  if (query.data && useAuthStore.getState().activePersonaId == null) {
    setActivePersonaId(query.data.id);
  }
  return query;
}

export function useCreatePersona() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PersonaCreatePayload) => {
      const { data } = await api.post<Persona>("/personas", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["personas"] });
      qc.invalidateQueries({ queryKey: ["personas", "current"] });
    },
  });
}

export function useSetDefaultPersona() {
  const qc = useQueryClient();
  const setActivePersonaId = useAuthStore((s) => s.setActivePersonaId);
  return useMutation({
    mutationFn: async (personaId: string) => {
      const { data } = await api.post<Persona>(
        `/personas/${personaId}/set-default`,
      );
      return data;
    },
    onSuccess: (data) => {
      setActivePersonaId(data.id);
      qc.invalidateQueries({ queryKey: ["personas"] });
      qc.invalidateQueries({ queryKey: ["personas", "current"] });
    },
  });
}

export function useDeletePersona() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (personaId: string) => {
      await api.delete(`/personas/${personaId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["personas"] });
      qc.invalidateQueries({ queryKey: ["personas", "current"] });
    },
  });
}
