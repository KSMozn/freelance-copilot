import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "@/app/apiClient";
import type {
  CvTemplateListResponse,
  DraftSummaryResponse,
  EmailCoachResponse,
  InternshipCoachRequest,
  InternshipCoachResponse,
  PhotoCoachResponse,
  ProofreadResponse,
  StudentEntry,
  StudentEntryUpsert,
  StudentProfile,
  StudentProfileUpdate,
  TextCoachResponse,
} from "@/types/student";

const PROFILE_KEY = ["student", "profile"] as const;
const ENTRIES_KEY = ["student", "entries"] as const;

export function useStudentProfile() {
  return useQuery({
    queryKey: PROFILE_KEY,
    queryFn: async () => {
      const { data } = await api.get<StudentProfile | null>("/students/profile");
      return data;
    },
  });
}

export function useUpdateStudentProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: StudentProfileUpdate): Promise<StudentProfile> => {
      const { data } = await api.put<StudentProfile>("/students/profile", payload);
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(PROFILE_KEY, data);
    },
  });
}

export function useUploadStudentPhoto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File): Promise<StudentProfile> => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<StudentProfile>(
        "/students/profile/photo",
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(PROFILE_KEY, data);
    },
  });
}

export function useStudentEntries() {
  return useQuery({
    queryKey: ENTRIES_KEY,
    queryFn: async () => {
      const { data } = await api.get<{ items: StudentEntry[] }>("/students/entries");
      return data.items;
    },
  });
}

export function useCreateStudentEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: StudentEntryUpsert): Promise<StudentEntry> => {
      const { data } = await api.post<StudentEntry>("/students/entries", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ENTRIES_KEY }),
  });
}

export function useUpdateStudentEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      payload,
    }: {
      id: string;
      payload: StudentEntryUpsert;
    }): Promise<StudentEntry> => {
      const { data } = await api.put<StudentEntry>(`/students/entries/${id}`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ENTRIES_KEY }),
  });
}

export function useDeleteStudentEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/students/entries/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ENTRIES_KEY }),
  });
}

export function useCoachEmail() {
  return useMutation({
    mutationFn: async (payload: {
      email: string;
      full_name?: string | null;
    }): Promise<EmailCoachResponse> => {
      const { data } = await api.post<EmailCoachResponse>(
        "/students/coach/email",
        payload,
      );
      return data;
    },
  });
}

export function useCoachPhoto() {
  return useMutation({
    mutationFn: async (file: File): Promise<PhotoCoachResponse> => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<PhotoCoachResponse>(
        "/students/coach/photo",
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
  });
}

export function useProofread() {
  return useMutation({
    mutationFn: async (): Promise<ProofreadResponse> => {
      const { data } = await api.get<ProofreadResponse>(
        "/students/coach/proofread",
      );
      return data;
    },
  });
}

export function useDraftSummary() {
  return useMutation({
    mutationFn: async (): Promise<DraftSummaryResponse> => {
      const { data } = await api.get<DraftSummaryResponse>(
        "/students/coach/draft-summary",
      );
      return data;
    },
  });
}

export function useCoachText() {
  return useMutation({
    mutationFn: async (payload: {
      field:
        | "summary"
        | "project_description"
        | "volunteer_description"
        | "internship_description";
      text: string;
      context?: Record<string, unknown>;
    }): Promise<TextCoachResponse> => {
      const { data } = await api.post<TextCoachResponse>(
        "/students/coach/text",
        payload,
      );
      return data;
    },
  });
}

export function useImproveInternship() {
  return useMutation({
    mutationFn: async (
      payload: InternshipCoachRequest,
    ): Promise<InternshipCoachResponse> => {
      const { data } = await api.post<InternshipCoachResponse>(
        "/students/coach/internship",
        payload,
      );
      return data;
    },
  });
}

// `<img src="/api/v1/students/profile/photo">` can't carry the JWT, so we
// fetch the photo through axios (which does) and turn the bytes into a
// blob: URL the <img> can load. The hook revokes the URL on unmount and
// re-fetches when the photo's file_id changes (i.e. after a re-upload).
export function useStudentPhotoBlob(photoFileId: string | null | undefined) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    let createdUrl: string | null = null;
    if (!photoFileId) {
      setUrl(null);
      return;
    }
    (async () => {
      try {
        const res = await api.get("/students/profile/photo", {
          responseType: "blob",
        });
        if (cancelled) return;
        createdUrl = URL.createObjectURL(res.data as Blob);
        setUrl(createdUrl);
      } catch {
        if (!cancelled) setUrl(null);
      }
    })();
    return () => {
      cancelled = true;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [photoFileId]);
  return url;
}

export async function fetchCvPreviewHtml(template?: string): Promise<string> {
  const params = template ? { template } : undefined;
  const { data } = await api.get<{ html: string }>("/students/cv/preview", {
    params,
  });
  return data.html;
}

export async function downloadStudentCv(template?: string): Promise<Blob> {
  const params = template ? { template } : undefined;
  const res = await api.get("/students/cv.pdf", {
    responseType: "blob",
    params,
  });
  return res.data as Blob;
}

export async function downloadStudentCvDocx(template?: string): Promise<Blob> {
  const params = template ? { template } : undefined;
  const res = await api.get("/students/cv.docx", {
    responseType: "blob",
    params,
  });
  return res.data as Blob;
}

export function useCvTemplates() {
  return useQuery({
    queryKey: ["student", "cv-templates"] as const,
    queryFn: async () => {
      const { data } = await api.get<CvTemplateListResponse>(
        "/students/cv-templates",
      );
      return data;
    },
    staleTime: 60_000,
  });
}
