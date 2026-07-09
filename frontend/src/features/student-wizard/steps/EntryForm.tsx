import { useState } from "react";
import { toast } from "sonner";

import { useCoachText } from "@/features/student-wizard/coaching/coachingApi";
import {
  useCreateStudentEntry,
  useUpdateStudentEntry,
} from "@/features/student-wizard/studentApi";
import {
  CERTIFICATE_ISSUERS,
  CERTIFICATES,
  COURSES,
  LANGUAGE_PROFICIENCIES,
  LANGUAGES,
  SKILL_PROFICIENCIES,
  SKILLS,
  TECH_STACK,
} from "@/features/student-wizard/studentSuggestions";
import type { StudentEntry, StudentEntryKind } from "@/features/student-wizard/studentTypes";
import { Button } from "@/shared/ui/button";
import { Combobox } from "@/shared/ui/combobox";
import { Input } from "@/shared/ui/input";
import { Select } from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";

import { Field } from "./wizardShared";

// Per-kind entry form — small, focused, and uses the right control per
// field. Handles both "add new" (no `entry` prop) and "edit existing"
// (pre-populates from `entry`, calls PUT instead of POST).
export function EntryForm({
  kind,
  entry,
  onCancel,
}: {
  kind: StudentEntryKind;
  entry?: StudentEntry;
  onCancel?: () => void;
}) {
  const create = useCreateStudentEntry();
  const update = useUpdateStudentEntry();
  const coach = useCoachText();
  const editing = Boolean(entry);
  const initialTechStack = Array.isArray(entry?.details?.tech_stack)
    ? (entry!.details.tech_stack as unknown[]).map(String)
    : [];
  const initialProficiency =
    typeof entry?.details?.proficiency === "string"
      ? (entry!.details.proficiency as string)
      : "";
  const initialRoles = Array.isArray(entry?.details?.roles)
    ? (entry!.details.roles as unknown[]).map(String)
    : [];
  const initialFeatures =
    typeof entry?.details?.features === "string"
      ? (entry!.details.features as string)
      : "";
  const initialHardest =
    typeof entry?.details?.hardest_part === "string"
      ? (entry!.details.hardest_part as string)
      : "";

  const [title, setTitle] = useState(entry?.title ?? "");
  const [description, setDescription] = useState(entry?.description ?? "");
  const [url, setUrl] = useState(entry?.url ?? "");
  const [organization, setOrganization] = useState(entry?.organization ?? "");
  const [startDate, setStartDate] = useState(entry?.start_date ?? "");
  const [endDate, setEndDate] = useState(entry?.end_date ?? "");
  const [isCurrent, setIsCurrent] = useState(entry?.is_current ?? false);
  const [proficiency, setProficiency] = useState(initialProficiency);
  const [techStack, setTechStack] = useState<string[]>(initialTechStack);
  const [techInput, setTechInput] = useState("");
  const [roles, setRoles] = useState<string[]>(initialRoles);
  const [features, setFeatures] = useState(initialFeatures);
  const [hardestPart, setHardestPart] = useState(initialHardest);
  // Auto-open the "Make it stronger" section in edit mode when the
  // student already filled at least one enhance field, so the values
  // are visible instead of hidden behind a collapsed toggle.
  const [showEnhance, setShowEnhance] = useState(
    Boolean(initialFeatures || initialHardest || (editing && entry?.url)),
  );
  const [coachSuggestion, setCoachSuggestion] = useState<string | null>(null);

  function reset() {
    setTitle("");
    setDescription("");
    setUrl("");
    setOrganization("");
    setStartDate("");
    setEndDate("");
    setIsCurrent(false);
    setProficiency("");
    setTechStack([]);
    setTechInput("");
    setRoles([]);
    setFeatures("");
    setHardestPart("");
    setShowEnhance(false);
    setCoachSuggestion(null);
  }

  function toggleRole(role: string) {
    setRoles((prev) => {
      if (prev.includes(role)) return prev.filter((r) => r !== role);
      // "solo" and "team" are mutually exclusive intent — toggling one
      // clears the other so the narrative doesn't produce nonsense
      // like "solo as part of a team".
      if (role === "solo") return [...prev.filter((r) => r !== "team"), "solo"];
      if (role === "team") return [...prev.filter((r) => r !== "solo"), "team"];
      return [...prev, role];
    });
  }

  function addTech(t: string) {
    const cleaned = t.trim();
    if (!cleaned) return;
    if (techStack.includes(cleaned)) return;
    setTechStack([...techStack, cleaned]);
    setTechInput("");
  }

  async function submit() {
    if (!title.trim()) {
      toast.error("Give this entry a title first.");
      return;
    }
    const details: Record<string, unknown> = {};
    if (kind === "skill" && proficiency) details.proficiency = proficiency;
    if (kind === "language" && proficiency) details.proficiency = proficiency;
    if (kind === "project") {
      if (techStack.length > 0) details.tech_stack = techStack;
      if (roles.length > 0) details.roles = roles;
      if (features.trim()) details.features = features.trim();
      if (hardestPart.trim()) details.hardest_part = hardestPart.trim();
    }

    const payload = {
      kind,
      title,
      organization: kind === "volunteer" || kind === "certificate" ? organization || null : null,
      description:
        kind === "project" || kind === "volunteer" ? description || null : null,
      url:
        kind === "project" || kind === "certificate" ? url || null : null,
      details,
      is_current: kind === "volunteer" ? isCurrent : false,
      start_date: kind === "volunteer" ? startDate || null : null,
      end_date: kind === "volunteer" && !isCurrent ? endDate || null : null,
    };

    if (editing && entry) {
      await update.mutateAsync({ id: entry.id, payload });
      onCancel?.();
    } else {
      await create.mutateAsync(payload);
      reset();
    }
  }

  async function tightenWithCoach() {
    if (!description.trim()) {
      toast.error("Write a draft description first.");
      return;
    }
    const field =
      kind === "project" ? "project_description"
      : kind === "volunteer" ? "volunteer_description"
      : "summary";
    const res = await coach.mutateAsync({
      field,
      text: description,
      context: { kind, title, organization },
    });
    if (res.ok) setCoachSuggestion(res.rewritten);
    else toast.error("Coach unavailable.");
  }

  const singular = SINGULAR[kind];

  // Per-kind form bodies. Each is small enough to read inline.
  let body: JSX.Element;
  if (kind === "skill") {
    body = (
      <>
        <Field label="Skill">
          <Combobox value={title} onChange={setTitle} options={SKILLS} placeholder="Python" />
        </Field>
        <Field label="Proficiency">
          <Select
            value={proficiency}
            onChange={(e) => setProficiency(e.target.value)}
            placeholder="Pick a level…"
            options={[
              { value: "", label: "—" },
              ...SKILL_PROFICIENCIES.map((p) => ({ value: p.value, label: p.label })),
            ]}
          />
        </Field>
      </>
    );
  } else if (kind === "course") {
    body = (
      <Field label="Course">
        <Combobox
          value={title}
          onChange={setTitle}
          options={COURSES}
          placeholder="Data Structures and Algorithms"
        />
      </Field>
    );
  } else if (kind === "language") {
    body = (
      <>
        <Field label="Language">
          <Combobox value={title} onChange={setTitle} options={LANGUAGES} placeholder="English" />
        </Field>
        <Field label="Proficiency">
          <Select
            value={proficiency}
            onChange={(e) => setProficiency(e.target.value)}
            placeholder="Pick a level…"
            options={[
              { value: "", label: "—" },
              ...LANGUAGE_PROFICIENCIES.map((p) => ({ value: p, label: p })),
            ]}
          />
        </Field>
      </>
    );
  } else if (kind === "certificate") {
    body = (
      <>
        <Field label="Certificate name">
          <Combobox
            value={title}
            onChange={setTitle}
            options={CERTIFICATES}
            placeholder="AWS Cloud Practitioner"
          />
        </Field>
        <Field label="Issuer">
          <Combobox
            value={organization}
            onChange={setOrganization}
            options={CERTIFICATE_ISSUERS}
            placeholder="Amazon Web Services"
          />
        </Field>
        <Field label="URL (optional)">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://…"
          />
        </Field>
      </>
    );
  } else if (kind === "project") {
    body = (
      <>
        <Field label="Project name">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Jobs Web Application"
          />
        </Field>
        <Field label="What does the project do?">
          <Textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Browse job listings and apply online"
          />
          <p className="mt-1 text-xs text-muted-foreground">
            Explain it simply in one sentence. Who uses it and what can they do?
          </p>
        </Field>
        <Field label="Technologies used">
          <div className="space-y-2">
            <Combobox
              value={techInput}
              onChange={setTechInput}
              onBlurCommit={(v) => addTech(v)}
              options={TECH_STACK}
              placeholder="Search a technology and press Enter…"
            />
            {techStack.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {techStack.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTechStack(techStack.filter((x) => x !== t))}
                    className="rounded-full border bg-background px-2 py-0.5 text-xs hover:bg-muted"
                    title="Click to remove"
                  >
                    {t} ×
                  </button>
                ))}
              </div>
            )}
          </div>
        </Field>
        <Field label="What did you work on?">
          <div className="grid grid-cols-2 gap-2">
            {PROJECT_ROLES.map((r) => (
              <label
                key={r.value}
                className="flex items-center gap-2 rounded-md border bg-background px-2 py-1.5 text-sm hover:bg-muted/40"
              >
                <input
                  type="checkbox"
                  checked={roles.includes(r.value)}
                  onChange={() => toggleRole(r.value)}
                />
                <span>{r.label}</span>
              </label>
            ))}
          </div>
        </Field>
        <div>
          <button
            type="button"
            className="text-sm text-primary hover:underline"
            onClick={() => setShowEnhance((v) => !v)}
          >
            {showEnhance ? "Hide extra details" : "Make it stronger (optional)"}
          </button>
        </div>
        {showEnhance && (
          <div className="space-y-3 rounded-md border border-dashed p-3">
            <Field label="What features did you build? (optional)">
              <Textarea
                rows={2}
                value={features}
                onChange={(e) => setFeatures(e.target.value)}
                placeholder="add tasks, mark them done, group by course"
              />
            </Field>
            <Field label="What was the hardest part? (optional)">
              <Input
                value={hardestPart}
                onChange={(e) => setHardestPart(e.target.value)}
                placeholder="wiring up the drag-and-drop reordering"
              />
            </Field>
            <Field label="GitHub or demo link (optional)">
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/you/project"
              />
            </Field>
          </div>
        )}
      </>
    );
  } else if (kind === "volunteer") {
    body = (
      <>
        <Field label="Role">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Mentor"
          />
        </Field>
        <Field label="Organization">
          <Input
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            placeholder="Local nonprofit"
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Start date">
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </Field>
          <Field label="End date">
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              disabled={isCurrent}
            />
            <label className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={isCurrent}
                onChange={(e) => {
                  setIsCurrent(e.target.checked);
                  if (e.target.checked) setEndDate("");
                }}
              />
              Still ongoing
            </label>
          </Field>
        </div>
        <Field label="Description">
          <Textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What did you do? Who did it help?"
          />
          <div className="mt-2 flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void tightenWithCoach()}
              disabled={coach.isPending}
            >
              {coach.isPending ? "Thinking…" : "Tighten with coach"}
            </Button>
          </div>
          {coachSuggestion && (
            <div className="mt-2 rounded-md border bg-muted/30 p-3 text-sm">
              <div className="mb-2 text-xs font-medium text-muted-foreground">Coach's rewrite</div>
              <p className="whitespace-pre-wrap">{coachSuggestion}</p>
              <div className="mt-2 flex gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    setDescription(coachSuggestion);
                    setCoachSuggestion(null);
                  }}
                >
                  Use this
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setCoachSuggestion(null)}>
                  Discard
                </Button>
              </div>
            </div>
          )}
        </Field>
      </>
    );
  } else {
    // award / extracurricular fall back to a minimal form.
    body = (
      <>
        <Field label="Title">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={`${singular} name`} />
        </Field>
        <Field label="Description (optional)">
          <Textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
      </>
    );
  }

  const busy = editing ? update.isPending : create.isPending;
  const primaryLabel = editing
    ? busy
      ? "Saving…"
      : "Save changes"
    : busy
      ? "Adding…"
      : `Add ${singular}`;

  return (
    <div className="rounded-md border p-4">
      <div className="mb-3 text-sm font-medium">
        {editing ? `Edit ${singular}` : `Add ${singular}`}
      </div>
      <div className="space-y-3">
        {body}
        <div className="flex gap-2">
          <Button onClick={() => void submit()} disabled={busy}>
            {primaryLabel}
          </Button>
          {editing ? (
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
          ) : (
            <Button variant="ghost" onClick={reset}>
              Clear
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

const SINGULAR: Record<StudentEntryKind, string> = {
  skill: "skill",
  course: "course",
  project: "project",
  internship: "internship",
  volunteer: "volunteer experience",
  language: "language",
  certificate: "certificate",
  award: "award",
  extracurricular: "activity",
};

// Project-role checkboxes shown under "What did you work on?". Values
// are the keys the backend narrative composer reads
// (`_project_role_phrase` in student_cv_renderer.py); labels are what
// the student sees. "solo" / "team" are treated as mutually-exclusive
// intent inside `toggleRole`.
const PROJECT_ROLES: { value: string; label: string }[] = [
  { value: "frontend", label: "Frontend" },
  { value: "backend", label: "Backend" },
  { value: "database", label: "Database" },
  { value: "ui_design", label: "UI/design" },
  { value: "testing", label: "Testing/debugging" },
  { value: "solo", label: "I built it alone" },
  { value: "team", label: "I worked in a team" },
];
