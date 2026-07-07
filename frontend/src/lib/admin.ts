import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  AdminActionResult,
  AdminActivityResponse,
  AdminCvTemplate,
  AdminCvTemplateListResponse,
  AdminCvTemplateUpdate,
  AdminEntriesResponse,
  AdminFeedbackItem,
  AdminFeedbackListResponse,
  AdminImpersonateResponse,
  AdminOverview,
  AdminUserDetail,
  AdminUserListResponse,
  EmailPreviewResponse,
  EmailTemplateSpec,
  SendEmailBulkDryRunResponse,
  SendEmailBulkResponse,
} from "@/types/admin";

const OVERVIEW_KEY = ["admin", "overview"] as const;
const USERS_KEY = (search: string | undefined, page: number) =>
  ["admin", "users", search ?? "", page] as const;
const USER_KEY = (id: string) => ["admin", "user", id] as const;
const ACTIVITY_KEY = (kind: string | undefined, status: string | undefined, page: number) =>
  ["admin", "activity", kind ?? "", status ?? "", page] as const;

export function useAdminOverview() {
  return useQuery({
    queryKey: OVERVIEW_KEY,
    queryFn: async () => {
      const { data } = await api.get<AdminOverview>("/admin/overview");
      return data;
    },
  });
}

export function useAdminUsers(params: { search?: string; page: number; size?: number }) {
  return useQuery({
    queryKey: USERS_KEY(params.search, params.page),
    queryFn: async () => {
      const { data } = await api.get<AdminUserListResponse>("/admin/users", {
        params: {
          search: params.search || undefined,
          page: params.page,
          size: params.size ?? 25,
        },
      });
      return data;
    },
  });
}

export function useAdminUser(id: string | undefined) {
  return useQuery({
    queryKey: USER_KEY(id ?? "none"),
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<AdminUserDetail>(`/admin/users/${id}`);
      return data;
    },
  });
}

export function useAdminUserEntries(
  id: string | undefined,
  kind?: string,
) {
  return useQuery({
    queryKey: ["admin", "user", id ?? "none", "entries", kind ?? ""] as const,
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<AdminEntriesResponse>(
        `/admin/users/${id}/entries`,
        { params: kind ? { kind } : undefined },
      );
      return data;
    },
  });
}

export function useAdminActivity(params: {
  kind?: string;
  status?: string;
  page: number;
  size?: number;
}) {
  return useQuery({
    queryKey: ACTIVITY_KEY(params.kind, params.status, params.page),
    queryFn: async () => {
      const { data } = await api.get<AdminActivityResponse>("/admin/activity", {
        params: {
          kind: params.kind || undefined,
          status: params.status || undefined,
          page: params.page,
          size: params.size ?? 50,
        },
      });
      return data;
    },
  });
}

export function useAdminEnableUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<AdminActionResult> => {
      const { data } = await api.post<AdminActionResult>(`/admin/users/${id}/enable`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
}

export function useAdminDisableUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<AdminActionResult> => {
      const { data } = await api.post<AdminActionResult>(`/admin/users/${id}/disable`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
}

export function useAdminResetWizard() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<AdminActionResult> => {
      const { data } = await api.post<AdminActionResult>(`/admin/users/${id}/reset-wizard`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
}

export function useAdminImpersonate() {
  return useMutation({
    mutationFn: async (id: string): Promise<AdminImpersonateResponse> => {
      const { data } = await api.post<AdminImpersonateResponse>(
        `/admin/users/${id}/impersonate`,
      );
      return data;
    },
  });
}

export function useAdminDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      confirmEmail,
    }: {
      id: string;
      confirmEmail: string;
    }): Promise<AdminActionResult> => {
      const { data } = await api.delete<AdminActionResult>(`/admin/users/${id}`, {
        data: { confirm_email: confirmEmail },
      });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
}

const CV_TEMPLATES_KEY = ["admin", "cv-templates"] as const;

export function useAdminCvTemplates() {
  return useQuery({
    queryKey: CV_TEMPLATES_KEY,
    queryFn: async () => {
      const { data } = await api.get<AdminCvTemplateListResponse>(
        "/admin/cv-templates",
      );
      return data;
    },
  });
}

export function useUpdateAdminCvTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      slug,
      payload,
    }: {
      slug: string;
      payload: AdminCvTemplateUpdate;
    }): Promise<AdminCvTemplate> => {
      const { data } = await api.patch<AdminCvTemplate>(
        `/admin/cv-templates/${slug}`,
        payload,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: CV_TEMPLATES_KEY }),
  });
}

// ---- Feedback triage ---------------------------------------------------

const FEEDBACK_KEY = (
  kind: string | undefined,
  resolved: boolean | undefined,
) => ["admin", "feedback", kind ?? "", resolved ?? "all"] as const;

export function useAdminFeedback(params: {
  kind?: string;
  resolved?: boolean;
  limit?: number;
}) {
  return useQuery({
    queryKey: FEEDBACK_KEY(params.kind, params.resolved),
    queryFn: async () => {
      const { data } = await api.get<AdminFeedbackListResponse>(
        "/admin/feedback",
        {
          params: {
            kind: params.kind || undefined,
            resolved: params.resolved,
            limit: params.limit ?? 200,
          },
        },
      );
      return data;
    },
  });
}

export function useAdminResolveFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<AdminFeedbackItem> => {
      const { data } = await api.post<AdminFeedbackItem>(
        `/admin/feedback/${id}/resolve`,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "feedback"] }),
  });
}

export function useAdminUnresolveFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<AdminFeedbackItem> => {
      const { data } = await api.post<AdminFeedbackItem>(
        `/admin/feedback/${id}/unresolve`,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "feedback"] }),
  });
}

// ---- Admin-triggered emails --------------------------------------------

const EMAIL_TEMPLATES_KEY = ["admin", "email-templates"] as const;

export function useAdminEmailTemplates() {
  return useQuery({
    queryKey: EMAIL_TEMPLATES_KEY,
    queryFn: async () => {
      const { data } = await api.get<EmailTemplateSpec[]>(
        "/admin/email-templates",
      );
      return data;
    },
    staleTime: Infinity,
  });
}

export function useAdminEmailPreview(
  userId: string | null,
  templateId: string | null,
) {
  return useQuery({
    queryKey: ["admin", "email-preview", userId, templateId] as const,
    enabled: !!userId && !!templateId,
    queryFn: async () => {
      const { data } = await api.get<EmailPreviewResponse>(
        `/admin/users/${userId}/email-preview`,
        { params: { template_id: templateId } },
      );
      return data;
    },
  });
}

export function useAdminSendEmail() {
  return useMutation({
    mutationFn: async ({
      userId,
      templateId,
    }: {
      userId: string;
      templateId: string;
    }): Promise<AdminActionResult> => {
      const { data } = await api.post<AdminActionResult>(
        `/admin/users/${userId}/send-email`,
        { template_id: templateId },
      );
      return data;
    },
  });
}

export function useAdminSendEmailBulk() {
  return useMutation({
    mutationFn: async ({
      userIds,
      templateId,
      dryRun,
    }: {
      userIds: string[];
      templateId: string;
      dryRun: boolean;
    }): Promise<SendEmailBulkResponse | SendEmailBulkDryRunResponse> => {
      const { data } = await api.post<
        SendEmailBulkResponse | SendEmailBulkDryRunResponse
      >("/admin/users/send-email-bulk", {
        user_ids: userIds,
        template_id: templateId,
        dry_run: dryRun,
      });
      return data;
    },
  });
}
