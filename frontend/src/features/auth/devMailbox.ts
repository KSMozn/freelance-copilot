import { useQuery } from "@tanstack/react-query";

import { api } from "@/app/apiClient";

export interface DevEmail {
  ts: string;
  to: string;
  subject: string;
  text_body: string;
  tags: Record<string, string>;
}

interface DevMailboxResponse {
  emails: DevEmail[];
}

/**
 * Poll the backend's dev-only mailbox (GET /dev/emails) for emails captured
 * by the mock provider. Two independent gates keep this out of production:
 * the query only runs in dev builds (`import.meta.env.DEV`), and the endpoint
 * 404s unless the backend runs ENVIRONMENT=development + EMAIL_PROVIDER=mock —
 * so against a real-sending backend the hook resolves to nothing and the dev
 * helpers render nothing.
 */
export function useLatestDevEmails(to: string) {
  return useQuery({
    queryKey: ["auth", "dev-emails", to],
    queryFn: async () => {
      const { data } = await api.get<DevMailboxResponse>("/dev/emails", {
        params: { to, limit: 5 },
      });
      return data.emails;
    },
    enabled: import.meta.env.DEV && to.length > 0,
    // Keeps the helper current after a "Resend" without any manual refresh.
    refetchInterval: 3_000,
    retry: false, // a 404 means "not a dev/mock backend" — don't hammer it
  });
}

export function extractOtpCode(emails: DevEmail[] | undefined): string | null {
  const otp = emails?.find((e) => e.tags?.kind === "otp");
  return otp ? (/\b(\d{6})\b/.exec(otp.subject)?.[1] ?? null) : null;
}

export function extractResetToken(emails: DevEmail[] | undefined): string | null {
  const reset = emails?.find((e) => e.tags?.kind === "password_reset");
  return reset ? (/#token=([A-Za-z0-9_-]+)/.exec(reset.text_body)?.[1] ?? null) : null;
}
