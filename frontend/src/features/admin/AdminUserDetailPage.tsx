import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { AlertTriangle, Loader2, Mail } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select } from "@/shared/ui/select";
import { LlmSpendCardBody } from "@/features/admin/LlmSpendCard";
import {
  downloadAdminUserCvDocx,
  downloadAdminUserCvPdf,
  useAdminDeleteUser,
  useAdminDisableUser,
  useAdminEditStudentProfile,
  useAdminEmailPreview,
  useAdminEmailTemplates,
  useAdminEnableUser,
  useAdminImpersonate,
  useAdminResetWizard,
  useAdminSendEmail,
  useAdminUser,
  useAdminUserCvPreview,
  useAdminUserEntries,
  useAdminUserLlmSpend,
} from "@/features/admin/adminApi";
import { parseInternshipAuditDetails } from "@/features/admin/adminTypes";
import type { AdminStudentSummary, AdminUserDetail } from "@/features/admin/adminTypes";

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
      // Prefer the app.* origin when we're on a real admin subdomain
      // (careero.app or the legacy personaarmory.com). On a single-origin
      // dev setup we stay on the same host — the ?surface=app query param
      // clears the sticky admin flag so the app bundle takes over and
      // /impersonate can decode the fragment.
      const host = window.location.hostname;
      const isAdminSubdomain = host.startsWith("admin.");
      const appOrigin = isAdminSubdomain
        ? window.location.origin.replace(/(^https?:\/\/)admin\./, "$1app.")
        : window.location.origin;
      window.location.href = `${appOrigin}/impersonate?surface=app#p=${encoded}`;
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
        <Link to="/users" className="text-xs text-muted-foreground hover:text-foreground">
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
                const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data
                  ?.detail;
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

      {id && user.student && (
        <CvPreviewCard userId={id} userFullName={user.full_name ?? user.email} />
      )}

      {id && <SendEmailCard userId={id} userEmail={user.email} />}

      {id && <UserLlmSpendCard userId={id} />}

      {id && user.student && <InternshipAuditPanel userId={id} />}

      {confirmingDelete && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-base text-destructive">Delete {user.email}?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">
              This deletes the user and all cascading data (profile, entries, uploaded files). This
              cannot be undone. Type the user's email to confirm.
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
                  del.isPending || deleteEmail.trim().toLowerCase() !== user.email.toLowerCase()
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

        {user.student && id && (
          <StudentProfileCard userId={id} user={user} student={user.student} />
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

// ---- Student profile card (view + edit) --------------------------------

function StudentProfileCard({
  userId,
  user,
  student,
}: {
  userId: string;
  user: AdminUserDetail;
  student: AdminStudentSummary;
}) {
  const [editing, setEditing] = useState(false);

  if (!editing) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">Student profile</CardTitle>
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
            Edit
          </Button>
        </CardHeader>
        <CardContent className="text-sm">
          <Row k="Name" v={student.full_name ?? "—"} />
          <Row k="CV email" v={student.professional_email ?? "—"} />
          <Row k="Phone" v={student.phone ?? "—"} />
          <Row k="Location" v={student.location ?? "—"} />
          <Row k="Date of birth" v={student.date_of_birth ?? "—"} />
          <Row k="CV template" v={student.cv_template_slug ?? "—"} />
          <Row k="University" v={student.college ?? "—"} />
          <Row k="Department" v={student.department ?? "—"} />
          <Row k="Degree" v={student.degree ?? "—"} />
          <Row k="Major" v={student.major ?? "—"} />
          <Row k="Grad. year" v={student.graduation_year?.toString() ?? "—"} />
          <Row k="GPA" v={student.gpa ?? "—"} />
          <Row
            k="Wizard"
            v={`${student.completed_steps.length}/13 · current: ${student.current_step ?? "none"}`}
          />
          <Row k="Entries" v={student.entries_count.toString()} />
          {student.headline && <Row k="Headline" v={student.headline} />}
          {student.summary && (
            <div className="mt-2">
              <div className="text-xs text-muted-foreground">Summary</div>
              <div className="mt-1 whitespace-pre-wrap rounded bg-muted/30 p-2 text-xs">
                {student.summary}
              </div>
            </div>
          )}
          {Object.keys(student.entries_by_kind).length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-muted-foreground">Entries by kind</div>
              <div className="mt-1 flex flex-wrap gap-1">
                {Object.entries(student.entries_by_kind).map(([k, c]) => (
                  <span key={k} className="rounded bg-muted px-1.5 py-0.5 text-[10px]">
                    {k}: {c}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <StudentProfileEditForm
      userId={userId}
      user={user}
      student={student}
      onDone={() => setEditing(false)}
    />
  );
}

function StudentProfileEditForm({
  userId,
  student,
  onDone,
}: {
  userId: string;
  user: AdminUserDetail;
  student: AdminStudentSummary;
  onDone: () => void;
}) {
  const mutation = useAdminEditStudentProfile(userId);
  const [fullName, setFullName] = useState(student.full_name ?? "");
  const [email, setEmail] = useState(student.professional_email ?? "");
  const [phone, setPhone] = useState(student.phone ?? "");
  const [location, setLocation] = useState(student.location ?? "");
  const [dob, setDob] = useState(student.date_of_birth ?? "");
  const [college, setCollege] = useState(student.college ?? "");
  const [department, setDepartment] = useState(student.department ?? "");
  const [degree, setDegree] = useState(student.degree ?? "");
  const [major, setMajor] = useState(student.major ?? "");
  const [year, setYear] = useState(student.graduation_year ? String(student.graduation_year) : "");

  async function save() {
    try {
      await mutation.mutateAsync({
        full_name: emptyToNull(fullName),
        professional_email: emptyToNull(email),
        phone: emptyToNull(phone),
        location: emptyToNull(location),
        date_of_birth: emptyToNull(dob),
        college: emptyToNull(college),
        department: emptyToNull(department),
        degree: emptyToNull(degree),
        major: emptyToNull(major),
        graduation_year: year ? Number(year) : null,
      });
      toast.success("Profile updated");
      onDone();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
        ?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail
                .map((d: { msg?: string; loc?: unknown[] }) =>
                  d.msg ? `${(d.loc ?? []).slice(-1)[0]}: ${d.msg}` : "invalid",
                )
                .join("; ")
            : "Could not save";
      toast.error(msg);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Student profile (editing)</CardTitle>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onDone} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button size="sm" onClick={() => void save()} disabled={mutation.isPending}>
            {mutation.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <EditField label="Name" value={fullName} onChange={setFullName} />
        <EditField label="CV email" value={email} onChange={setEmail} type="email" />
        <EditField label="Phone" value={phone} onChange={setPhone} />
        <EditField label="Location" value={location} onChange={setLocation} />
        <EditField
          label="Date of birth"
          value={dob}
          onChange={setDob}
          type="date"
          placeholder="YYYY-MM-DD"
        />
        <EditField label="University" value={college} onChange={setCollege} />
        <EditField label="Department" value={department} onChange={setDepartment} />
        <EditField label="Degree" value={degree} onChange={setDegree} />
        <EditField label="Major" value={major} onChange={setMajor} />
        <EditField
          label="Grad. year"
          value={year}
          onChange={(v) => setYear(v.replace(/[^0-9]/g, "").slice(0, 4))}
          placeholder="2027"
        />
        <div className="pt-1 text-[11px] text-muted-foreground">
          Only fields on this card are editable here. Photo, template choice, summary, headline, and
          links stay under the student's control.
        </div>
      </CardContent>
    </Card>
  );
}

function EditField({
  label,
  value,
  onChange,
  type,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div className="grid grid-cols-[110px_1fr] items-center gap-2">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Input
        value={value}
        type={type}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 text-sm"
      />
    </div>
  );
}

function emptyToNull(v: string): string | null {
  const t = v.trim();
  return t.length === 0 ? null : t;
}

// ---- Send email card + preview modal -----------------------------------

function SendEmailCard({ userId, userEmail }: { userId: string; userEmail: string }) {
  const { data: templates } = useAdminEmailTemplates();
  const [templateId, setTemplateId] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);

  const options = (templates ?? []).map((t) => ({ value: t.id, label: t.name })) ?? [];
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
          <Label className="text-xs" htmlFor="tpl">
            Template
          </Label>
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
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
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
                    <span className="font-medium">{preview.recipient_name}</span>
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
          <Button variant="brand" size="sm" onClick={submit} disabled={send.isPending || !preview}>
            {send.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Send email
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---- Per-user LLM spend card ------------------------------------------

function UserLlmSpendCard({ userId }: { userId: string }) {
  const { data, isLoading, isError } = useAdminUserLlmSpend(userId, 30);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">LLM spend (last 30 days)</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-xs text-muted-foreground">Loading…</div>
        ) : isError || !data ? (
          <div className="text-xs text-destructive">Could not load spend.</div>
        ) : (
          <LlmSpendCardBody
            summary={data}
            userId={userId}
            emptyMessage="This user has no coach or career-pack LLM calls in the last 30 days."
          />
        )}
      </CardContent>
    </Card>
  );
}

// ---- CV preview card ---------------------------------------------------
//
// Renders the user's CV HTML inline so we can eyeball it without
// impersonating (which would mutate their last_login_at + fire an
// impersonation audit event). Also exposes PDF + DOCX download —
// same renderers as the student, one audit event per action.

function CvPreviewCard({ userId, userFullName }: { userId: string; userFullName: string }) {
  const [loaded, setLoaded] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [docxBusy, setDocxBusy] = useState(false);
  const { data, isLoading, error, refetch } = useAdminUserCvPreview(loaded ? userId : undefined);

  async function download(format: "pdf" | "docx") {
    const setBusy = format === "pdf" ? setPdfBusy : setDocxBusy;
    setBusy(true);
    try {
      const blob =
        format === "pdf"
          ? await downloadAdminUserCvPdf(userId)
          : await downloadAdminUserCvDocx(userId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName = userFullName.replace(/\s+/g, "_");
      a.download = format === "pdf" ? `${safeName}.pdf` : `${safeName}_CV.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      toast.error(`Could not download ${format.toUpperCase()}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">CV preview</CardTitle>
        <div className="flex gap-2">
          {loaded && (
            <Button variant="ghost" size="sm" onClick={() => void refetch()} disabled={isLoading}>
              Reload
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => void download("pdf")}
            disabled={pdfBusy}
          >
            {pdfBusy ? "…" : "Download PDF"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void download("docx")}
            disabled={docxBusy}
          >
            {docxBusy ? "…" : "Download DOCX"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!loaded ? (
          <div className="flex items-center justify-between rounded-md border bg-muted/20 p-3">
            <div className="text-xs text-muted-foreground">
              Preview renders the CV as it would render for the student — no impersonation, no
              session side effects.
            </div>
            <Button size="sm" onClick={() => setLoaded(true)}>
              Load preview
            </Button>
          </div>
        ) : isLoading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading…</div>
        ) : error ? (
          <div className="p-4 text-sm text-destructive">Could not load preview.</div>
        ) : data ? (
          <div className="overflow-hidden rounded-md border bg-white">
            <iframe
              title="Admin CV preview"
              srcDoc={data.html}
              className="h-[900px] w-full"
              sandbox="allow-same-origin"
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
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
          <div className="text-xs text-muted-foreground">No internships yet.</div>
        ) : (
          items.map((it) => {
            const d = parseInternshipAuditDetails(it.details);
            const aiSummary = d.ai_summary;
            const aiBullets = d.ai_bullets;
            const responsibilities = d.responsibilities;
            const achievements = d.achievements;
            const tools = d.tools;
            const skills = d.skills_gained;
            const field = d.field;
            const workMode = d.work_mode;
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
                        <span className="font-medium">Responsibilities:</span> {responsibilities}
                      </div>
                    )}
                    {achievements && (
                      <div className="mt-1 whitespace-pre-wrap rounded bg-muted/30 p-2 text-xs">
                        <span className="font-medium">Achievements:</span> {achievements}
                      </div>
                    )}
                    {tools.length > 0 && (
                      <div className="mt-1 text-xs">
                        <span className="font-medium">Tools:</span> {tools.join(", ")}
                      </div>
                    )}
                    {skills.length > 0 && (
                      <div className="mt-1 text-xs">
                        <span className="font-medium">Skills:</span> {skills.join(", ")}
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
                      <div className="mt-1 text-xs text-muted-foreground">No AI summary saved.</div>
                    )}
                    {aiBullets.length > 0 ? (
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">
                        {aiBullets.map((b, i) => (
                          <li key={i}>{b}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="mt-1 text-xs text-muted-foreground">No AI bullets saved.</div>
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

function _formatEntryRange(start: string | null, end: string | null, isCurrent: boolean): string {
  const e = isCurrent ? "Present" : (end ?? "");
  const s = start ?? "";
  if (s && e) return `${s} – ${e}`;
  return s || e;
}
