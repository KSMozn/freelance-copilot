import { useEffect, useState } from "react";
import { toast } from "sonner";

import { useImproveInternship } from "@/features/student-wizard/coaching/coachingApi";
import {
  useCreateStudentEntry,
  useUpdateStudentEntry,
} from "@/features/student-wizard/studentApi";
import {
  INTERNSHIP_ACTION_CHIPS,
  INTERNSHIP_FIELD_OPTIONS,
  INTERNSHIP_FIELD_TASK_PRESETS,
  INTERNSHIP_WORK_MODES,
  SKILLS,
  TECH_STACK,
} from "@/features/student-wizard/studentSuggestions";
import type {
  InternshipDetails,
  InternshipField,
  InternshipWorkMode,
  StudentEntry,
  StudentEntryKind,
} from "@/features/student-wizard/studentTypes";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Combobox } from "@/shared/ui/combobox";
import { Input } from "@/shared/ui/input";
import { Select } from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";

import { Field } from "./wizardShared";

export function InternshipCard({
  entry,
  onDone,
}: {
  entry?: StudentEntry;
  onDone: () => void;
}) {
  const create = useCreateStudentEntry();
  const update = useUpdateStudentEntry();
  const improve = useImproveInternship();

  const initialDetails = (entry?.details ?? {}) as InternshipDetails;

  const [organization, setOrganization] = useState(entry?.organization ?? "");
  const [title, setTitle] = useState(entry?.title ?? "");
  const [field, setField] = useState<InternshipField | "">(
    (initialDetails.field as InternshipField | undefined) ?? "",
  );
  // Track which field-preset chips the student has already picked so
  // we can hide them and backfill from the rest of the pool. Reset on
  // field change (new pool → nothing consumed yet).
  const [usedPresetIdxs, setUsedPresetIdxs] = useState<Set<number>>(
    () => new Set(),
  );
  useEffect(() => {
    setUsedPresetIdxs(new Set());
  }, [field]);
  const [location, setLocation] = useState(initialDetails.location ?? "");
  const [workMode, setWorkMode] = useState<InternshipWorkMode | "">(
    initialDetails.work_mode ?? "",
  );
  const [department, setDepartment] = useState(initialDetails.department ?? "");
  const [startDate, setStartDate] = useState(entry?.start_date ?? "");
  const [endDate, setEndDate] = useState(entry?.end_date ?? "");
  const [isCurrent, setIsCurrent] = useState(entry?.is_current ?? false);
  const [responsibilities, setResponsibilities] = useState(
    initialDetails.responsibilities ?? "",
  );
  const [achievements, setAchievements] = useState(
    initialDetails.achievements ?? "",
  );
  const [tools, setTools] = useState<string[]>(initialDetails.tools ?? []);
  const [toolInput, setToolInput] = useState("");
  const [skillsGained, setSkillsGained] = useState<string[]>(
    initialDetails.skills_gained ?? [],
  );
  const [skillInput, setSkillInput] = useState("");
  const [url, setUrl] = useState(entry?.url ?? "");

  const [aiSummary, setAiSummary] = useState(initialDetails.ai_summary ?? "");
  const [aiBullets, setAiBullets] = useState<string[]>(
    initialDetails.ai_bullets ?? [],
  );
  const [followUps, setFollowUps] = useState<string[]>([]);
  const [followUpAnswers, setFollowUpAnswers] = useState<string[]>([]);

  const canImprove =
    !!organization.trim() &&
    !!title.trim() &&
    (responsibilities.trim().length > 0 ||
      achievements.trim().length > 0 ||
      tools.length > 0 ||
      skillsGained.length > 0);

  const dateError =
    startDate && endDate && startDate > endDate
      ? "Start date can't be after end date."
      : null;

  function appendChip(verb: string) {
    setResponsibilities((prev) =>
      prev.trim().length === 0 ? `${verb} ` : `${prev.replace(/\n?$/, "\n")}${verb} `,
    );
  }

  function addPresetTask(task: string, poolIdx: number) {
    setResponsibilities((prev) =>
      prev.trim().length === 0
        ? task
        : `${prev.replace(/\n?$/, "\n")}${task}`,
    );
    setUsedPresetIdxs((prev) => {
      const next = new Set(prev);
      next.add(poolIdx);
      return next;
    });
  }

  function addToolChip(v: string) {
    const t = v.trim();
    if (!t || tools.includes(t)) return;
    setTools([...tools, t]);
    setToolInput("");
  }
  function removeTool(t: string) {
    setTools(tools.filter((x) => x !== t));
  }
  function addSkillChip(v: string) {
    const t = v.trim();
    if (!t || skillsGained.includes(t)) return;
    setSkillsGained([...skillsGained, t]);
    setSkillInput("");
  }
  function removeSkill(t: string) {
    setSkillsGained(skillsGained.filter((x) => x !== t));
  }

  async function runImprove() {
    if (!canImprove) return;
    try {
      const res = await improve.mutateAsync({
        organization: organization.trim(),
        title: title.trim(),
        field: (field || null) as InternshipField | null,
        location: location.trim() || null,
        work_mode: (workMode || null) as InternshipWorkMode | null,
        department: department.trim() || null,
        responsibilities: responsibilities.trim() || null,
        achievements: achievements.trim() || null,
        tools,
        skills_gained: skillsGained,
        follow_up_answers: followUpAnswers.filter((a) => a.trim()),
      });
      if (!res.ok) {
        toast.error("AI is unavailable — try again in a moment.");
        return;
      }
      if (res.vague) {
        setFollowUps(res.follow_ups);
        setFollowUpAnswers(res.follow_ups.map(() => ""));
        setAiSummary("");
        setAiBullets([]);
        toast.info("Add a bit more detail so we can draft strong bullets.");
        return;
      }
      setFollowUps([]);
      setFollowUpAnswers([]);
      setAiSummary(res.summary ?? "");
      setAiBullets(res.bullets);
      // Fold suggested tools/skills that student didn't already add.
      if (res.tools_suggested.length) {
        setTools((prev) =>
          Array.from(
            new Set([...prev, ...res.tools_suggested.map((t) => t.trim())]),
          ),
        );
      }
      if (res.skills_suggested.length) {
        setSkillsGained((prev) =>
          Array.from(
            new Set([
              ...prev,
              ...res.skills_suggested.map((s) => s.trim()),
            ]),
          ),
        );
      }
      toast.success("Draft ready — edit any line to make it yours.");
    } catch {
      toast.error("Couldn't reach the coach. Try again in a moment.");
    }
  }

  async function save() {
    if (!organization.trim() || !title.trim()) {
      toast.error("Company name and role are required.");
      return;
    }
    if (dateError) {
      toast.error(dateError);
      return;
    }
    const details: InternshipDetails = {
      field: (field || null) as InternshipField | null,
      location: location.trim() || null,
      work_mode: (workMode || null) as InternshipWorkMode | null,
      department: department.trim() || null,
      responsibilities: responsibilities.trim() || null,
      achievements: achievements.trim() || null,
      tools,
      skills_gained: skillsGained,
      ai_summary: aiSummary.trim() || null,
      ai_bullets: aiBullets.filter((b) => b.trim()),
    };
    const payload = {
      kind: "internship" as StudentEntryKind,
      title: title.trim(),
      organization: organization.trim() || null,
      start_date: startDate || null,
      end_date: isCurrent ? null : endDate || null,
      is_current: isCurrent,
      description: null,
      url: url.trim() || null,
      details: details as unknown as Record<string, unknown>,
    };
    try {
      if (entry) {
        await update.mutateAsync({ id: entry.id, payload });
      } else {
        await create.mutateAsync(payload);
      }
      toast.success(entry ? "Internship updated." : "Internship added.");
      onDone();
    } catch {
      toast.error("Couldn't save internship.");
    }
  }

  const busy = create.isPending || update.isPending;
  const presetPool = field ? INTERNSHIP_FIELD_TASK_PRESETS[field] ?? [] : [];
  // Show up to 6 unused preset chips at a time. As the student picks
  // one it disappears and the next unused pool entry fills its slot.
  const visiblePresets = presetPool
    .map((task, i) => ({ task, i }))
    .filter(({ i }) => !usedPresetIdxs.has(i))
    .slice(0, 6);

  return (
    <Card className="rounded-2xl border-border/70">
      <CardHeader className="space-y-1 pb-2">
        <CardTitle className="text-base">
          {entry ? "Edit internship" : "New internship"}
        </CardTitle>
        <CardDescription className="text-xs">
          Answer in plain language — Careero can polish it into
          professional bullet points for you.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Basics */}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="Company / Organization *">
            <Input
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
              placeholder="TechNova Solutions"
            />
          </Field>
          <Field label="Role / Title *">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Software Development Intern"
            />
          </Field>
          <Field label="Location">
            <Input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Cairo, Egypt"
            />
          </Field>
          <Field label="Work mode">
            <Select
              value={workMode}
              onChange={(e) =>
                setWorkMode(e.target.value as InternshipWorkMode | "")
              }
              options={[
                { value: "", label: "—" },
                ...INTERNSHIP_WORK_MODES.map((m) => ({
                  value: m.value,
                  label: m.label,
                })),
              ]}
            />
          </Field>
          <Field label="Department / Team">
            <Input
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="Engineering"
            />
          </Field>
          <Field label="Field of internship">
            <Select
              value={field}
              onChange={(e) => setField(e.target.value as InternshipField | "")}
              options={[
                { value: "", label: "—" },
                ...INTERNSHIP_FIELD_OPTIONS.map((o) => ({
                  value: o.value,
                  label: o.label,
                })),
              ]}
            />
          </Field>
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
          </Field>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isCurrent}
            onChange={(e) => setIsCurrent(e.target.checked)}
          />
          Currently ongoing
        </label>
        {dateError && (
          <div className="text-xs text-destructive">{dateError}</div>
        )}

        {/* Preset tasks */}
        {presetPool.length > 0 && (
          <div className="rounded-md bg-muted/30 p-3">
            <div className="mb-2 text-xs text-muted-foreground">
              Common tasks for this field — click to add.
            </div>
            {visiblePresets.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {visiblePresets.map(({ task, i }) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => addPresetTask(task, i)}
                    className="rounded-full border border-primary/30 bg-primary/5 px-2.5 py-1 text-xs text-primary hover:bg-primary/10"
                  >
                    {task}
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                All suggestions added — you're set.
              </div>
            )}
          </div>
        )}

        {/* Responsibilities */}
        <Field label="Main responsibilities">
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">
              What kind of tasks did you work on? Did you use any tools?
            </div>
            <Textarea
              value={responsibilities}
              onChange={(e) => setResponsibilities(e.target.value)}
              placeholder="I helped test the website, joined stand-ups, fixed small bugs…"
              rows={4}
            />
            <div className="flex flex-wrap gap-1.5">
              {INTERNSHIP_ACTION_CHIPS.map((verb) => (
                <button
                  key={verb}
                  type="button"
                  onClick={() => appendChip(verb)}
                  className="rounded-full border border-border bg-background px-2.5 py-1 text-xs hover:bg-muted"
                >
                  {verb}
                </button>
              ))}
            </div>
          </div>
        </Field>

        {/* Achievements */}
        <Field label="Key achievements">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">
              Did you improve, build, analyze, test, support, document,
              or present anything?
            </div>
            <Textarea
              value={achievements}
              onChange={(e) => setAchievements(e.target.value)}
              placeholder="Automated a reporting process that saved ~2h/week…"
              rows={3}
            />
          </div>
        </Field>

        {/* Tools */}
        <Field label="Tools / Technologies">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1.5">
              {tools.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => removeTool(t)}
                  className="rounded-full bg-primary/10 px-2.5 py-1 text-xs text-primary hover:bg-primary/20"
                  title="Remove"
                >
                  {t} ×
                </button>
              ))}
            </div>
            <Combobox
              value={toolInput}
              onChange={setToolInput}
              onBlurCommit={(v) => addToolChip(v)}
              options={TECH_STACK}
              placeholder="Type a tool and press Enter…"
            />
          </div>
        </Field>

        {/* Skills */}
        <Field label="Skills gained">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1.5">
              {skillsGained.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => removeSkill(t)}
                  className="rounded-full bg-primary/10 px-2.5 py-1 text-xs text-primary hover:bg-primary/20"
                  title="Remove"
                >
                  {t} ×
                </button>
              ))}
            </div>
            <Combobox
              value={skillInput}
              onChange={setSkillInput}
              onBlurCommit={(v) => addSkillChip(v)}
              options={SKILLS}
              placeholder="Type a skill and press Enter…"
            />
          </div>
        </Field>

        {/* Certificate URL */}
        <Field label="Certificate / proof link (optional)">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://…"
          />
        </Field>

        {/* Improve with AI */}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="brand"
            disabled={!canImprove || improve.isPending}
            onClick={() => void runImprove()}
          >
            {improve.isPending ? "Drafting…" : "Improve with AI"}
          </Button>
          <div className="text-xs text-muted-foreground">
            Careero rewrites your input into 2–4 professional bullet
            points. Never invents facts.
          </div>
        </div>

        {/* Follow-up questions (vague path) */}
        {followUps.length > 0 && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 p-3">
            <div className="text-sm font-medium text-amber-900">
              Add a bit more so we can draft strong bullets
            </div>
            <div className="mt-2 space-y-2">
              {followUps.map((q, i) => (
                <div key={i}>
                  <div className="text-xs text-amber-900">{q}</div>
                  <Input
                    value={followUpAnswers[i] ?? ""}
                    onChange={(e) => {
                      const next = [...followUpAnswers];
                      next[i] = e.target.value;
                      setFollowUpAnswers(next);
                    }}
                    className="mt-1"
                  />
                </div>
              ))}
              <Button
                type="button"
                size="sm"
                onClick={() => void runImprove()}
                disabled={improve.isPending}
              >
                Try again
              </Button>
            </div>
          </div>
        )}

        {/* AI output */}
        {aiBullets.length > 0 && (
          <div className="rounded-lg border border-primary/40 bg-primary/5 p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">AI draft — edit any line</div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void runImprove()}
                disabled={improve.isPending}
              >
                Re-generate
              </Button>
            </div>
            <div className="mt-2 space-y-2">
              <Field label="Summary">
                <Textarea
                  value={aiSummary}
                  onChange={(e) => setAiSummary(e.target.value)}
                  rows={2}
                />
              </Field>
              <div className="text-xs text-muted-foreground">Bullets</div>
              {aiBullets.map((b, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="mt-2 text-muted-foreground">•</span>
                  <Textarea
                    value={b}
                    rows={2}
                    onChange={(e) => {
                      const next = [...aiBullets];
                      next[i] = e.target.value;
                      setAiBullets(next);
                    }}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      setAiBullets(aiBullets.filter((_, j) => j !== i))
                    }
                  >
                    Remove
                  </Button>
                </div>
              ))}
              {aiBullets.length < 6 && (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setAiBullets([...aiBullets, ""])}
                >
                  + Add bullet
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Save / cancel */}
        <div className="flex gap-2 pt-2">
          <Button type="button" onClick={() => void save()} disabled={busy}>
            {busy ? "Saving…" : entry ? "Save changes" : "Save internship"}
          </Button>
          <Button type="button" variant="ghost" onClick={onDone}>
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
