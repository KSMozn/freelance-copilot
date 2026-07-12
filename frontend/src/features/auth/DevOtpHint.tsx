import { FlaskConical } from "lucide-react";

import { extractOtpCode, useLatestDevEmails } from "@/features/auth/devMailbox";

/**
 * Dev-only helper shown on OTP entry steps. Locally the mock email provider
 * never sends real mail — codes are captured in the backend's dev mailbox
 * (var/dev-emails.jsonl, exposed at GET /dev/emails in development). This box
 * makes that impossible to miss: it polls the mailbox, shows the latest code,
 * and fills it in one click. Renders nothing in production builds, and
 * nothing against a backend that isn't running development + mock (the
 * endpoint 404s there).
 */
export function DevOtpHint({ email, onCode }: { email: string; onCode: (code: string) => void }) {
  const { data: emails } = useLatestDevEmails(email);

  if (!import.meta.env.DEV || emails === undefined) return null;

  const code = extractOtpCode(emails);

  return (
    <div className="rounded-md border border-dashed border-muted-foreground/30 bg-muted/40 p-3 text-xs text-muted-foreground">
      <p className="flex items-center gap-1.5 font-medium">
        <FlaskConical className="h-3.5 w-3.5" />
        Development mode — emails are captured locally and are not sent to your inbox.
      </p>
      {code ? (
        <p className="mt-2 flex items-center gap-2">
          Latest code:
          <span className="font-mono text-sm font-semibold tracking-widest text-foreground">
            {code}
          </span>
          <button
            type="button"
            className="rounded border border-muted-foreground/30 px-2 py-0.5 font-medium text-primary hover:bg-muted"
            onClick={() => onCode(code)}
          >
            Use code
          </button>
        </p>
      ) : (
        <p className="mt-1">
          No code captured yet for {email} — it appears here seconds after you request one.
        </p>
      )}
      <p className="mt-1.5 text-[11px] opacity-70">
        Mailbox: <code className="font-mono">backend/var/dev-emails.jsonl</code> · API:{" "}
        <code className="font-mono">GET /api/v1/dev/emails</code>
      </p>
    </div>
  );
}
