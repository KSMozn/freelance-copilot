import {
  Bell,
  CalendarClock,
  CheckCircle2,
  Inbox,
  MessageSquare,
  Plus,
  Send,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import {
  useAddInteraction,
  useAddInterview,
  useAddReminder,
  useApplicationActivity,
  useCompleteReminder,
  useDeleteInteraction,
  useDeleteInterview,
  useDeleteReminder,
  useUpdateInterview,
  type FollowUpReminder,
  type InteractionChannel,
  type InterviewEvent,
  type InterviewFormat,
  type InterviewOutcome,
  type RecruiterInteraction,
} from "@/features/professional/applications/trackerApi";

function nowIso() {
  return new Date().toISOString().slice(0, 16);
}

function toToast(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? "Failed";
}

const CHANNEL_LABEL: Record<InteractionChannel, string> = {
  email: "Email",
  linkedin: "LinkedIn",
  phone: "Phone",
  in_person: "In-person",
  other: "Other",
};

const INTERVIEW_FORMAT_LABEL: Record<InterviewFormat, string> = {
  phone_screen: "Phone screen",
  technical: "Technical",
  system_design: "System design",
  behavioral: "Behavioral",
  onsite: "On-site",
  final: "Final",
  other: "Other",
};

const INTERVIEW_OUTCOMES: InterviewOutcome[] = ["pending", "pass", "fail", "cancelled"];

interface Props {
  applicationId: string;
}

export function ApplicationActivityCard({ applicationId }: Props) {
  const { data, isLoading } = useApplicationActivity(applicationId);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Activity tracker</CardTitle>
        <CardDescription>
          Recruiter touchpoints, interview rounds, and follow-ups for this application.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        <RemindersSection applicationId={applicationId} reminders={data?.reminders ?? []} />
        <InterviewsSection applicationId={applicationId} interviews={data?.interviews ?? []} />
        <InteractionsSection
          applicationId={applicationId}
          interactions={data?.interactions ?? []}
        />
      </CardContent>
    </Card>
  );
}

// ---- Reminders -----------------------------------------------------------

function RemindersSection({
  applicationId,
  reminders,
}: {
  applicationId: string;
  reminders: FollowUpReminder[];
}) {
  const [open, setOpen] = useState(false);
  const [due, setDue] = useState(nowIso());
  const [note, setNote] = useState("");
  const add = useAddReminder(applicationId);
  const complete = useCompleteReminder(applicationId);
  const remove = useDeleteReminder(applicationId);

  function submit() {
    if (!note.trim()) return;
    add.mutate(
      { due_at: new Date(due).toISOString(), note: note.trim() },
      {
        onSuccess: () => {
          toast.success("Reminder added");
          setNote("");
          setOpen(false);
        },
        onError: (err) => toast.error(toToast(err)),
      },
    );
  }

  const now = Date.now();

  return (
    <Section
      icon={<Bell className="h-4 w-4 text-primary" />}
      title="Follow-up reminders"
      subtitle={
        reminders.filter((r) => !r.completed_at).length === 0
          ? "No open reminders."
          : `${reminders.filter((r) => !r.completed_at).length} open`
      }
      onAdd={() => setOpen((s) => !s)}
    >
      {open && (
        <Form>
          <div className="grid gap-2 md:grid-cols-2">
            <div>
              <Label htmlFor="due">Due</Label>
              <Input
                id="due"
                type="datetime-local"
                value={due}
                onChange={(e) => setDue(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="note">Note</Label>
              <Input
                id="note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Reply with availability"
              />
            </div>
          </div>
          <Button size="sm" onClick={submit} disabled={add.isPending || !note.trim()}>
            Add reminder
          </Button>
        </Form>
      )}

      {reminders.map((r) => {
        const due = new Date(r.due_at);
        const overdue = !r.completed_at && due.getTime() < now;
        return (
          <Row key={r.id}>
            <div className="min-w-0 flex-1 space-y-0.5">
              <p
                className={`text-sm ${r.completed_at ? "text-muted-foreground line-through" : ""}`}
              >
                {r.note}
              </p>
              <p className="flex items-center gap-2 text-xs text-muted-foreground">
                <CalendarClock className="h-3 w-3" />
                {due.toLocaleString()}
                {overdue && (
                  <Badge variant="outline" className="text-[10px] text-destructive">
                    overdue
                  </Badge>
                )}
                {r.completed_at && (
                  <Badge variant="outline" className="text-[10px]">
                    done
                  </Badge>
                )}
              </p>
            </div>
            <div className="flex gap-1">
              {!r.completed_at && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => complete.mutate(r.id)}
                  title="Mark complete"
                >
                  <CheckCircle2 className="h-3 w-3" />
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive"
                onClick={() => {
                  if (!confirm("Delete this reminder?")) return;
                  remove.mutate(r.id);
                }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </Row>
        );
      })}
    </Section>
  );
}

// ---- Interviews ----------------------------------------------------------

function InterviewsSection({
  applicationId,
  interviews,
}: {
  applicationId: string;
  interviews: InterviewEvent[];
}) {
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState("");
  const [format, setFormat] = useState<InterviewFormat>("phone_screen");
  const [scheduled, setScheduled] = useState(nowIso());
  const [duration, setDuration] = useState<number>(30);
  const add = useAddInterview(applicationId);
  const update = useUpdateInterview(applicationId);
  const remove = useDeleteInterview(applicationId);

  function submit() {
    if (!label.trim()) return;
    add.mutate(
      {
        round_label: label.trim(),
        format,
        scheduled_at: new Date(scheduled).toISOString(),
        duration_minutes: duration,
      },
      {
        onSuccess: () => {
          toast.success("Interview added");
          setLabel("");
          setOpen(false);
        },
        onError: (err) => toast.error(toToast(err)),
      },
    );
  }

  return (
    <Section
      icon={<CalendarClock className="h-4 w-4 text-primary" />}
      title="Interviews"
      subtitle={
        interviews.length === 0
          ? "No interviews scheduled."
          : `${interviews.length} round${interviews.length === 1 ? "" : "s"}`
      }
      onAdd={() => setOpen((s) => !s)}
    >
      {open && (
        <Form>
          <div className="grid gap-2 md:grid-cols-2">
            <div>
              <Label htmlFor="label">Round label</Label>
              <Input
                id="label"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="Hiring manager screen"
              />
            </div>
            <div>
              <Label htmlFor="format">Format</Label>
              <select
                id="format"
                value={format}
                onChange={(e) => setFormat(e.target.value as InterviewFormat)}
                className="h-9 w-full rounded-md border bg-background px-2 text-sm"
              >
                {Object.entries(INTERVIEW_FORMAT_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="scheduled">Scheduled</Label>
              <Input
                id="scheduled"
                type="datetime-local"
                value={scheduled}
                onChange={(e) => setScheduled(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="duration">Duration (min)</Label>
              <Input
                id="duration"
                type="number"
                min={5}
                max={600}
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value || "30", 10))}
              />
            </div>
          </div>
          <Button size="sm" onClick={submit} disabled={add.isPending || !label.trim()}>
            Add interview
          </Button>
        </Form>
      )}

      {interviews.map((ev) => (
        <Row key={ev.id}>
          <div className="min-w-0 flex-1 space-y-0.5">
            <p className="flex items-center gap-2 text-sm font-medium">
              {ev.round_label}
              <Badge variant="outline" className="text-[10px]">
                {INTERVIEW_FORMAT_LABEL[ev.format]}
              </Badge>
              <OutcomeBadge outcome={ev.outcome} />
            </p>
            <p className="text-xs text-muted-foreground">
              {ev.scheduled_at ? new Date(ev.scheduled_at).toLocaleString() : "no scheduled time"}
              {ev.duration_minutes && ` · ${ev.duration_minutes} min`}
              {ev.interviewer_names && ` · ${ev.interviewer_names}`}
            </p>
          </div>
          <div className="flex items-center gap-1">
            <select
              value={ev.outcome}
              onChange={(e) =>
                update.mutate({
                  id: ev.id,
                  patch: { outcome: e.target.value as InterviewOutcome },
                })
              }
              className="h-7 rounded-md border bg-background px-1 text-xs"
            >
              {INTERVIEW_OUTCOMES.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
            <Button
              size="sm"
              variant="ghost"
              className="text-destructive"
              onClick={() => {
                if (!confirm(`Delete "${ev.round_label}"?`)) return;
                remove.mutate(ev.id);
              }}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </Row>
      ))}
    </Section>
  );
}

function OutcomeBadge({ outcome }: { outcome: InterviewOutcome }) {
  const cfg = {
    pending: "bg-muted text-muted-foreground",
    pass: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
    fail: "bg-destructive/10 text-destructive",
    cancelled: "bg-muted text-muted-foreground line-through",
  }[outcome];
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${cfg}`}>
      {outcome}
    </span>
  );
}

// ---- Recruiter interactions ---------------------------------------------

function InteractionsSection({
  applicationId,
  interactions,
}: {
  applicationId: string;
  interactions: RecruiterInteraction[];
}) {
  const [open, setOpen] = useState(false);
  const [channel, setChannel] = useState<InteractionChannel>("email");
  const [direction, setDirection] = useState<"inbound" | "outbound">("inbound");
  const [occurred, setOccurred] = useState(nowIso());
  const [contact, setContact] = useState("");
  const [summary, setSummary] = useState("");
  const add = useAddInteraction(applicationId);
  const remove = useDeleteInteraction(applicationId);

  function submit() {
    if (!summary.trim()) return;
    add.mutate(
      {
        channel,
        direction,
        occurred_at: new Date(occurred).toISOString(),
        contact_name: contact.trim() || null,
        summary: summary.trim(),
      },
      {
        onSuccess: () => {
          toast.success("Interaction logged");
          setSummary("");
          setContact("");
          setOpen(false);
        },
        onError: (err) => toast.error(toToast(err)),
      },
    );
  }

  return (
    <Section
      icon={<MessageSquare className="h-4 w-4 text-primary" />}
      title="Recruiter interactions"
      subtitle={
        interactions.length === 0
          ? "No interactions logged."
          : `${interactions.length} touchpoint${interactions.length === 1 ? "" : "s"}`
      }
      onAdd={() => setOpen((s) => !s)}
    >
      {open && (
        <Form>
          <div className="grid gap-2 md:grid-cols-2">
            <div>
              <Label htmlFor="channel">Channel</Label>
              <select
                id="channel"
                value={channel}
                onChange={(e) => setChannel(e.target.value as InteractionChannel)}
                className="h-9 w-full rounded-md border bg-background px-2 text-sm"
              >
                {Object.entries(CHANNEL_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="direction">Direction</Label>
              <select
                id="direction"
                value={direction}
                onChange={(e) => setDirection(e.target.value as "inbound" | "outbound")}
                className="h-9 w-full rounded-md border bg-background px-2 text-sm"
              >
                <option value="inbound">Inbound (they wrote me)</option>
                <option value="outbound">Outbound (I wrote them)</option>
              </select>
            </div>
            <div>
              <Label htmlFor="occurred">When</Label>
              <Input
                id="occurred"
                type="datetime-local"
                value={occurred}
                onChange={(e) => setOccurred(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="contact">Contact name</Label>
              <Input
                id="contact"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                placeholder="Jane Recruiter"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="summary">Summary</Label>
              <Textarea
                id="summary"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={3}
                placeholder="What was said?"
              />
            </div>
          </div>
          <Button size="sm" onClick={submit} disabled={add.isPending || !summary.trim()}>
            Log interaction
          </Button>
        </Form>
      )}

      {interactions.map((i) => (
        <Row key={i.id}>
          <div className="min-w-0 flex-1 space-y-0.5">
            <p className="flex items-center gap-2 text-sm">
              {i.direction === "inbound" ? (
                <Inbox className="h-3 w-3 text-muted-foreground" />
              ) : (
                <Send className="h-3 w-3 text-muted-foreground" />
              )}
              <span className="font-medium">{i.contact_name ?? "Recruiter"}</span>
              <Badge variant="outline" className="text-[10px]">
                {CHANNEL_LABEL[i.channel]}
              </Badge>
            </p>
            {i.summary && <p className="text-sm">{i.summary}</p>}
            <p className="text-xs text-muted-foreground">
              {new Date(i.occurred_at).toLocaleString()}
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="text-destructive"
            onClick={() => {
              if (!confirm("Delete this interaction?")) return;
              remove.mutate(i.id);
            }}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </Row>
      ))}
    </Section>
  );
}

// ---- Layout primitives --------------------------------------------------

function Section({
  icon,
  title,
  subtitle,
  onAdd,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  onAdd: () => void;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="text-sm font-semibold">{title}</h3>
        </div>
        <Button size="sm" variant="outline" onClick={onAdd}>
          <Plus className="mr-1 h-3 w-3" />
          Add
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">{subtitle}</p>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

function Row({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border bg-muted/30 px-3 py-2">
      {children}
    </div>
  );
}

function Form({ children }: { children: React.ReactNode }) {
  return <div className="space-y-3 rounded-md border bg-muted/30 p-3">{children}</div>;
}
