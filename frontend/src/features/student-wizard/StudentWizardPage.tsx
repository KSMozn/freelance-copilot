import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { logoutCurrentSurface } from "@/app/apiClient";
import { useAuthStore } from "@/features/auth/authStore";
import { useLastProfileStore } from "@/features/auth/lastProfileStore";
import { fetchPhotoDataUri } from "@/features/student-wizard/photoCache";
import { useStudentProfile, useUpdateStudentProfile } from "@/features/student-wizard/studentApi";
import type { StudentEntryKind } from "@/features/student-wizard/studentTypes";
import { AppShell } from "@/shared/layout/AppShell";
import { PageContainer } from "@/shared/layout/PageContainer";
import { BrandWordmark } from "@/shared/ui/brand/BrandWordmark";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

import { FeedbackDialog } from "./feedback/FeedbackDialog";
import { StepBasics } from "./steps/StepBasics";
import { StepEducation } from "./steps/StepEducation";
import { StepEntries } from "./steps/StepEntries";
import { StepInternships } from "./steps/StepInternships";
import { StepPhoto } from "./steps/StepPhoto";
import { StepPreview } from "./steps/StepPreview";
import { StepStarterPack } from "./steps/StepStarterPack";
import { StepSummary } from "./steps/StepSummary";

interface StepDef {
  slug: string;
  title: string;
  blurb: string;
}

const STEPS: StepDef[] = [
  { slug: "basics", title: "About you", blurb: "Name, email, where you're based." },
  { slug: "education", title: "Where you study", blurb: "University, department, degree." },
  { slug: "photo", title: "Profile photo", blurb: "Optional — but a clean photo helps." },
  {
    slug: "skills",
    title: "Skills",
    blurb: "Things you can do. Pick from the list or type your own.",
  },
  { slug: "courses", title: "Coursework", blurb: "Relevant courses you've taken." },
  { slug: "projects", title: "Projects", blurb: "What you've built." },
  {
    slug: "internships",
    title: "Internships",
    blurb: "Optional — internships, summer training, or practical experience you've done.",
  },
  { slug: "volunteer", title: "Volunteer work", blurb: "Where you've contributed." },
  { slug: "languages", title: "Languages", blurb: "Spoken / written languages." },
  { slug: "certificates", title: "Certificates", blurb: "Any certifications or courses." },
  {
    slug: "summary",
    title: "Summary",
    blurb: "We'll draft a headline + summary from what you've shared — edit freely.",
  },
  { slug: "preview", title: "Preview & download", blurb: "Your CV, ready to share." },
  {
    slug: "starter-pack",
    title: "Career Starter Pack",
    blurb: "Optional next steps to strengthen your internship application.",
  },
];

const KIND_FOR_STEP: Record<string, StudentEntryKind> = {
  skills: "skill",
  courses: "course",
  projects: "project",
  internships: "internship",
  volunteer: "volunteer",
  languages: "language",
  certificates: "certificate",
};

// Two save models coexist in the wizard and the footer must not lie about
// which one is active: profile steps persist via useAutoSave (debounced),
// while entry/internship steps only persist on their explicit Add/Save
// buttons — an unsubmitted form is discarded on navigation. Preview and
// the starter pack capture nothing, so they make no save claim at all.
type SaveModel = "auto" | "manual" | "none";

const SAVE_MODEL: Record<string, SaveModel> = {
  basics: "auto",
  education: "auto",
  photo: "auto",
  summary: "auto",
  skills: "manual",
  courses: "manual",
  projects: "manual",
  internships: "manual",
  volunteer: "manual",
  languages: "manual",
  certificates: "manual",
  preview: "none",
  "starter-pack": "none",
};

const SAVE_HINT: Record<SaveModel, string | null> = {
  auto: "Changes auto-saved",
  manual: "Click save to keep your changes",
  none: null,
};

export function StudentWizardPage() {
  const { data: profile, isLoading: profileLoading } = useStudentProfile();
  const updateProfile = useUpdateStudentProfile();
  const [searchParams] = useSearchParams();
  // Deep-link support: `?step=<slug>` lands the wizard directly on that
  // tab (used by admin-triggered email CTAs). Unknown slugs fall through.
  const requestedStepIndex = useMemo(() => {
    const slug = searchParams.get("step");
    if (!slug) return -1;
    return STEPS.findIndex((s) => s.slug === slug);
  }, [searchParams]);
  const [stepIndex, setStepIndex] = useState(() =>
    requestedStepIndex >= 0 ? requestedStepIndex : 0,
  );

  // Land returning students on the step after the last one they completed —
  // unless a `?step=` deep-link is present, in which case the URL wins.
  //
  // Resume is an INITIAL-HYDRATION behavior: it fires exactly once, when the
  // profile first arrives. It must NOT re-fire on later completed_steps
  // changes — Preview auto-marks itself complete on first land, and the old
  // every-change version re-triggered here and yanked the student straight
  // to the Starter Pack (the "preview auto-advance" bug).
  const resumedRef = useRef(false);
  useEffect(() => {
    if (resumedRef.current) return;
    if (requestedStepIndex >= 0) {
      resumedRef.current = true; // deep link wins — never auto-resume afterwards
      return;
    }
    if (!profile) return;
    resumedRef.current = true;
    if (profile.completed_steps?.length) {
      const lastCompleted = profile.completed_steps[profile.completed_steps.length - 1];
      const next = STEPS.findIndex((s) => s.slug === lastCompleted);
      if (next >= 0 && next < STEPS.length - 1) setStepIndex(next + 1);
    }
  }, [profile, requestedStepIndex]);

  // Keep the /login picker snapshot in sync — name updates and photo
  // uploads from the wizard propagate into localStorage so the next
  // visit greets the student with the freshest data. Fire-and-forget:
  // an error here should never block the wizard.
  //
  // The fields the effect consumes are narrowed to scalars first so the
  // dependency array is genuinely exhaustive (no eslint-disable) without
  // re-running on every profile refetch — the query returns a fresh
  // object identity each time even when nothing changed.
  const profileLoaded = Boolean(profile);
  const profileFullName = profile?.full_name ?? null;
  const photoFileId = profile?.photo_file_id ?? null;
  const photoOffsetX = profile?.photo_offset_x ?? 50;
  const photoOffsetY = profile?.photo_offset_y ?? 50;
  const photoZoom = profile?.photo_zoom ?? 100;
  useEffect(() => {
    const authUser = useAuthStore.getState().user;
    if (!authUser || !profileLoaded) return;
    useLastProfileStore.getState().remember({
      email: authUser.email,
      full_name: profileFullName ?? authUser.full_name,
      photo_data_uri: null,
      photo_offset_x: photoOffsetX,
      photo_offset_y: photoOffsetY,
      photo_zoom: photoZoom,
    });
    if (photoFileId) {
      void fetchPhotoDataUri().then((uri) => {
        if (uri) useLastProfileStore.getState().patchPhoto(uri);
      });
    } else {
      useLastProfileStore.getState().patchPhoto(null);
    }
  }, [profileLoaded, profileFullName, photoFileId, photoOffsetX, photoOffsetY, photoZoom]);

  const step = STEPS[stepIndex];

  async function markStepDone(slug: string) {
    await updateProfile.mutateAsync({
      mark_steps: [slug],
      current_step: STEPS[Math.min(stepIndex + 1, STEPS.length - 1)].slug,
    });
  }

  // Preview and Career Starter Pack are consume-only steps with no save
  // action, so we auto-mark them done on land — otherwise the admin
  // funnel undercounts and returning students loop back to Preview
  // forever. Every other step must go through its own Save & continue
  // to be marked complete; auto-marking on mere navigation inflates
  // wizard-completion and lies about data that isn't actually captured
  // (a real student was landing on impersonation with `completed_steps`
  // containing all 13 slugs while only their name had been saved).
  useEffect(() => {
    if (!profile) return;
    if (step.slug !== "preview" && step.slug !== "starter-pack") return;
    const already = profile.completed_steps ?? [];
    if (already.includes(step.slug)) return;
    void markStepDone(step.slug);
  }, [step.slug, profile?.completed_steps]); // eslint-disable-line react-hooks/exhaustive-deps

  function goNext() {
    resumedRef.current = true;
    setStepIndex((i) => Math.min(i + 1, STEPS.length - 1));
  }
  function goPrev() {
    resumedRef.current = true;
    setStepIndex((i) => Math.max(i - 1, 0));
  }
  function jumpToStep(index: number) {
    resumedRef.current = true;
    setStepIndex(index);
  }

  const header = (
    <header className="border-b border-border/60 bg-background/70 backdrop-blur">
      <PageContainer className="flex items-center justify-between py-3">
        <BrandWordmark variant="careero" size={22} />
        <div className="flex items-center gap-4 text-xs">
          <FeedbackDialog />
          <SignOutButton />
        </div>
      </PageContainer>
    </header>
  );

  return (
    <AppShell header={header}>
      <ProgressBar
        steps={STEPS}
        stepIndex={stepIndex}
        completed={profile?.completed_steps ?? []}
        onJump={jumpToStep}
      />

      <Card className="mt-6 rounded-2xl border-border/60 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-semibold tracking-tight">{step.title}</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">{step.blurb}</CardDescription>
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
              Step {stepIndex + 1} of {STEPS.length}
              {SAVE_HINT[SAVE_MODEL[step.slug] ?? "none"]
                ? ` · ${SAVE_HINT[SAVE_MODEL[step.slug] ?? "none"]}`
                : ""}
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
    </AppShell>
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
        const done = completed.includes(s.slug) && SAVE_MODEL[s.slug] !== "none";
        const active = i === stepIndex;
        return (
          <button
            key={s.slug}
            type="button"
            onClick={() => onJump(i)}
            title={s.title}
            aria-current={active ? "step" : undefined}
            className={
              "h-2 min-w-[14px] flex-1 rounded-full transition-all " +
              (active
                ? "bg-brand-gradient scale-y-150 shadow-[0_0_0_2px_hsl(var(--background)),0_0_0_4px_hsl(var(--brand-mid)/0.55)]"
                : done
                  ? "bg-primary/50"
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
    case "starter-pack":
      return <StepStarterPack />;
    case "internships":
      return <StepInternships onSaved={onSaved} />;
    default:
      return <StepEntries kind={KIND_FOR_STEP[stepSlug]} onSaved={onSaved} />;
  }
}

function SignOutButton() {
  const navigate = useNavigate();
  const email = useAuthStore((s) => s.user?.email);
  const [signingOut, setSigningOut] = useState(false);
  return (
    <div className="flex items-center gap-2">
      {email && (
        <span className="hidden max-w-[180px] truncate text-muted-foreground md:inline">
          {email}
        </span>
      )}
      <button
        type="button"
        disabled={signingOut}
        onClick={() => {
          setSigningOut(true);
          void logoutCurrentSurface().finally(() => navigate("/login", { replace: true }));
        }}
        className="rounded-md border border-border/60 px-2 py-1 text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
      >
        {signingOut ? "Signing out…" : "Sign out"}
      </button>
    </div>
  );
}
