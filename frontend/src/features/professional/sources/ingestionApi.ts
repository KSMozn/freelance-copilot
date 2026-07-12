import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";

// ---- Types --------------------------------------------------------------

export type ParseStatus = "pending" | "parsing" | "parsed" | "failed";
export type ContentItemType = "blog_post" | "talk" | "paper" | "open_source";

export interface CvUpload {
  id: string;
  user_id: string;
  persona_id: string | null;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  parse_status: ParseStatus;
  parse_error: string | null;
  extracted_structure: {
    summary?: string;
    skills?: string[];
    experiences?: Array<{
      company: string;
      role: string;
      location?: string | null;
      start_date?: string | null;
      end_date?: string | null;
      summary?: string | null;
      skills?: string[];
      achievements?: string[];
    }>;
  };
  extracted_skills: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface LinkedInSnapshot {
  id: string;
  user_id: string;
  parse_status: ParseStatus;
  parse_error: string | null;
  extracted_structure: CvUpload["extracted_structure"];
  parsed_at: string | null;
  created_at: string | null;
}

export interface Certificate {
  id: string;
  user_id: string;
  name: string;
  issuer: string;
  issued_date: string | null;
  expiry_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ContentItem {
  id: string;
  user_id: string;
  type: ContentItemType;
  title: string;
  url: string | null;
  published_date: string | null;
  summary: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// ---- CV uploads ---------------------------------------------------------

export function useCvUploads() {
  return useQuery({
    queryKey: ["cv-uploads"],
    queryFn: async () => {
      const { data } = await api.get<CvUpload[]>("/cv-uploads");
      return data;
    },
  });
}

export function useUploadCv() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, personaId }: { file: File; personaId?: string }) => {
      const form = new FormData();
      form.append("file", file);
      if (personaId) form.append("persona_id", personaId);
      const { data } = await api.post<CvUpload>("/cv-uploads", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cv-uploads"] });
    },
  });
}

export function usePasteCv() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { title: string; text: string; personaId?: string }) => {
      const { data } = await api.post<CvUpload>("/cv-uploads/paste", {
        title: payload.title,
        text: payload.text,
        persona_id: payload.personaId ?? null,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cv-uploads"] });
    },
  });
}

// ---- LinkedIn -----------------------------------------------------------

export function useImportLinkedIn() {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<LinkedInSnapshot>("/linkedin/import", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
  });
}

// ---- Certificates -------------------------------------------------------

export function useCertificates() {
  return useQuery({
    queryKey: ["certificates"],
    queryFn: async () => {
      const { data } = await api.get<Certificate[]>("/certificates");
      return data;
    },
  });
}

export function useCreateCertificate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name: string;
      issuer: string;
      issued_date?: string | null;
      expiry_date?: string | null;
      credential_id?: string | null;
      credential_url?: string | null;
    }) => {
      const { data } = await api.post<Certificate>("/certificates", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["certificates"] }),
  });
}

export function useDeleteCertificate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/certificates/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["certificates"] }),
  });
}

// ---- Content items ------------------------------------------------------

export function useContentItems() {
  return useQuery({
    queryKey: ["content-items"],
    queryFn: async () => {
      const { data } = await api.get<ContentItem[]>("/content-items");
      return data;
    },
  });
}

export function useCreateContentItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      type: ContentItemType;
      title: string;
      url?: string | null;
      published_date?: string | null;
      summary?: string | null;
    }) => {
      const { data } = await api.post<ContentItem>("/content-items", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["content-items"] }),
  });
}

export function useDeleteContentItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/content-items/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["content-items"] }),
  });
}
