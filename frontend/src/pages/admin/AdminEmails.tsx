import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import {
  useAdminEmailSends,
  useAdminEmailTemplates,
  useAdminSendEmail,
} from "@/lib/admin";
import { cn } from "@/lib/utils";
import type { AdminEmailSendRow } from "@/types/admin";

const STATUS_OPTIONS = [
  { value: "", label: "Any status" },
  { value: "ok", label: "Delivered" },
  { value: "error", label: "Failed" },
];

export function AdminEmailsPage() {
  const [templateId, setTemplateId] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const { data, isLoading } = useAdminEmailSends({
    templateId: templateId || undefined,
    status: status || undefined,
  });
  const { data: templates = [] } = useAdminEmailTemplates();
  const resend = useAdminSendEmail();
  const [resendingId, setResendingId] = useState<string | null>(null);

  const templateOptions = useMemo(
    () => [
      { value: "", label: "All templates" },
      ...templates.map((t) => ({ value: t.id, label: t.name })),
    ],
    [templates],
  );

  async function handleResend(row: AdminEmailSendRow) {
    if (!row.target_user_id) {
      toast.error("This send has no target user (deleted?)");
      return;
    }
    if (!row.template_id) {
      toast.error("Missing template id in the audit record");
      return;
    }
    setResendingId(row.id);
    try {
      await resend.mutateAsync({
        userId: row.target_user_id,
        templateId: row.template_id,
      });
      toast.success(`Resent to ${row.target_email ?? "user"}`);
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(msg ?? "Resend failed");
    } finally {
      setResendingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Emails</h1>
        <p className="text-sm text-muted-foreground">
          Every admin-triggered email send, newest first.
          {data && ` ${data.total.toLocaleString()} shown.`}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="w-72">
          <Select
            value={templateId}
            onChange={(e) => setTemplateId(e.target.value)}
            options={templateOptions}
            placeholder="All templates"
          />
        </div>
        <div className="w-40">
          <Select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            options={STATUS_OPTIONS}
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading…</div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">
              No email sends match those filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-muted/30 uppercase text-muted-foreground">
                    <Th>When</Th>
                    <Th>Template</Th>
                    <Th>Recipient</Th>
                    <Th>Actor</Th>
                    <Th>Status</Th>
                    <Th />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((r) => (
                    <tr key={r.id} className="border-b align-top hover:bg-muted/30">
                      <Td className="whitespace-nowrap">
                        {new Date(r.sent_at).toLocaleString()}
                      </Td>
                      <Td>
                        <div className="font-medium">
                          {r.template_name ?? (
                            <span className="text-muted-foreground italic">
                              unknown template
                            </span>
                          )}
                        </div>
                        <div className="font-mono text-[10px] text-muted-foreground">
                          {r.template_id || "—"}
                        </div>
                      </Td>
                      <Td>
                        {r.target_user_id && r.target_email ? (
                          <Link
                            to={`/users/${r.target_user_id}`}
                            className="text-primary hover:underline"
                          >
                            {r.target_email}
                          </Link>
                        ) : (
                          <span className="text-muted-foreground">
                            {r.target_email ?? "deleted user"}
                          </span>
                        )}
                        {r.target_full_name && (
                          <div className="text-[10px] text-muted-foreground">
                            {r.target_full_name}
                          </div>
                        )}
                      </Td>
                      <Td className="whitespace-nowrap text-muted-foreground">
                        {r.actor_email ?? "—"}
                      </Td>
                      <Td>
                        <span
                          className={cn(
                            "rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                            r.status === "error"
                              ? "bg-destructive/10 text-destructive"
                              : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
                          )}
                        >
                          {r.status === "ok" ? "Delivered" : "Failed"}
                        </span>
                        {r.error_message && (
                          <div className="mt-1 max-w-xs whitespace-pre-wrap text-[10px] text-destructive">
                            {r.error_message}
                          </div>
                        )}
                      </Td>
                      <Td className="whitespace-nowrap">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={
                            resendingId === r.id ||
                            !r.target_user_id ||
                            !r.template_id
                          }
                          onClick={() => void handleResend(r)}
                        >
                          {resendingId === r.id ? "Sending…" : "Resend"}
                        </Button>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="px-3 py-2 text-left font-medium">{children}</th>;
}

function Td({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={cn("px-3 py-2", className)}>{children}</td>;
}
