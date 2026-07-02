import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { fetchPhotoDataUri } from "@/lib/photoCache";
import { useLastProfileStore } from "@/stores/lastProfile";
import { AboutFooter } from "@/components/brand/AboutFooter";
import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { CoachWarnings } from "@/components/student/CoachWarnings";
import { DateOfBirthPicker } from "@/components/student/DateOfBirthPicker";
import { PhotoPositioner } from "@/components/student/PhotoPositioner";
import { PostDownloadSurvey } from "@/components/student/PostDownloadSurvey";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Combobox } from "@/components/ui/combobox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  downloadStudentCv,
  fetchCvPreviewHtml,
  useCoachEmail,
  useCoachPhoto,
  useCoachText,
  useCreateStudentEntry,
  useCvTemplates,
  useDeleteStudentEntry,
  useDraftSummary,
  useProofread,
  useStudentEntries,
  useStudentPhotoBlob,
  useStudentProfile,
  useUpdateStudentEntry,
  useUpdateStudentProfile,
  useUploadStudentPhoto,
} from "@/lib/student";
import {
  CERTIFICATE_ISSUERS,
  CERTIFICATES,
  COURSES,
  DEGREES,
  LANGUAGE_PROFICIENCIES,
  LANGUAGES,
  MAJORS,
  SKILL_PROFICIENCIES,
  SKILLS,
  TECH_STACK,
  UNIVERSITIES,
} from "@/lib/studentSuggestions";
import { useAutoSave } from "@/lib/useAutoSave";
import { useAuthStore } from "@/stores/auth";
import type {
  CoachSuggestion,
  CoachWarning,
  ProofreadFix,
  StudentEntry,
  StudentEntryKind,
  StudentLinks,
  StudentProfileUpdate,
} from "@/types/student";

interface StepDef {
  slug: string;
  title: string;
  blurb: string;
}

const STEPS: StepDef[] = [
  { slug: "basics", title: "About you", blurb: "Name, email, where you're based." },
  { slug: "education", title: "Where you study", blurb: "University, department, degree." },
  { slug: "photo", title: "Profile photo", blurb: "Optional — but a clean photo helps." },
  { slug: "skills", title: "Skills", blurb: "Things you can do. Pick from the list or type your own." },
  { slug: "courses", title: "Coursework", blurb: "Relevant courses you've taken." },
  { slug: "projects", title: "Projects", blurb: "What you've built." },
  { slug: "volunteer", title: "Volunteer work", blurb: "Where you've contributed." },
  { slug: "languages", title: "Languages", blurb: "Spoken / written languages." },
  { slug: "certificates", title: "Certificates", blurb: "Any certifications or courses." },
  {
    slug: "summary",
    title: "Summary",
    blurb: "We'll draft a headline + summary from what you've shared — edit freely.",
  },
  { slug: "preview", title: "Preview & download", blurb: "Your CV, ready to share." },
];

const KIND_FOR_STEP: Record<string, StudentEntryKind> = {
  skills: "skill",
  courses: "course",
  projects: "project",
  volunteer: "volunteer",
  languages: "language",
  certificates: "certificate",
};

export function StudentWizardPage() {
  const { data: profile, isLoading: profileLoading } = useStudentProfile();
  const updateProfile = useUpdateStudentProfile();
  const [stepIndex, setStepIndex] = useState(0);

  // Land returning students on the step after the last one they completed.
  useEffect(() => {
    if (profile && profile.completed_steps?.length) {
      const lastCompleted = profile.completed_steps[profile.completed_steps.length - 1];
      const next = STEPS.findIndex((s) => s.slug === lastCompleted);
      if (next >= 0 && next < STEPS.length - 1) setStepIndex(next + 1);
    }
  }, [profile?.completed_steps?.length]);  // eslint-disable-line react-hooks/exhaustive-deps

  // Keep the /login picker snapshot in sync — name updates and photo
  // uploads from the wizard propagate into localStorage so the next
  // visit greets the student with the freshest data. Fire-and-forget:
  // an error here should never block the wizard.
  useEffect(() => {
    const authUser = useAuthStore.getState().user;
    if (!authUser || !profile) return;
    useLastProfileStore.getState().remember({
      email: authUser.email,
      full_name: profile.full_name ?? authUser.full_name,
      photo_data_uri: null,
      photo_offset_x: profile.photo_offset_x,
      photo_offset_y: profile.photo_offset_y,
      photo_zoom: profile.photo_zoom,
    });
    if (profile.photo_file_id) {
      void fetchPhotoDataUri().then((uri) => {
        if (uri) useLastProfileStore.getState().patchPhoto(uri);
      });
    } else {
      useLastProfileStore.getState().patchPhoto(null);
    }
  }, [
    profile?.photo_file_id,
    profile?.full_name,
    profile?.photo_offset_x,
    profile?.photo_offset_y,
    profile?.photo_zoom,
  ]);  // eslint-disable-line react-hooks/exhaustive-deps

  const step = STEPS[stepIndex];

  async function markStepDone(slug: string) {
    await updateProfile.mutateAsync({
      mark_steps: [slug],
      current_step: STEPS[Math.min(stepIndex + 1, STEPS.length - 1)].slug,
    });
  }

  function goNext() {
    setStepIndex((i) => Math.min(i + 1, STEPS.length - 1));
  }
  function goPrev() {
    setStepIndex((i) => Math.max(i - 1, 0));
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/60 bg-background/70 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <BrandWordmark variant="careero" size={22} />
          <div className="flex items-center gap-4 text-xs">
            <Link
              to="/feedback"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              Send feedback →
            </Link>
            <SignOutButton />
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ProgressBar
          steps={STEPS}
          stepIndex={stepIndex}
          completed={profile?.completed_steps ?? []}
          onJump={(i) => setStepIndex(i)}
        />

        <Card className="mt-6 rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-semibold tracking-tight">
              {step.title}
            </CardTitle>
            <CardDescription className="text-sm text-muted-foreground">
              {step.blurb}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {profileLoading ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : (
              <StepBody
                stepSlug={step.slug}
                onSaved={async () => {
                  await markStepDone(step.slug);
                  goNext();
                }}
              />
            )}

            <div className="flex items-center justify-between pt-4">
              <Button variant="ghost" onClick={goPrev} disabled={stepIndex === 0}>
                Back
              </Button>
              <div className="text-xs text-muted-foreground">
                Step {stepIndex + 1} of {STEPS.length} · auto-saved
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  void markStepDone(step.slug);
                  goNext();
                }}
                disabled={stepIndex === STEPS.length - 1}
              >
                Skip
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ProgressBar({
  steps,
  stepIndex,
  completed,
  onJump,
}: {
  steps: StepDef[];
  stepIndex: number;
  completed: string[];
  onJump: (i: number) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {steps.map((s, i) => {
        const done = completed.includes(s.slug);
        const active = i === stepIndex;
        return (
          <button
            key={s.slug}
            type="button"
            onClick={() => onJump(i)}
            title={s.title}
            className={
              "h-2 flex-1 min-w-[14px] rounded-full transition-all " +
              (active
                ? "bg-brand-gradient shadow-[0_0_0_2px_hsl(var(--brand-mid)/0.15)]"
                : done
                  ? "bg-brand-gradient opacity-60"
                  : "bg-muted")
            }
          />
        );
      })}
    </div>
  );
}

function StepBody({
  stepSlug,
  onSaved,
}: {
  stepSlug: string;
  onSaved: () => Promise<void> | void;
}) {
  switch (stepSlug) {
    case "basics":
      return <StepBasics onSaved={onSaved} />;
    case "education":
      return <StepEducation onSaved={onSaved} />;
    case "photo":
      return <StepPhoto onSaved={onSaved} />;
    case "summary":
      return <StepSummary onSaved={onSaved} />;
    case "preview":
      return <StepPreview />;
    default:
      return <StepEntries kind={KIND_FOR_STEP[stepSlug]} onSaved={onSaved} />;
  }
}

// ---- Step: Basics ------------------------------------------------------

function StepBasics({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();
  const coachEmail = useCoachEmail();
  const authUser = useAuthStore((s) => s.user);

  const [fullName, setFullName] = useState(
    profile?.full_name ?? authUser?.full_name ?? "",
  );
  const [email, setEmail] = useState(
    profile?.professional_email ?? authUser?.email ?? "",
  );
  const [phone, setPhone] = useState(profile?.phone ?? "");
  const [location, setLocation] = useState(profile?.location ?? "");
  const [dob, setDob] = useState<string | null>(profile?.date_of_birth ?? null);
  const [emailWarnings, setEmailWarnings] = useState<CoachWarning[]>([]);
  const [emailSuggestions, setEmailSuggestions] = useState<CoachSuggestion[]>([]);
  const [emailConfirmed, setEmailConfirmed] = useState(false);

  useEffect(() => {
    if (!profile) return;
    setFullName((current) => current || profile.full_name || authUser?.full_name || "");
    setEmail((current) => current || profile.professional_email || authUser?.email || "");
    setPhone((current) => current || profile.phone || "");
    setLocation((current) => current || profile.location || "");
    setDob((current) => current || profile.date_of_birth || null);
  }, [profile?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps

  useAutoSave(
    { fullName, email, phone, location, dob },
    async ({ fullName, email, phone, location, dob }) => {
      const payload: StudentProfileUpdate = {
        full_name: fullName || null,
        professional_email: email || null,
        phone: phone || null,
        location: location || null,
        date_of_birth: dob,
      };
      try {
        await update.mutateAsync(payload);
      } catch {
        // Auto-save failures are silent; explicit Save & continue surfaces them.
      }
    },
  );

  async function checkEmail() {
    if (!email.trim()) return;
    const res = await coachEmail.mutateAsync({ email, full_name: fullName });
    setEmailWarnings(res.warnings);
    setEmailSuggestions(res.suggestions);
  }

  async function saveAndContinue() {
    if (!emailConfirmed && emailWarnings.length === 0 && email) await checkEmail();
    await update.mutateAsync({
      full_name: fullName || null,
      professional_email: email || null,
      phone: phone || null,
      location: location || null,
      date_of_birth: dob,
    });
    await onSaved();
  }

  const hasBlocker = emailWarnings.some((w) => w.severity === "block");

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="b-fullname">Full name</Label>
        <Input
          id="b-fullname"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Jane Student"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="b-email">Email shown on your CV</Label>
        <Input
          id="b-email"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setEmailConfirmed(false);
            setEmailWarnings([]);
            setEmailSuggestions([]);
          }}
          onBlur={() => void checkEmail()}
          placeholder="jane.student@school.edu"
        />
        <p className="text-xs text-muted-foreground">
          Pre-filled with your sign-in email
          {authUser?.email ? ` (${authUser.email})` : ""}. Edit if you'd
          rather use a school address.
        </p>
        <CoachWarnings
          warnings={emailWarnings}
          suggestions={emailSuggestions}
          onApplySuggestion={(v) => {
            setEmail(v);
            setEmailWarnings([]);
            setEmailSuggestions([]);
          }}
        />
        {emailWarnings.length > 0 && !hasBlocker && (
          <label className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={emailConfirmed}
              onChange={(e) => setEmailConfirmed(e.target.checked)}
            />
            I know, keep this email anyway.
          </label>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="b-phone">Phone</Label>
          <Input
            id="b-phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+966 5 …"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="b-loc">Location</Label>
          <Input
            id="b-loc"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Riyadh, SA"
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label>Date of birth</Label>
        <DateOfBirthPicker value={dob} onChange={setDob} />
        <p className="text-xs text-muted-foreground">
          Shown in the CV header next to your contact details.
        </p>
      </div>
      <div>
        <Button
          onClick={() => void saveAndContinue()}
          disabled={update.isPending || hasBlocker || (emailWarnings.length > 0 && !emailConfirmed)}
        >
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}

// ---- Step: Education ---------------------------------------------------

function StepEducation({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();

  const [university, setUniversity] = useState(profile?.college ?? "");
  const [department, setDepartment] = useState(profile?.department ?? "");
  const [degree, setDegree] = useState(profile?.degree ?? "");
  const [major, setMajor] = useState(profile?.major ?? "");
  const [year, setYear] = useState<string>(
    profile?.graduation_year ? String(profile.graduation_year) : "",
  );

  useEffect(() => {
    if (!profile) return;
    setUniversity((cur) => cur || profile.college || "");
    setDepartment((cur) => cur || profile.department || "");
    setDegree((cur) => cur || profile.degree || "");
    setMajor((cur) => cur || profile.major || "");
    setYear((cur) => cur || (profile.graduation_year ? String(profile.graduation_year) : ""));
  }, [profile?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps

  useAutoSave(
    { university, department, degree, major, year },
    async ({ university, department, degree, major, year }) => {
      try {
        await update.mutateAsync({
          college: university || null,
          department: department || null,
          degree: degree || null,
          major: major || null,
          graduation_year: year ? Number(year) : null,
        });
      } catch {
        // silent
      }
    },
  );

  async function saveAndContinue() {
    await update.mutateAsync({
      college: university || null,
      department: department || null,
      degree: degree || null,
      major: major || null,
      graduation_year: year ? Number(year) : null,
    });
    await onSaved();
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>University</Label>
        <Combobox
          value={university}
          onChange={setUniversity}
          options={UNIVERSITIES}
          placeholder="Start typing…"
        />
      </div>
      <div className="space-y-2">
        <Label>Faculty / department (optional)</Label>
        <Input
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          placeholder="School of Engineering"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Degree</Label>
          <Select
            value={degree}
            onChange={(e) => setDegree(e.target.value)}
            placeholder="Select a degree…"
            options={[
              { value: "", label: "—" },
              ...DEGREES.map((d) => ({ value: d, label: d })),
            ]}
          />
        </div>
        <div className="space-y-2">
          <Label>Graduation year</Label>
          <Input
            inputMode="numeric"
            value={year}
            onChange={(e) => setYear(e.target.value.replace(/[^0-9]/g, ""))}
            placeholder="2027"
            maxLength={4}
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label>Major</Label>
        <Combobox
          value={major}
          onChange={setMajor}
          options={MAJORS}
          placeholder="Computer Science"
        />
      </div>
      <div>
        <Button onClick={() => void saveAndContinue()} disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}

// ---- Step: Photo -------------------------------------------------------

function StepPhoto({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const upload = useUploadStudentPhoto();
  const coach = useCoachPhoto();
  const updateProfile = useUpdateStudentProfile();
  const photoUrl = useStudentPhotoBlob(profile?.photo_file_id);
  const [warnings, setWarnings] = useState<CoachWarning[]>([]);
  const [summary, setSummary] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  async function onPick(file: File) {
    const judgement = await coach.mutateAsync(file).catch(() => null);
    if (judgement) {
      setWarnings(judgement.warnings);
      setSummary(judgement.summary);
    }
    await upload.mutateAsync(file);
    toast.success("Photo saved");
  }

  // Debounce autosave for the crop transform — the positioner fires
  // `onChange` on every pointer settle and every wheel tick.
  const saveTransformRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  function saveTransform(next: {
    photo_offset_x: number;
    photo_offset_y: number;
    photo_zoom: number;
  }) {
    if (saveTransformRef.current) clearTimeout(saveTransformRef.current);
    saveTransformRef.current = setTimeout(() => {
      void updateProfile.mutateAsync(next);
    }, 250);
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Optional — a clean, well-lit head-and-shoulders photo helps recruiters put a
        face to your name. Selfies at odd angles or party photos read as casual.
      </p>
      <div className="flex items-center gap-4">
        {photoUrl ? (
          <PhotoPositioner
            photoUrl={photoUrl}
            offsetX={profile?.photo_offset_x ?? 50}
            offsetY={profile?.photo_offset_y ?? 50}
            zoom={profile?.photo_zoom ?? 100}
            onChange={saveTransform}
          />
        ) : (
          <div className="grid h-28 w-28 place-items-center rounded-full bg-muted text-xs text-muted-foreground ring-1 ring-border">
            No photo
          </div>
        )}
        <label className="cursor-pointer rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent">
          {photoUrl ? "Replace photo" : "Upload photo"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onPick(f);
            }}
          />
        </label>
      </div>
      {summary && (
        <p className="text-sm text-muted-foreground">
          <span className="font-medium">Reviewer:</span> {summary}
        </p>
      )}
      <CoachWarnings warnings={warnings} />
      {warnings.length > 0 && (
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I'm happy with this photo.
        </label>
      )}
      <div>
        <Button
          onClick={() => void onSaved()}
          disabled={warnings.length > 0 && !confirmed}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}

// ---- Step: Summary -----------------------------------------------------

function StepSummary({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();
  const draft = useDraftSummary();
  const [headline, setHeadline] = useState(profile?.headline ?? "");
  const [summary, setSummary] = useState(profile?.summary ?? "");
  const [links, setLinks] = useState<StudentLinks>(profile?.links ?? {});
  const [draftedNotes, setDraftedNotes] = useState<string[]>([]);
  const [autoDraftAttempted, setAutoDraftAttempted] = useState(false);

  useEffect(() => {
    if (!profile) return;
    setHeadline((current) => current || profile.headline || "");
    setSummary((current) => current || profile.summary || "");
    setLinks(profile.links ?? {});
  }, [profile?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (autoDraftAttempted) return;
    if (!profile) return;
    if (profile.headline || profile.summary) return;
    setAutoDraftAttempted(true);
    void generateDraft({ silent: true });
  }, [profile?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps

  useAutoSave({ headline, summary, links }, async ({ headline, summary, links }) => {
    try {
      await update.mutateAsync({
        headline: headline || null,
        summary: summary || null,
        links,
      });
    } catch {
      // silent
    }
  });

  async function generateDraft({ silent }: { silent?: boolean } = {}) {
    const res = await draft.mutateAsync();
    if (!res.ok) {
      setDraftedNotes(res.notes);
      if (!silent) toast.error(res.notes[0] ?? "Coach couldn't draft yet — try again.");
      return;
    }
    setDraftedNotes(res.notes);
    setHeadline(res.headline);
    setSummary(res.summary);
  }

  async function save() {
    await update.mutateAsync({
      headline: headline || null,
      summary: summary || null,
      links,
    });
    await onSaved();
  }

  const drafting = draft.isPending;

  return (
    <div className="space-y-5">
      <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
        <div className="font-medium">Coach draft</div>
        <div className="mt-1 text-xs text-muted-foreground">
          {drafting
            ? "Drafting from your education, skills, projects, and the rest…"
            : "We drafted a starter headline + summary from what you've shared. Edit anything below; nothing is locked in until you continue."}
        </div>
        <div className="mt-2 flex gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => void generateDraft()}
            disabled={drafting}
          >
            {drafting ? "Thinking…" : "Regenerate draft"}
          </Button>
        </div>
        {draftedNotes.length > 0 && (
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
            {draftedNotes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-2">
        <Label>Headline</Label>
        <Input
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder={drafting ? "Drafting…" : "CS undergrad — backend & ML side-projects"}
          disabled={drafting && !headline}
        />
      </div>
      <div className="space-y-2">
        <Label>Summary</Label>
        <Textarea
          rows={6}
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder={drafting ? "Drafting…" : "A short paragraph about who you are and what you care about."}
          disabled={drafting && !summary}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>GitHub URL</Label>
          <Input
            value={links.github ?? ""}
            onChange={(e) => setLinks({ ...links, github: e.target.value || null })}
            placeholder="https://github.com/you"
          />
        </div>
        <div className="space-y-2">
          <Label>LinkedIn URL</Label>
          <Input
            value={links.linkedin ?? ""}
            onChange={(e) => setLinks({ ...links, linkedin: e.target.value || null })}
            placeholder="https://linkedin.com/in/you"
          />
        </div>
        <div className="space-y-2">
          <Label>Personal website</Label>
          <Input
            value={links.website ?? ""}
            onChange={(e) => setLinks({ ...links, website: e.target.value || null })}
          />
        </div>
        <div className="space-y-2">
          <Label>Portfolio URL</Label>
          <Input
            value={links.portfolio ?? ""}
            onChange={(e) => setLinks({ ...links, portfolio: e.target.value || null })}
          />
        </div>
      </div>
      <div>
        <Button onClick={() => void save()} disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}

// ---- Step: Entries (per-kind specialization) --------------------------

function StepEntries({
  kind,
  onSaved,
}: {
  kind: StudentEntryKind;
  onSaved: () => Promise<void> | void;
}) {
  const { data: entries = [] } = useStudentEntries();
  const items = useMemo(() => entries.filter((e) => e.kind === kind), [entries, kind]);

  return (
    <div className="space-y-5">
      {items.length > 0 && (
        <div className="space-y-2">
          {items.map((e) => (
            <EntryRow key={e.id} entry={e} kind={kind} />
          ))}
        </div>
      )}

      <EntryForm kind={kind} />

      <div>
        <Button onClick={() => void onSaved()}>Continue</Button>
      </div>
    </div>
  );
}

function EntryRow({ entry, kind }: { entry: StudentEntry; kind: StudentEntryKind }) {
  const remove = useDeleteStudentEntry();
  const [editing, setEditing] = useState(false);

  if (editing) {
    return (
      <EntryForm
        kind={kind}
        entry={entry}
        onCancel={() => setEditing(false)}
      />
    );
  }

  return (
    <div className="flex items-start justify-between gap-3 rounded-md border bg-muted/20 p-3">
      <div className="min-w-0">
        <div className="font-medium">{entry.title}</div>
        {kind === "language" && entry.details?.proficiency ? (
          <div className="text-xs text-muted-foreground">{String(entry.details.proficiency)}</div>
        ) : kind === "skill" && entry.details?.proficiency ? (
          <div className="text-xs text-muted-foreground">
            Proficiency {String(entry.details.proficiency)}/5
          </div>
        ) : entry.organization ? (
          <div className="text-xs text-muted-foreground">{entry.organization}</div>
        ) : null}
        {entry.description && (
          <div className="mt-1 text-sm text-muted-foreground line-clamp-2">{entry.description}</div>
        )}
        {kind === "project" && Array.isArray(entry.details?.tech_stack) && (
          <div className="mt-1 flex flex-wrap gap-1">
            {(entry.details.tech_stack as unknown[]).map((t, i) => (
              <span
                key={i}
                className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] text-muted-foreground"
              >
                {String(t)}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="flex flex-col items-end gap-1 shrink-0">
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="text-xs text-muted-foreground hover:text-primary"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => void remove.mutateAsync(entry.id)}
          className="text-xs text-muted-foreground hover:text-destructive"
        >
          Remove
        </button>
      </div>
    </div>
  );
}

// Per-kind entry form — small, focused, and uses the right control per
// field. Handles both "add new" (no `entry` prop) and "edit existing"
// (pre-populates from `entry`, calls PUT instead of POST).
function EntryForm({
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
    setCoachSuggestion(null);
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
    if (kind === "project" && techStack.length > 0) details.tech_stack = techStack;

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
            placeholder="Open-source REST API"
          />
        </Field>
        <Field label="Description">
          <Textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What did you build? What problem did it solve? What did you learn?"
          />
        </Field>
        <Field label="Tech stack">
          <div className="space-y-2">
            <Combobox
              value={techInput}
              onChange={setTechInput}
              onBlurCommit={(v) => addTech(v)}
              options={TECH_STACK}
              placeholder="Type a tech and press Enter…"
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
        <Field label="URL (optional)">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/you/project"
          />
        </Field>
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

const SINGULAR: Record<StudentEntryKind, string> = {
  skill: "skill",
  course: "course",
  project: "project",
  volunteer: "volunteer experience",
  language: "language",
  certificate: "certificate",
  award: "award",
  extracurricular: "activity",
};

// ---- Step: Preview -----------------------------------------------------

function StepPreview() {
  const { data: profile } = useStudentProfile();
  const { data: entries = [] } = useStudentEntries();
  const { data: templatesResp } = useCvTemplates();
  const updateProfile = useUpdateStudentProfile();
  const updateEntry = useUpdateStudentEntry();
  const proofread = useProofread();
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  // Currently previewed template slug. Not necessarily saved — user
  // must click "Set as default" to persist the choice.
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  // Flipped true after a successful download; drives the survey card.
  // Local state only — refreshing the page hides the card, and it
  // returns on the next successful download.
  const [showSurvey, setShowSurvey] = useState(false);
  // Fixes returned by the coach that the student hasn't acted on yet.
  const [fixes, setFixes] = useState<ProofreadFix[]>([]);
  const [proofreadNotes, setProofreadNotes] = useState<string[]>([]);
  // Track which fix is currently being applied so we can disable its
  // button without re-rendering the whole list unnecessarily.
  const [applyingIndex, setApplyingIndex] = useState<number | null>(null);

  // Seed selection from profile → template list default. Runs whenever
  // the templates list resolves — first render just sees `null`.
  useEffect(() => {
    if (selectedSlug) return;
    const seed =
      profile?.cv_template_slug ??
      templatesResp?.default_slug ??
      templatesResp?.items[0]?.slug ??
      null;
    if (seed) setSelectedSlug(seed);
  }, [profile?.cv_template_slug, templatesResp, selectedSlug]);

  async function loadPreview(slug: string | null = selectedSlug) {
    setLoading(true);
    try {
      const h = await fetchCvPreviewHtml(slug ?? undefined);
      setHtml(h);
    } catch {
      toast.error("Could not load preview");
    } finally {
      setLoading(false);
    }
  }

  // Reload preview when the picked template changes.
  useEffect(() => {
    if (selectedSlug) void loadPreview(selectedSlug);
  }, [selectedSlug]);  // eslint-disable-line react-hooks/exhaustive-deps

  const savedSlug =
    profile?.cv_template_slug ?? templatesResp?.default_slug ?? null;
  const canSaveAsDefault =
    !!selectedSlug && selectedSlug !== profile?.cv_template_slug;

  async function saveAsDefault() {
    if (!selectedSlug) return;
    try {
      await updateProfile.mutateAsync({ cv_template_slug: selectedSlug });
      toast.success("Saved — this is now your default template.");
    } catch {
      toast.error("Couldn't save your default template.");
    }
  }

  async function download() {
    setDownloading(true);
    try {
      const blob = await downloadStudentCv(selectedSlug ?? undefined);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const fname = (profile?.full_name ?? "cv").replace(/\s+/g, "_");
      a.download = `${fname}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      // Prompt for a rating right after a successful download.
      setShowSurvey(true);
    } catch (err) {
      const status = (err as { response?: { status?: number } } | undefined)?.response?.status;
      if (status === 503) {
        toast.error(
          "PDF renderer isn't installed in this environment. Rebuild the backend image to install WeasyPrint system deps.",
        );
      } else {
        toast.error("Could not download PDF");
      }
    } finally {
      setDownloading(false);
    }
  }

  async function runProofread() {
    const res = await proofread.mutateAsync();
    setProofreadNotes(res.notes);
    setFixes(res.fixes);
    if (res.ok && res.fixes.length === 0) {
      toast.success("Looks good — no fixes to suggest.");
    }
    if (!res.ok && res.notes.length > 0) {
      toast.error(res.notes[0]);
    }
  }

  async function applyFix(fix: ProofreadFix, i: number) {
    setApplyingIndex(i);
    try {
      if (fix.entity_kind === "profile") {
        const patch: StudentProfileUpdate =
          fix.field === "summary"
            ? { summary: fix.suggested }
            : { headline: fix.suggested };
        await updateProfile.mutateAsync(patch);
      } else if (fix.entity_kind === "entry" && fix.entity_id) {
        const entry = entries.find((e) => e.id === fix.entity_id);
        if (!entry) {
          toast.error("That entry no longer exists — skipped.");
          setFixes((prev) => prev.filter((_, idx) => idx !== i));
          return;
        }
        const nextTitle = fix.field === "title" ? fix.suggested : entry.title;
        const nextDesc =
          fix.field === "description" ? fix.suggested : entry.description;
        await updateEntry.mutateAsync({
          id: entry.id,
          payload: {
            kind: entry.kind,
            title: nextTitle,
            organization: entry.organization,
            start_date: entry.start_date,
            end_date: entry.end_date,
            is_current: entry.is_current,
            description: nextDesc,
            url: entry.url,
            details: entry.details,
            sort_order: entry.sort_order,
          },
        });
      }
      setFixes((prev) => prev.filter((_, idx) => idx !== i));
      // Refresh the preview so the student sees the improvement immediately.
      void loadPreview();
    } catch {
      toast.error("Couldn't apply that one — try again.");
    } finally {
      setApplyingIndex(null);
    }
  }

  function ignoreFix(i: number) {
    setFixes((prev) => prev.filter((_, idx) => idx !== i));
  }

  const templates = templatesResp?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <p className="flex-1 text-sm text-muted-foreground">
          This is what recruiters will see. Give it one last polish, then
          download.
        </p>
        <Button
          type="button"
          variant="outline"
          onClick={() => void runProofread()}
          disabled={proofread.isPending}
        >
          {proofread.isPending ? "Proofreading…" : "Proofread with AI"}
        </Button>
        <Button
          variant="brand"
          size="lg"
          onClick={() => void download()}
          disabled={downloading}
        >
          {downloading ? "Preparing…" : "Download PDF"}
        </Button>
      </div>

      {templates.length > 1 && (
        <div className="space-y-3 rounded-2xl border border-border/60 bg-muted/20 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-medium">Template</div>
              <div className="text-xs text-muted-foreground">
                Click any style to preview it. Set as default to save your
                choice — Download uses whatever is showing.
              </div>
            </div>
            {canSaveAsDefault && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void saveAsDefault()}
                disabled={updateProfile.isPending}
              >
                {updateProfile.isPending ? "Saving…" : "Set as default"}
              </Button>
            )}
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {templates.map((t) => {
              const active = selectedSlug === t.slug;
              const isSaved = savedSlug === t.slug;
              return (
                <button
                  key={t.slug}
                  type="button"
                  onClick={() => setSelectedSlug(t.slug)}
                  className={`group relative min-w-[200px] flex-shrink-0 overflow-hidden rounded-xl border p-3 text-left transition-all ${
                    active
                      ? "border-transparent bg-background shadow-md ring-2 ring-primary/60"
                      : "border-border/70 bg-background hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-sm"
                  }`}
                >
                  {active && (
                    <span
                      aria-hidden
                      className="pointer-events-none absolute inset-x-0 top-0 h-0.5 bg-brand-gradient"
                    />
                  )}
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold tracking-tight">
                      {t.display_name}
                    </div>
                    {isSaved && (
                      <span className="bg-brand-gradient rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                        Default
                      </span>
                    )}
                  </div>
                  <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                    {t.description}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {(fixes.length > 0 || proofreadNotes.length > 0) && (
        <div className="space-y-2 rounded-md border border-primary/30 bg-primary/5 p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">
              Coach found {fixes.length} suggestion{fixes.length === 1 ? "" : "s"}
            </div>
            {fixes.length > 0 && (
              <button
                type="button"
                className="text-xs text-muted-foreground hover:text-foreground"
                onClick={() => setFixes([])}
              >
                Dismiss all
              </button>
            )}
          </div>
          {proofreadNotes.map((n, i) => (
            <div key={i} className="text-xs text-muted-foreground">
              {n}
            </div>
          ))}
          <div className="space-y-2">
            {fixes.map((fix, i) => (
              <FixCard
                key={i}
                fix={fix}
                applying={applyingIndex === i}
                onApply={() => void applyFix(fix, i)}
                onIgnore={() => ignoreFix(i)}
              />
            ))}
          </div>
        </div>
      )}

      {showSurvey && (
        <PostDownloadSurvey
          templateSlug={selectedSlug}
          onDismiss={() => setShowSurvey(false)}
        />
      )}

      <div className="overflow-hidden rounded-2xl border border-border/40 bg-white shadow-xl">
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading…</div>
        ) : html ? (
          <iframe
            title="CV preview"
            srcDoc={html}
            className="h-[900px] w-full"
            sandbox="allow-same-origin"
          />
        ) : (
          <div className="p-8 text-center text-sm text-muted-foreground">No preview</div>
        )}
      </div>

      <AboutFooter className="pt-2" />
    </div>
  );
}

function FixCard({
  fix,
  applying,
  onApply,
  onIgnore,
}: {
  fix: ProofreadFix;
  applying: boolean;
  onApply: () => void;
  onIgnore: () => void;
}) {
  const badge = CATEGORY_BADGE[fix.category];
  const where = LOCATION_LABEL[fix.field] + (fix.entity_kind === "entry" ? " (entry)" : "");
  return (
    <div className="rounded-md border bg-background p-3 text-sm">
      <div className="mb-1 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={
              "rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide " +
              badge.className
            }
          >
            {badge.label}
          </span>
          <span className="text-xs text-muted-foreground">{where}</span>
        </div>
        <div className="flex gap-1">
          <Button size="sm" onClick={onApply} disabled={applying}>
            {applying ? "…" : "Apply"}
          </Button>
          <Button size="sm" variant="ghost" onClick={onIgnore} disabled={applying}>
            Ignore
          </Button>
        </div>
      </div>
      <div className="text-xs text-muted-foreground">{fix.reason}</div>
      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Original
          </div>
          <div className="mt-0.5 whitespace-pre-wrap rounded bg-destructive/5 p-2 text-xs">
            {fix.original}
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Suggested
          </div>
          <div className="mt-0.5 whitespace-pre-wrap rounded bg-primary/5 p-2 text-xs">
            {fix.suggested}
          </div>
        </div>
      </div>
    </div>
  );
}

const CATEGORY_BADGE: Record<
  ProofreadFix["category"],
  { label: string; className: string }
> = {
  typo: { label: "Typo", className: "bg-destructive/10 text-destructive" },
  grammar: { label: "Grammar", className: "bg-amber-500/10 text-amber-600" },
  clarity: { label: "Clarity", className: "bg-primary/10 text-primary" },
  style: { label: "Style", className: "bg-muted text-foreground" },
};

const LOCATION_LABEL: Record<ProofreadFix["field"], string> = {
  summary: "Summary",
  headline: "Headline",
  description: "Description",
  title: "Title",
};

function SignOutButton() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const email = useAuthStore((s) => s.user?.email);
  return (
    <div className="flex items-center gap-2">
      {email && (
        <span className="hidden max-w-[180px] truncate text-muted-foreground md:inline">
          {email}
        </span>
      )}
      <button
        type="button"
        onClick={() => {
          logout();
          navigate("/login", { replace: true });
        }}
        className="rounded-md border border-border/60 px-2 py-1 text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
      >
        Sign out
      </button>
    </div>
  );
}
