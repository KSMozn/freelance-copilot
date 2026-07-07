import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { AlertTriangle, Loader2, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  useAdminEmailTemplates,
  useAdminSendEmailBulk,
  useAdminUsers,
} from "@/lib/admin";
import { cn } from "@/lib/utils";
import type {
  BulkRecipient,
  SendEmailBulkDryRunResponse,
  SendEmailBulkResponse,
} from "@/types/admin";

const STUCK_AT_LABELS: Record<string, string> = {
  registered: "Registered but no wizard progress",
  basics: "Stuck at Basics",
  education: "Stuck at Education",
  photo: "Stuck at Photo",
  skills: "Stuck at Skills",
  courses: "Stuck at Courses",
  projects: "Stuck at Projects",
  internships: "Stuck at Internships",
  volunteer: "Stuck at Volunteer",
  languages: "Stuck at Languages",
  certificates: "Stuck at Certificates",
  summary: "Stuck at Summary",
  preview: "Stuck at Preview",
  "starter-pack": "Reached Starter Pack",
};

function parseBool(v: string | null): boolean | undefined {
  if (v === "true") return true;
  if (v === "false") return false;
  return undefined;
}

export function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const size = 25;
  const [params, setParams] = useSearchParams();
  const stuckAt = params.get("stuck_at");
  const persona = params.get("persona") ?? "";
  const active = parseBool(params.get("active"));
  const emailVerified = parseBool(params.get("email_verified"));
  const hasCv = parseBool(params.get("has_cv"));
  const college = params.get("college") ?? "";
  const signedUpAfter = params.get("signed_up_after") ?? "";
  const signedUpBefore = params.get("signed_up_before") ?? "";
  const stuckAtLabel = stuckAt ? STUCK_AT_LABELS[stuckAt] ?? stuckAt : null;

  function updateFilter(key: string, value: string | null) {
    const next = new URLSearchParams(params);
    if (value === null || value === "") next.delete(key);
    else next.set(key, value);
    setParams(next, { replace: true });
    setPage(1);
  }

  function clearAllFilters() {
    setParams(new URLSearchParams(), { replace: true });
    setPage(1);
  }

  const hasAnyFilter =
    !!stuckAt ||
    !!persona ||
    active !== undefined ||
    emailVerified !== undefined ||
    hasCv !== undefined ||
    !!college ||
    !!signedUpAfter ||
    !!signedUpBefore;

  const { data, isLoading } = useAdminUsers({
    search,
    page,
    size,
    stuckAt: stuckAt ?? undefined,
    persona: persona || undefined,
    active,
    emailVerified,
    hasCv,
    college: college || undefined,
    signedUpAfter: signedUpAfter
      ? new Date(signedUpAfter).toISOString()
      : undefined,
    signedUpBefore: signedUpBefore
      ? new Date(signedUpBefore).toISOString()
      : undefined,
  });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkOpen, setBulkOpen] = useState(false);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / size)) : 1;

  const pageIds = useMemo(() => (data?.items ?? []).map((u) => u.id), [data]);
  const allSelectedOnPage =
    pageIds.length > 0 && pageIds.every((id) => selected.has(id));
  const someSelectedOnPage = pageIds.some((id) => selected.has(id));

  function toggleOne(id: string, checked: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleAllOnPage(checked: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      for (const id of pageIds) {
        if (checked) next.add(id);
        else next.delete(id);
      }
      return next;
    });
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Users</h1>
        <p className="text-sm text-muted-foreground">
          {data ? `${data.total.toLocaleString()} total` : "—"}
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="Search by email or name…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="max-w-sm"
          />
          <div className="w-36">
            <Select
              value={persona}
              onChange={(e) => updateFilter("persona", e.target.value)}
              options={[
                { value: "", label: "All personas" },
                { value: "student", label: "Student" },
                { value: "professional", label: "Professional" },
              ]}
            />
          </div>
          <div className="w-32">
            <Select
              value={active === undefined ? "" : String(active)}
              onChange={(e) => updateFilter("active", e.target.value)}
              options={[
                { value: "", label: "Any status" },
                { value: "true", label: "Active" },
                { value: "false", label: "Disabled" },
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              value={
                emailVerified === undefined ? "" : String(emailVerified)
              }
              onChange={(e) => updateFilter("email_verified", e.target.value)}
              options={[
                { value: "", label: "Any verification" },
                { value: "true", label: "Verified" },
                { value: "false", label: "Unverified" },
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              value={hasCv === undefined ? "" : String(hasCv)}
              onChange={(e) => updateFilter("has_cv", e.target.value)}
              options={[
                { value: "", label: "CV download?" },
                { value: "true", label: "Downloaded CV" },
                { value: "false", label: "No CV yet" },
              ]}
            />
          </div>
          <Input
            placeholder="University…"
            value={college}
            onChange={(e) => updateFilter("college", e.target.value)}
            className="max-w-[200px]"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span>Signed up between</span>
          <Input
            type="date"
            value={signedUpAfter}
            onChange={(e) => updateFilter("signed_up_after", e.target.value)}
            className="h-8 max-w-[160px] text-xs"
          />
          <span>and</span>
          <Input
            type="date"
            value={signedUpBefore}
            onChange={(e) => updateFilter("signed_up_before", e.target.value)}
            className="h-8 max-w-[160px] text-xs"
          />
          {hasAnyFilter && (
            <button
              type="button"
              onClick={clearAllFilters}
              className="ml-auto text-xs text-primary hover:underline"
            >
              Clear all filters
            </button>
          )}
        </div>
        {stuckAtLabel && (
          <div className="flex flex-wrap gap-1">
            <div className="flex items-center gap-1 rounded-full border bg-primary/10 px-3 py-1 text-xs text-primary">
              <span className="font-medium">{stuckAtLabel}</span>
              <button
                type="button"
                onClick={() => updateFilter("stuck_at", null)}
                className="ml-1 rounded-full px-1 text-primary/70 hover:bg-primary/20 hover:text-primary"
                aria-label="Clear funnel filter"
              >
                ×
              </button>
            </div>
          </div>
        )}
        {selected.size > 0 && (
          <div className="ml-auto flex items-center gap-2 rounded-md border bg-muted/40 px-3 py-1.5 text-sm">
            <span className="font-medium">{selected.size}</span> selected
            <Button
              size="sm"
              variant="brand"
              onClick={() => setBulkOpen(true)}
            >
              <Mail className="h-4 w-4" />
              Send email…
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelected(new Set())}
            >
              Clear
            </Button>
          </div>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading…</div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">No users found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/30 text-xs uppercase text-muted-foreground">
                    <Th>
                      <input
                        type="checkbox"
                        checked={allSelectedOnPage}
                        ref={(el) => {
                          if (el)
                            el.indeterminate =
                              !allSelectedOnPage && someSelectedOnPage;
                        }}
                        onChange={(e) => toggleAllOnPage(e.target.checked)}
                        aria-label="Select all on this page"
                      />
                    </Th>
                    <Th>Email</Th>
                    <Th>Name</Th>
                    <Th>Persona</Th>
                    <Th>Status</Th>
                    <Th>Wizard</Th>
                    <Th>LinkedIn</Th>
                    <Th>GitHub</Th>
                    <Th>Downloaded CV</Th>
                    <Th>Last login</Th>
                    <Th>Joined</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((u) => (
                    <tr key={u.id} className="border-b hover:bg-muted/30">
                      <Td>
                        <input
                          type="checkbox"
                          checked={selected.has(u.id)}
                          onChange={(e) => toggleOne(u.id, e.target.checked)}
                          aria-label={`Select ${u.email}`}
                        />
                      </Td>
                      <Td>
                        <Link
                          to={`/users/${u.id}`}
                          className="text-primary hover:underline"
                        >
                          {u.email}
                        </Link>
                        {u.is_superuser && (
                          <span className="ml-1 rounded bg-primary/10 px-1 text-[10px] font-semibold uppercase text-primary">
                            Super
                          </span>
                        )}
                      </Td>
                      <Td>{u.full_name ?? "—"}</Td>
                      <Td className="capitalize">{u.persona_kind}</Td>
                      <Td>
                        <StatusBadge active={u.is_active} verified={u.email_verified} />
                      </Td>
                      <Td>
                        {u.wizard_step || u.wizard_completed > 0 ? (
                          <span className="text-xs text-muted-foreground">
                            {u.wizard_completed}/13
                            {u.wizard_step ? ` · ${u.wizard_step}` : ""}
                          </span>
                        ) : (
                          "—"
                        )}
                      </Td>
                      <Td><PresenceBadge value={u.has_linkedin} /></Td>
                      <Td><PresenceBadge value={u.has_github} /></Td>
                      <Td><PresenceBadge value={u.has_downloaded_cv} /></Td>
                      <Td className="whitespace-nowrap">
                        {u.last_login_at ? fmtRelative(u.last_login_at) : "—"}
                      </Td>
                      <Td className="whitespace-nowrap">{fmtDate(u.created_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {data && data.total > size && (
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {bulkOpen && (
        <BulkEmailModal
          userIds={Array.from(selected)}
          onClose={() => setBulkOpen(false)}
          onSent={() => setSelected(new Set())}
        />
      )}
    </div>
  );
}

function BulkEmailModal({
  userIds,
  onClose,
  onSent,
}: {
  userIds: string[];
  onClose: () => void;
  onSent: () => void;
}) {
  const { data: templates } = useAdminEmailTemplates();
  const bulk = useAdminSendEmailBulk();
  const [templateId, setTemplateId] = useState("");
  const [recipients, setRecipients] = useState<BulkRecipient[] | null>(null);
  const [result, setResult] = useState<SendEmailBulkResponse | null>(null);

  const options = (templates ?? []).map((t) => ({ value: t.id, label: t.name }));
  const chosen = (templates ?? []).find((t) => t.id === templateId) ?? null;

  async function prepare() {
    if (!templateId || userIds.length === 0) return;
    try {
      const res = (await bulk.mutateAsync({
        userIds,
        templateId,
        dryRun: true,
      })) as SendEmailBulkDryRunResponse;
      setRecipients(res.recipients);
    } catch {
      toast.error("Couldn't prepare recipient list.");
    }
  }

  async function submit() {
    if (!templateId || userIds.length === 0) return;
    try {
      const res = (await bulk.mutateAsync({
        userIds,
        templateId,
        dryRun: false,
      })) as SendEmailBulkResponse;
      setResult(res);
      if (res.sent > 0) {
        toast.success(`Sent ${res.sent} email${res.sent === 1 ? "" : "s"}.`);
      } else {
        toast.error(
          `0 sent. ${res.skipped} skipped, ${res.failed.length} failed.`,
        );
      }
      onSent();
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(msg ?? "Bulk send failed.");
    }
  }

  const recentCount = recipients?.filter((r) => r.has_recent_send).length ?? 0;

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
          <div className="text-sm font-semibold">
            Send email to {userIds.length}{" "}
            {userIds.length === 1 ? "user" : "users"}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        <div className="flex-1 space-y-4 overflow-auto p-4">
          {result ? (
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">{result.sent}</span> sent,{" "}
                <span className="font-medium">{result.skipped}</span> skipped,{" "}
                <span className="font-medium">{result.failed.length}</span> failed.
              </div>
              {result.failed.length > 0 && (
                <div className="rounded border border-destructive/40 bg-destructive/5 p-3 text-xs">
                  <div className="mb-1 font-medium">Failures</div>
                  <ul className="list-disc space-y-0.5 pl-4">
                    {result.failed.map((f) => (
                      <li key={f.user_id}>
                        {f.user_id}: {f.error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <Label className="text-xs" htmlFor="bulk-tpl">
                  Template
                </Label>
                <Select
                  id="bulk-tpl"
                  value={templateId}
                  onChange={(e) => {
                    setTemplateId(e.target.value);
                    setRecipients(null);
                  }}
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

              {!recipients && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={prepare}
                  disabled={!templateId || bulk.isPending}
                >
                  {bulk.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Prepare recipient list
                </Button>
              )}

              {recipients && (
                <div className="space-y-2">
                  <div className="rounded-md border border-primary/40 bg-primary/10 p-3 text-xs">
                    <span className="font-semibold">Preview only —</span>{" "}
                    nothing has been sent yet. Review the list below, then
                    click <span className="font-semibold">Send to {recipients.length}</span>{" "}
                    at the bottom to deliver.
                  </div>
                  {recentCount > 0 && (
                    <div className="flex gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs">
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                      <div>
                        <span className="font-medium">{recentCount}</span> of
                        these users received this template in the last 7 days.
                        Sending again is allowed — just double-check first.
                      </div>
                    </div>
                  )}
                  <div className="max-h-64 overflow-auto rounded border">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 border-b bg-muted/40">
                        <tr>
                          <th className="px-2 py-1.5 text-left font-medium">Email</th>
                          <th className="px-2 py-1.5 text-left font-medium">Name</th>
                          <th className="px-2 py-1.5 text-left font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recipients.map((r) => (
                          <tr key={r.user_id} className="border-b last:border-b-0">
                            <td className="px-2 py-1.5">{r.email}</td>
                            <td className="px-2 py-1.5">{r.full_name ?? "—"}</td>
                            <td className="px-2 py-1.5">
                              {r.has_recent_send ? (
                                <span className="inline-flex items-center gap-1 text-amber-600">
                                  <AlertTriangle className="h-3 w-3" />
                                  Recent send
                                </span>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
        <div className="flex items-center justify-end gap-2 border-t px-4 py-3">
          {result ? (
            <Button variant="brand" size="sm" onClick={onClose}>
              Done
            </Button>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="brand"
                size="sm"
                onClick={submit}
                disabled={!recipients || bulk.isPending}
              >
                {bulk.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Send to {recipients?.length ?? 0}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-2 text-left font-medium">{children}</th>;
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-3 py-2", className)}>{children}</td>;
}

function PresenceBadge({ value }: { value: boolean | null }) {
  if (value === null) return <span className="text-xs text-muted-foreground">—</span>;
  if (value)
    return (
      <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-primary">
        Yes
      </span>
    );
  return (
    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold uppercase text-muted-foreground">
      No
    </span>
  );
}

function StatusBadge({ active, verified }: { active: boolean; verified: boolean }) {
  if (!active)
    return (
      <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-destructive">
        Disabled
      </span>
    );
  return (
    <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-primary">
      {verified ? "Active" : "Unverified"}
    </span>
  );
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString();
}

function fmtRelative(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString();
}
