import { FlaskConical } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { extractResetToken, useLatestDevEmails } from "@/features/auth/devMailbox";

/**
 * Dev-only companion to the forgot-password success screen. In production
 * the user gets only the generic "if this account exists…" message and must
 * open the emailed link; locally the mock provider captured that email, so
 * this box surfaces the reset link directly. Same double gate as DevOtpHint:
 * dev builds only, and the mailbox endpoint 404s outside development + mock.
 */
export function DevResetLinkHint({ email }: { email: string }) {
  const navigate = useNavigate();
  const { data: emails } = useLatestDevEmails(email);

  if (!import.meta.env.DEV || emails === undefined) return null;

  const token = extractResetToken(emails);

  return (
    <div className="mt-4 rounded-md border border-dashed border-muted-foreground/30 bg-muted/40 p-3 text-xs text-muted-foreground">
      <p className="flex items-center gap-1.5 font-medium">
        <FlaskConical className="h-3.5 w-3.5" />
        Development mode — the reset email was captured locally, not sent to your inbox.
      </p>
      {token ? (
        <p className="mt-2">
          <button
            type="button"
            className="rounded border border-muted-foreground/30 px-2 py-1 font-medium text-primary hover:bg-muted"
            onClick={() => navigate(`/reset-password#token=${token}`)}
          >
            Open reset link
          </button>
        </p>
      ) : (
        <p className="mt-1">
          No reset email captured yet for {email} — it appears here seconds after you request one.
        </p>
      )}
      <p className="mt-1.5 text-[11px] opacity-70">
        Mailbox: <code className="font-mono">backend/var/dev-emails.jsonl</code> · API:{" "}
        <code className="font-mono">GET /api/v1/dev/emails</code>
      </p>
    </div>
  );
}
