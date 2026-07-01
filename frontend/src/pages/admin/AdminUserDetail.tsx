import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useAdminDeleteUser,
  useAdminDisableUser,
  useAdminEnableUser,
  useAdminImpersonate,
  useAdminResetWizard,
  useAdminUser,
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
      navigate("/admin/users");
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
          to="/admin/users"
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
            disabled={reset.isPending || user.persona_kind !== "student"}
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
                v={`${user.student.completed_steps.length}/11 · current: ${user.student.current_step ?? "none"}`}
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
