import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { AlertTriangle, Loader2, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  useAdminDeleteUser,
  useAdminDisableUser,
  useAdminEmailPreview,
  useAdminEmailTemplates,
  useAdminEnableUser,
  useAdminImpersonate,
  useAdminResetWizard,
  useAdminSendEmail,
  useAdminUser,
  useAdminUserEntries,
} from "@/lib/admin";

export function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: user, isLoading } = useAdminUser(id);
  const enable = useAdminEnableUser();
  const disable = useAdminDisableUser();
  const reset = useAdminResetWizard();
  const impersonate = useAdminImpersonate();
  const del = useAdminDeleteUser();
  const navigate = useNavigate();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleteEmail, setDeleteEmail] = useState("");

  if (isLoading || !user) {
    return <div className="text-sm text-muted-foreground">Loading…</div>;
  }

  async function doImpersonate() {
    if (!id || !user) return;
    try {
      const res = await impersonate.mutateAsync(id);
      // We're on admin.personaarmory.com. The student app lives at
      // app.personaarmory.com — a different origin with its own
      // localStorage. Hand off the impersonation tokens via URL fragment
      // (never sent to the server, doesn't hit history). The app-side
      // `/impersonate` route decodes and stores them.
      const payload = {
        id: res.target_user_id,
        email: res.target_user_email,
        full_name: user.full_name,
        persona_kind: user.persona_kind,
        created_at: user.created_at,
        access_token: res.access_token,
        refresh_token: res.refresh_token,
      };
      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
      const appOrigin =
        window.location.hostname === "admin.personaarmory.com"
          ? "https://app.personaarmory.com"
          : window.location.origin.replace(/(^https?:\/\/)admin\./, "$1app.");
      window.location.href = `${appOrigin}/impersonate#p=${encoded}`;
    } catch {
      toast.error("Impersonation failed");
    }
  }

  async function confirmDelete() {
    if (!id) return;
    try {
      await del.mutateAsync({ id, confirmEmail: deleteEmail });
      toast.success("User deleted");
      navigate("/users");
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "Could not delete");
    }
  }

  // No self-check needed — admin identity space is fully separate from
  // the users table, so actor.id can never equal a users.id.
  const isSelf = false;

  return (
    <div className="space-y-4">
      <div>
        <Link
          to="/users"
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          ← Users
        </Link>
        <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold">
          {user.email}
          {user.is_superuser && (
            <span className="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-semibold uppercase text-primary">
              Super
            </span>
          )}
          {!user.is_active && (
            <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-xs font-semibold uppercase text-destructive">
              Disabled
            </span>
          )}
        </h1>
        <p className="text-sm text-muted-foreground">
          {user.full_name ?? "no name"} · Persona: {user.persona_kind} · Joined{" "}
          {new Date(user.created_at).toLocaleDateString()}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {user.is_active ? (
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                if (!id) return;
                try {
                  await disable.mutateAsync(id);
                  toast.success("Disabled");
                } catch {
                  toast.error("Failed");
                }
              }}
              disabled={disable.isPending || isSelf}
            >
              Disable
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                if (!id) return;
                try {
                  await enable.mutateAsync(id);
                  toast.success("Enabled");
                } catch {
                  toast.error("Failed");
                }
              }}
              disabled={enable.isPending}
            >
              Enable
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              if (!id) return;
              try {
                await reset.mutateAsync(id);
                toast.success("Wizard progress reset");
              } catch (err) {
                const msg = (err as { response?: { data?: { detail?: string } } })
                  ?.response?.data?.detail;
                toast.error(msg ?? "Failed");
              }
            }}
            disabled={reset.isPending || !user.student}
          >
            Reset wizard
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void doImpersonate()}
            disabled={impersonate.isPending || isSelf}
          >
            View as user
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setConfirmingDelete(true)}
            disabled={del.isPending || isSelf}
          >
            Delete…
          </Button>
        </CardContent>
      </Card>

      {id && <SendEmailCard userId={id} userEmail={user.email} />}

      {id && user.student && <InternshipAuditPanel userId={id} />}

      {confirmingDelete && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-base text-destructive">
              Delete {user.email}?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">
              This deletes the user and all cascading data (profile, entries,
              uploaded files). This cannot be undone. Type the user's email to
              confirm.
            </p>
            <Input
              value={deleteEmail}
              onChange={(e) => setDeleteEmail(e.target.value)}
              placeholder={user.email}
            />
            <div className="flex gap-2">
              <Button
                variant="destructive"
                size="sm"
                onClick={() => void confirmDelete()}
                disabled={
                  del.isPending ||
                  deleteEmail.trim().toLowerCase() !== user.email.toLowerCase()
                }
              >
                Delete permanently
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setConfirmingDelete(false);
                  setDeleteEmail("");
                }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <Row k="ID" v={user.id} mono />
            <Row k="Email" v={user.email} />
            <Row k="Persona" v={user.persona_kind} />
            <Row k="Active" v={user.is_active ? "Yes" : "No"} />
            <Row k="Superuser" v={user.is_superuser ? "Yes" : "No"} />
            <Row
              k="Email verified"
              v={user.email_verified_at ? new Date(user.email_verified_at).toLocaleString() : "No"}
            />
            <Row
              k="Last login"
              v={user.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}
            />
            <Row k="Joined" v={new Date(user.created_at).toLocaleString()} />
          </CardContent>
        </Card>

        {user.student && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Student profile</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <Row k="Name" v={user.student.full_name ?? "—"} />
              <Row k="CV email" v={user.student.professional_email ?? "—"} />
              <Row k="Phone" v={user.student.phone ?? "—"} />
              <Row k="Location" v={user.student.location ?? "—"} />
              <Row k="Date of birth" v={user.student.date_of_birth ?? "—"} />
              <Row k="CV template" v={user.student.cv_template_slug ?? "—"} />
              <Row k="University" v={user.student.college ?? "—"} />
              <Row k="Department" v={user.student.department ?? "—"} />
              <Row k="Degree" v={user.student.degree ?? "—"} />
              <Row k="Major" v={user.student.major ?? "—"} />
              <Row k="Grad. year" v={user.student.graduation_year?.toString() ?? "—"} />
              <Row k="GPA" v={user.student.gpa ?? "—"} />
              <Row
                k="Wizard"
                v={`${user.student.completed_steps.length}/13 · current: ${user.student.current_step ?? "none"}`}
              />
              <Row k="Entries" v={user.student.entries_count.toString()} />
              {user.student.headline && <Row k="Headline" v={user.student.headline} />}
              {user.student.summary && (
                <div className="mt-2">
                  <div className="text-xs text-muted-foreground">Summary</div>
                  <div className="mt-1 whitespace-pre-wrap rounded bg-muted/30 p-2 text-xs">
                    {user.student.summary}
                  </div>
                </div>
              )}
              {Object.keys(user.student.entries_by_kind).length > 0 && (
                <div className="mt-2">
                  <div className="text-xs text-muted-foreground">Entries by kind</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {Object.entries(user.student.entries_by_kind).map(([k, c]) => (
                      <span
                        key={k}
                        className="rounded bg-muted px-1.5 py-0.5 text-[10px]"
                      >
                        {k}: {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="grid grid-cols-[110px_1fr] gap-2 border-b py-1.5 last:border-none">
      <div className="text-xs text-muted-foreground">{k}</div>
      <div className={mono ? "font-mono text-xs" : ""}>{v}</div>
    </div>
  );
}

// ---- Send email card + preview modal -----------------------------------

function SendEmailCard({
  userId,
  userEmail,
}: {
  userId: string;
  userEmail: string;
}) {
  const { data: templates } = useAdminEmailTemplates();
  const [templateId, setTemplateId] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);

  const options =
    (templates ?? []).map((t) => ({ value: t.id, label: t.name })) ?? [];
  const chosen = (templates ?? []).find((t) => t.id === templateId) ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Mail className="h-4 w-4" /> Send templated email
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <Label className="text-xs" htmlFor="tpl">Template</Label>
          <Select
            id="tpl"
            value={templateId}
            onChange={(e) => setTemplateId(e.target.value)}
            options={options}
            placeholder={templates ? "Pick a template…" : "Loading…"}
          />
          {chosen && (
            <p className="text-xs text-muted-foreground">
              {chosen.description}
              {chosen.audience_hint && (
                <>
                  {" "}
                  <span className="italic">{chosen.audience_hint}</span>
                </>
              )}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3">
          <p className="text-xs text-muted-foreground">
            Will be sent to <span className="font-medium">{userEmail}</span>.
          </p>
          <Button
            variant="brand"
            size="sm"
            onClick={() => setPreviewOpen(true)}
            disabled={!templateId}
          >
            Preview &amp; send
          </Button>
        </div>
      </CardContent>
      {previewOpen && templateId && (
        <EmailPreviewModal
          userId={userId}
          templateId={templateId}
          onClose={() => setPreviewOpen(false)}
        />
      )}
    </Card>
  );
}

function EmailPreviewModal({
  userId,
  templateId,
  onClose,
}: {
  userId: string;
  templateId: string;
  onClose: () => void;
}) {
  const { data: preview, isLoading, error } = useAdminEmailPreview(userId, templateId);
  const send = useAdminSendEmail();

  async function submit() {
    try {
      await send.mutateAsync({ userId, templateId });
      toast.success("Email sent.");
      onClose();
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(msg ?? "Failed to send.");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl border bg-background shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="text-sm font-semibold">Email preview</div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Rendering preview…
            </div>
          ) : error || !preview ? (
            <div className="p-6 text-sm text-destructive">Couldn't load preview.</div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-[110px_1fr] gap-2 text-sm">
                <div className="text-xs text-muted-foreground">To</div>
                <div>
                  {preview.recipient_name && (
                    <span className="font-medium">
                      {preview.recipient_name}
                    </span>
                  )}{" "}
                  &lt;{preview.recipient_email}&gt;
                </div>
                <div className="text-xs text-muted-foreground">Subject</div>
                <div className="font-medium">{preview.subject}</div>
              </div>
              {preview.recent_send_at && (
                <div className="flex gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs">
                  <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                  <div>
                    This template was already sent to this user on{" "}
                    <span className="font-medium">
                      {new Date(preview.recent_send_at).toLocaleString()}
                    </span>
                    . Sending again is allowed — just double-check first.
                  </div>
                </div>
              )}
              <iframe
                title="Email preview"
                srcDoc={preview.html}
                sandbox="allow-same-origin"
                className="h-[520px] w-full rounded border bg-white"
              />
            </div>
          )}
        </div>
        <div className="flex items-center justify-end gap-2 border-t px-4 py-3">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="brand"
            size="sm"
            onClick={submit}
            disabled={send.isPending || !preview}
          >
            {send.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Send email
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---- Internship audit panel --------------------------------------------
//
// Read-only view of the raw student input + LLM-generated summary +
// bullets. Lets admins spot hallucinated content or empty drafts
// without impersonating the student.

function InternshipAuditPanel({ userId }: { userId: string }) {
  const { data, isLoading } = useAdminUserEntries(userId, "internship");
  const items = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Internships (audit)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <div className="text-xs text-muted-foreground">Loading…</div>
        ) : items.length === 0 ? (
          <div className="text-xs text-muted-foreground">
            No internships yet.
          </div>
        ) : (
          items.map((it) => {
            const d = (it.details ?? {}) as Record<string, unknown>;
            const aiSummary = (d.ai_summary as string | undefined) ?? "";
            const aiBullets = (d.ai_bullets as string[] | undefined) ?? [];
            const responsibilities = (d.responsibilities as string | undefined) ?? "";
            const achievements = (d.achievements as string | undefined) ?? "";
            const tools = (d.tools as string[] | undefined) ?? [];
            const skills = (d.skills_gained as string[] | undefined) ?? [];
            const field = (d.field as string | undefined) ?? null;
            const workMode = (d.work_mode as string | undefined) ?? null;
            const dates = _formatEntryRange(it.start_date, it.end_date, it.is_current);
            return (
              <div key={it.id} className="rounded-lg border bg-background p-3 text-sm">
                <div className="font-medium">
                  {it.title}
                  {it.organization ? (
                    <span className="text-muted-foreground"> @ {it.organization}</span>
                  ) : null}
                </div>
                <div className="text-xs text-muted-foreground">
                  {[dates, field, workMode].filter(Boolean).join(" · ")}
                </div>
                <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      Raw input
                    </div>
                    {responsibilities && (
                      <div className="mt-1 whitespace-pre-wrap rounded bg-muted/30 p-2 text-xs">
                        <span className="font-medium">Responsibilities:</span>{" "}
                        {responsibilities}
                      </div>
                    )}
                    {achievements && (
                      <div className="mt-1 whitespace-pre-wrap rounded bg-muted/30 p-2 text-xs">
                        <span className="font-medium">Achievements:</span>{" "}
                        {achievements}
                      </div>
                    )}
                    {tools.length > 0 && (
                      <div className="mt-1 text-xs">
                        <span className="font-medium">Tools:</span> {tools.join(", ")}
                      </div>
                    )}
                    {skills.length > 0 && (
                      <div className="mt-1 text-xs">
                        <span className="font-medium">Skills:</span>{" "}
                        {skills.join(", ")}
                      </div>
                    )}
                  </div>
                  <div>
                    <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      AI output
                    </div>
                    {aiSummary ? (
                      <div className="mt-1 rounded bg-primary/5 p-2 text-xs italic">
                        {aiSummary}
                      </div>
                    ) : (
                      <div className="mt-1 text-xs text-muted-foreground">
                        No AI summary saved.
                      </div>
                    )}
                    {aiBullets.length > 0 ? (
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">
                        {aiBullets.map((b, i) => (
                          <li key={i}>{b}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="mt-1 text-xs text-muted-foreground">
                        No AI bullets saved.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}

function _formatEntryRange(
  start: string | null,
  end: string | null,
  isCurrent: boolean,
): string {
  const e = isCurrent ? "Present" : end ?? "";
  const s = start ?? "";
  if (s && e) return `${s} – ${e}`;
  return s || e;
}
