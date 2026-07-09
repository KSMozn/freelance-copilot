import { ArrowLeft, Briefcase, ExternalLink, Loader2, Save, Trash2 } from "lucide-react";

import { ApplicationActivityCard } from "@/features/professional/applications/ApplicationActivityCard";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import {
  useApplication,
  useApplicationHistory,
  useDeleteApplication,
  useUpdateApplicationDetails,
  useUpdateApplicationStatus,
} from "@/features/professional/applications/applicationsApi";
import { cn } from "@/shared/lib/utils";
import {
  APPLICATION_STATUS_TRANSITIONS,
  type Application,
  type ApplicationStatus,
} from "@/features/professional/apiTypes";

const STATUS_LABEL: Record<ApplicationStatus, string> = {
  draft: "Draft",
  applied: "Applied",
  viewed: "Viewed",
  interview: "Interview",
  offer: "Offer",
  won: "Won",
  completed: "Completed",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

const TIMESTAMP_FIELDS: { key: keyof Application; label: ApplicationStatus }[] = [
  { key: "applied_at", label: "applied" },
  { key: "viewed_at", label: "viewed" },
  { key: "interview_at", label: "interview" },
  { key: "offer_at", label: "offer" },
  { key: "won_at", label: "won" },
  { key: "completed_at", label: "completed" },
  { key: "rejected_at", label: "rejected" },
  { key: "withdrawn_at", label: "withdrawn" },
];

function fmt(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: app, isLoading } = useApplication(id);
  const { data: history } = useApplicationHistory(id);
  const updateStatus = useUpdateApplicationStatus(id);
  const updateDetails = useUpdateApplicationDetails(id);
  const del = useDeleteApplication();

  const [contractAmount, setContractAmount] = useState("");
  const [clientResponse, setClientResponse] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [notes, setNotes] = useState("");
  const [statusNote, setStatusNote] = useState("");

  useEffect(() => {
    if (!app) return;
    setContractAmount(app.contract_amount ?? "");
    setClientResponse(app.client_response ?? "");
    setRejectionReason(app.rejection_reason ?? "");
    setNotes(app.notes ?? "");
  }, [app]);

  if (isLoading) return <div className="text-sm text-muted-foreground">Loading…</div>;
  if (!app) return <div className="text-sm text-muted-foreground">Application not found.</div>;

  const allowedNext = APPLICATION_STATUS_TRANSITIONS[app.status] ?? [];

  const handleTransition = (to: ApplicationStatus) => {
    updateStatus.mutate(
      { to_status: to, note: statusNote || undefined },
      {
        onSuccess: () => {
          toast.success(`Status → ${STATUS_LABEL[to]}`);
          setStatusNote("");
        },
        onError: (err: unknown) => {
          const detail =
            (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data
              ?.detail ?? "Could not update status";
          toast.error(detail);
        },
      },
    );
  };

  const handleSaveDetails = () => {
    updateDetails.mutate(
      {
        contract_amount: contractAmount || null,
        client_response: clientResponse || null,
        rejection_reason: rejectionReason || null,
        notes: notes || null,
      },
      {
        onSuccess: () => toast.success("Details saved"),
        onError: () => toast.error("Could not save"),
      },
    );
  };

  const snapshot = app.snapshot;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <Link
            to="/applications"
            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="mr-1 h-3.5 w-3.5" /> Applications
          </Link>
          <h1 className="mt-1 truncate text-2xl font-semibold tracking-tight">
            {snapshot?.job?.title ?? "Application"}
          </h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="secondary">{STATUS_LABEL[app.status]}</Badge>
            {app.contract_amount && <span>contract ${app.contract_amount}</span>}
            <Link
              to={`/jobs/${app.job_id}`}
              className="inline-flex items-center text-primary hover:underline"
            >
              <Briefcase className="mr-1 h-3 w-3" /> open job
              <ExternalLink className="ml-1 h-3 w-3" />
            </Link>
          </div>
        </div>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => {
            if (!confirm("Delete this application?")) return;
            del.mutate(app.id, {
              onSuccess: () => {
                toast.success("Deleted");
                navigate("/applications");
              },
              onError: () => toast.error("Could not delete"),
            });
          }}
        >
          <Trash2 className="mr-1 h-3.5 w-3.5" />
          Delete
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
            {TIMESTAMP_FIELDS.map(({ key, label }) => (
              <div key={key}>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {STATUS_LABEL[label]}
                </div>
                <div className="text-xs">{fmt(app[key] as string | null)}</div>
              </div>
            ))}
          </div>
          {allowedNext.length > 0 ? (
            <div className="space-y-2">
              <Label htmlFor="status-note">Transition note (optional)</Label>
              <Input
                id="status-note"
                value={statusNote}
                onChange={(e) => setStatusNote(e.target.value)}
                placeholder="e.g. Client opened the proposal."
              />
              <div className="flex flex-wrap gap-2">
                {allowedNext.map((to) => (
                  <Button
                    key={to}
                    size="sm"
                    variant="outline"
                    disabled={updateStatus.isPending}
                    onClick={() => handleTransition(to)}
                  >
                    → {STATUS_LABEL[to]}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">
              {STATUS_LABEL[app.status]} is a terminal status.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="contract-amount">Contract amount</Label>
              <Input
                id="contract-amount"
                inputMode="decimal"
                value={contractAmount}
                onChange={(e) => setContractAmount(e.target.value)}
                placeholder="e.g. 4500.00"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="client-response">Client response</Label>
              <Input
                id="client-response"
                value={clientResponse}
                onChange={(e) => setClientResponse(e.target.value)}
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <Label htmlFor="rejection-reason">Rejection reason</Label>
              <Input
                id="rejection-reason"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>
          <div className="mt-3 flex justify-end">
            <Button onClick={handleSaveDetails} disabled={updateDetails.isPending}>
              {updateDetails.isPending ? (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Save className="mr-2 h-3.5 w-3.5" />
              )}
              Save details
            </Button>
          </div>
        </CardContent>
      </Card>

      {snapshot && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Snapshot at submission</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Job</div>
              <div>{snapshot.job?.title}</div>
              {snapshot.job?.budget && (
                <div className="text-muted-foreground">Budget: {snapshot.job.budget}</div>
              )}
              {snapshot.job?.url && (
                <a
                  href={snapshot.job.url}
                  target="_blank"
                  rel="noreferrer"
                  className="break-all text-primary hover:underline"
                >
                  {snapshot.job.url}
                </a>
              )}
            </div>
            {snapshot.opportunity_score && (
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Opportunity score
                </div>
                <div>
                  {snapshot.opportunity_score.score}/100 ·{" "}
                  {snapshot.opportunity_score.recommendation}
                </div>
              </div>
            )}
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Proposal</div>
              {snapshot.proposal.title && (
                <div className="font-medium">{snapshot.proposal.title}</div>
              )}
              {snapshot.proposal.quality_score != null && (
                <div className="text-muted-foreground">
                  Quality: {snapshot.proposal.quality_score}/100
                </div>
              )}
              <pre className="mt-2 whitespace-pre-wrap break-words rounded-md bg-muted/40 p-3 font-sans text-sm leading-relaxed">
                {snapshot.proposal.body}
              </pre>
            </div>
            {snapshot.resume && (
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Resume</div>
                <div className="font-medium">{snapshot.resume.title}</div>
                {snapshot.resume.target_role && (
                  <div className="text-muted-foreground">
                    Target role: {snapshot.resume.target_role}
                  </div>
                )}
                {snapshot.resume.suggested_positioning.length > 0 && (
                  <ul className="mt-1 list-disc space-y-0.5 pl-5">
                    {snapshot.resume.suggested_positioning.map((p) => (
                      <li key={p}>{p}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            {snapshot.portfolio.length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Portfolio
                </div>
                <ul className="space-y-2">
                  {snapshot.portfolio.map((p) => (
                    <li key={p.id} className="rounded-md border border-border/70 p-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{p.title}</span>
                        {p.match_score != null && (
                          <Badge variant="outline">match {Math.round(p.match_score * 100)}%</Badge>
                        )}
                      </div>
                      {p.talking_points.length > 0 && (
                        <ul className="mt-1 list-disc space-y-0.5 pl-5 text-xs">
                          {p.talking_points.map((t) => (
                            <li key={t}>{t}</li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          {!history?.length ? (
            <div className="text-sm text-muted-foreground">No history yet.</div>
          ) : (
            <ol className="space-y-2">
              {history.map((h) => (
                <li
                  key={h.id}
                  className={cn("rounded-md border border-border/70 px-3 py-2 text-sm")}
                >
                  <div className="flex items-baseline justify-between">
                    <span>
                      <span className="text-muted-foreground">
                        {h.from_status ?? "(initial)"} →
                      </span>{" "}
                      <span className="font-medium">{h.to_status}</span>
                    </span>
                    <span className="text-xs text-muted-foreground">{fmt(h.created_at)}</span>
                  </div>
                  {h.note && <div className="mt-1 text-muted-foreground">{h.note}</div>}
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      <ApplicationActivityCard applicationId={app.id} />
    </div>
  );
}
