import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export type InteractionChannel =
  | "email"
  | "linkedin"
  | "phone"
  | "in_person"
  | "other";
export type InteractionDirection = "inbound" | "outbound";
export type InterviewFormat =
  | "phone_screen"
  | "technical"
  | "system_design"
  | "behavioral"
  | "onsite"
  | "final"
  | "other";
export type InterviewOutcome = "pending" | "pass" | "fail" | "cancelled";

export interface RecruiterInteraction {
  id: string;
  application_id: string;
  user_id: string;
  channel: InteractionChannel;
  direction: InteractionDirection;
  occurred_at: string;
  contact_name: string | null;
  summary: string | null;
  raw_content: string | null;
  created_at: string | null;
}

export interface InterviewEvent {
  id: string;
  application_id: string;
  user_id: string;
  round_label: string;
  format: InterviewFormat;
  scheduled_at: string | null;
  duration_minutes: number | null;
  interviewer_names: string | null;
  interviewer_notes: string | null;
  my_feedback: string | null;
  outcome: InterviewOutcome;
  created_at: string | null;
  updated_at: string | null;
}

export interface FollowUpReminder {
  id: string;
  application_id: string;
  user_id: string;
  due_at: string;
  note: string;
  channel: InteractionChannel | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface ApplicationActivity {
  interactions: RecruiterInteraction[];
  interviews: InterviewEvent[];
  reminders: FollowUpReminder[];
}

// ---- Read ---------------------------------------------------------------

export function useApplicationActivity(applicationId: string | undefined) {
  return useQuery({
    queryKey: ["application-activity", applicationId],
    queryFn: async () => {
      const { data } = await api.get<ApplicationActivity>(
        `/applications/${applicationId}/activity`,
      );
      return data;
    },
    enabled: !!applicationId,
  });
}

export function useOpenReminders() {
  return useQuery({
    queryKey: ["tracker", "open-reminders"],
    queryFn: async () => {
      const { data } = await api.get<FollowUpReminder[]>(`/tracker/reminders`);
      return data;
    },
    staleTime: 1000 * 60,
  });
}

// ---- Recruiter interactions --------------------------------------------

export function useAddInteraction(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      channel: InteractionChannel;
      direction: InteractionDirection;
      occurred_at: string;
      contact_name?: string | null;
      summary?: string | null;
    }) => {
      const { data } = await api.post<RecruiterInteraction>(
        `/applications/${applicationId}/interactions`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] });
    },
  });
}

export function useDeleteInteraction(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/applications/${applicationId}/interactions/${id}`);
    },
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] }),
  });
}

// ---- Interview events --------------------------------------------------

export function useAddInterview(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      round_label: string;
      format: InterviewFormat;
      scheduled_at?: string | null;
      duration_minutes?: number | null;
      interviewer_names?: string | null;
    }) => {
      const { data } = await api.post<InterviewEvent>(
        `/applications/${applicationId}/interviews`,
        payload,
      );
      return data;
    },
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] }),
  });
}

export function useUpdateInterview(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      patch,
    }: {
      id: string;
      patch: Partial<Omit<InterviewEvent, "id" | "application_id" | "user_id" | "created_at" | "updated_at">>;
    }) => {
      const { data } = await api.patch<InterviewEvent>(
        `/applications/${applicationId}/interviews/${id}`,
        patch,
      );
      return data;
    },
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] }),
  });
}

export function useDeleteInterview(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/applications/${applicationId}/interviews/${id}`);
    },
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] }),
  });
}

// ---- Follow-up reminders -----------------------------------------------

export function useAddReminder(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      due_at: string;
      note: string;
      channel?: InteractionChannel | null;
    }) => {
      const { data } = await api.post<FollowUpReminder>(
        `/applications/${applicationId}/reminders`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] });
      qc.invalidateQueries({ queryKey: ["tracker", "open-reminders"] });
    },
  });
}

export function useCompleteReminder(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<FollowUpReminder>(
        `/applications/${applicationId}/reminders/${id}/complete`,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] });
      qc.invalidateQueries({ queryKey: ["tracker", "open-reminders"] });
    },
  });
}

export function useDeleteReminder(applicationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/applications/${applicationId}/reminders/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application-activity", applicationId] });
      qc.invalidateQueries({ queryKey: ["tracker", "open-reminders"] });
    },
  });
}
