import { useState } from "react";
import { Copy, Github, Linkedin, Loader2, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCareerPack,
  useClearCareerPack,
  useGenerateGitHub,
  useGenerateLinkedIn,
  useReviewGitHub,
  useReviewLinkedIn,
} from "@/lib/careerPack";
import { useUpdateStudentProfile } from "@/lib/student";
import type {
  CareerStatus,
  GitHubGenerated,
  GitHubProjectReadme,
  GitHubReview,
  LinkedInGenerated,
  LinkedInReview,
} from "@/types/careerPack";

const LINKEDIN_URL_RE = /^https?:\/\/([a-z]{2,3}\.)?linkedin\.com\/(in|pub|profile|company)\/[A-Za-z0-9\-_/%.]+\/?$/i;
const GITHUB_URL_RE = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\/?$/i;

function isLinkedInUrl(url: string): boolean {
  return LINKEDIN_URL_RE.test(url.trim());
}
function isGitHubUrl(url: string): boolean {
  return GITHUB_URL_RE.test(url.trim());
}

const STATUS_META: Record<CareerStatus, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  missing: { label: "Missing", variant: "outline" },
  started: { label: "Started", variant: "secondary" },
  needs_improvement: { label: "Needs improvement", variant: "secondary" },
  completed: { label: "Completed", variant: "default" },
};

export function CareerStarterPack() {
  const { data: pack, isLoading } = useCareerPack();
  if (isLoading || !pack) return null;

  return (
    <section className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Your CV is ready. These optional steps can make your internship
        application stronger.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <LinkedInCard />
        <GitHubCard />
      </div>
    </section>
  );
}

// ---- LinkedIn -----------------------------------------------------------

type LinkedInMode = "auto" | "create" | "enhance";

function LinkedInCard() {
  const { data: pack } = useCareerPack();
  const [manualMode, setManualMode] = useState<LinkedInMode>("auto");
  const [showLinkForm, setShowLinkForm] = useState(false);

  if (!pack) return null;

  const hasUrl = !!pack.linkedin_url;
  const effectiveMode: LinkedInMode =
    manualMode !== "auto" ? manualMode : hasUrl ? "enhance" : "create";
  const status = pack.linkedin_status;
  const meta = STATUS_META[status];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5">
            <CardTitle className="flex items-center gap-2 text-base">
              <Linkedin className="h-4 w-4" />
              {effectiveMode === "create"
                ? "Create your LinkedIn profile"
                : "Improve your LinkedIn profile"}
            </CardTitle>
            <CardDescription>
              {effectiveMode === "create"
                ? "Prepare a student-friendly headline, About section, education, skills, and projects from your CV."
                : "Upload your LinkedIn PDF export and Careero will compare it against your CV and suggest section-by-section changes."}
            </CardDescription>
          </div>
          <Badge variant={meta.variant}>{meta.label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Uncertain / initial prompt — only if no URL AND no local override */}
        {!hasUrl && manualMode === "auto" && (
          <div className="rounded-md border bg-muted/40 p-3 text-sm">
            <p className="mb-2 font-medium">Do you already have a LinkedIn profile?</p>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setManualMode("enhance");
                  setShowLinkForm(true);
                }}
              >
                Yes, I have one
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setManualMode("create")}
              >
                No, help me create one
              </Button>
            </div>
          </div>
        )}

        {effectiveMode === "create" ? (
          <LinkedInCreate onAddLink={() => setShowLinkForm(true)} />
        ) : (
          <LinkedInEnhance />
        )}

        <div className="pt-1 text-xs text-muted-foreground">
          {effectiveMode === "enhance" ? (
            <button
              type="button"
              className="underline hover:text-foreground"
              onClick={() => setManualMode("create")}
            >
              I don't have a LinkedIn yet — help me create one
            </button>
          ) : (
            <button
              type="button"
              className="underline hover:text-foreground"
              onClick={() => {
                setManualMode("enhance");
                setShowLinkForm(true);
              }}
            >
              I actually have a LinkedIn — let me add it
            </button>
          )}
        </div>

        {showLinkForm && (
          <LinkUrlEditor
            side="linkedin"
            initial={pack.linkedin_url ?? ""}
            validator={isLinkedInUrl}
            placeholder="https://linkedin.com/in/you"
            onClose={() => setShowLinkForm(false)}
          />
        )}
      </CardContent>
    </Card>
  );
}

function LinkedInCreate({ onAddLink }: { onAddLink: () => void }) {
  const { data: pack } = useCareerPack();
  const generate = useGenerateLinkedIn();
  const generated = pack?.linkedin_generated ?? null;

  async function run() {
    try {
      await generate.mutateAsync();
      toast.success("LinkedIn content ready.");
    } catch (err) {
      toast.error(errText(err, "Couldn't generate LinkedIn content."));
    }
  }

  return (
    <div className="space-y-3">
      {!generated && (
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="brand"
            onClick={run}
            disabled={generate.isPending}
          >
            {generate.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Generate LinkedIn Content
          </Button>
          <Button size="sm" variant="outline" onClick={onAddLink}>
            I already created one — add link
          </Button>
        </div>
      )}

      {generated && (
        <LinkedInWalkthrough
          generated={generated}
          onRegenerate={run}
          regenerating={generate.isPending}
        />
      )}
    </div>
  );
}

// ---- LinkedIn create — step-by-step walkthrough -----------------------

function LinkedInWalkthrough({
  generated,
  onRegenerate,
  regenerating,
}: {
  generated: LinkedInGenerated;
  onRegenerate: () => Promise<void> | void;
  regenerating: boolean;
}) {
  const [stepIndex, setStepIndex] = useState(0);
  const projects = generated.project_entries;

  // Steps that always show, plus one dynamic step per project (so students
  // paste them one at a time rather than as a wall of text).
  type Step = { title: string; body: React.ReactNode };
  const steps: Step[] = [
    {
      title: "Ready to build your LinkedIn",
      body: (
        <StepIntro
          count={5 + Math.max(projects.length, 1) + 2}
        />
      ),
    },
    {
      title: "Create your LinkedIn account",
      body: <StepAccount />,
    },
    {
      title: "Add a profile photo",
      body: <StepPhoto />,
    },
    {
      title: "Add your headline",
      body: (
        <StepPasteSection
          instructions="On LinkedIn, click your profile → Edit intro → Headline. Paste the text below."
          label="Your headline"
          text={generated.headline}
        />
      ),
    },
    {
      title: "Add your About section",
      body: (
        <StepPasteSection
          instructions="On LinkedIn, click your profile → About → the pencil icon. Paste the text below."
          label="About"
          text={generated.about}
          multiline
        />
      ),
    },
    {
      title: "Add your education",
      body: (
        <StepPasteSection
          instructions="On LinkedIn, click Add profile section → Core → Add education. Fill in the fields — this paragraph fits well in the 'Description' box."
          label="Education entry"
          text={generated.education_entry || "(No education info in your CV yet — you can skip this and add it later.)"}
          multiline
        />
      ),
    },
    ...(projects.length > 0
      ? projects.map((p, i) => ({
          title: `Add project: ${p.name}`,
          body: (
            <StepPasteSection
              instructions="On LinkedIn, Add profile section → Additional → Add projects. Use the name below as the title and paste the description into the 'Description' field."
              label={`Project ${i + 1} of ${projects.length} — ${p.name}`}
              text={p.description}
              multiline
            />
          ),
        }))
      : [
          {
            title: "Add projects",
            body: (
              <p className="text-sm text-muted-foreground">
                No projects listed in your CV yet — you can add some later on
                LinkedIn under <span className="font-medium">Add profile section → Additional → Add projects</span>.
              </p>
            ),
          },
        ]),
    {
      title: "Add your skills",
      body: <StepSkills skills={generated.skills} />,
    },
    {
      title: "Save your profile link",
      body: <StepSaveUrl onSaved={() => setStepIndex((i) => i + 1)} />,
    },
    {
      title: "Nice work",
      body: (
        <div className="space-y-3 text-sm">
          <p>
            That's your LinkedIn built from your CV. When you're ready for
            polish, come back here and pick{" "}
            <span className="font-semibold">Yes, I have one</span> — upload
            your PDF export and Careero will suggest section-by-section
            improvements.
          </p>
        </div>
      ),
    },
  ];

  const totalSteps = steps.length;
  const step = steps[Math.min(stepIndex, totalSteps - 1)];
  const atStart = stepIndex === 0;
  const atEnd = stepIndex === totalSteps - 1;

  return (
    <div className="space-y-3 rounded-md border bg-card p-4">
      <div className="flex items-center justify-between gap-2">
        <Badge variant="outline" className="shrink-0">
          Step {stepIndex + 1} of {totalSteps}
        </Badge>
        <ClearButton side="linkedin" kind="generated" label="Start over" />
      </div>

      <h3 className="text-base font-semibold">{step.title}</h3>
      <div>{step.body}</div>

      <div className="flex items-center justify-between pt-2">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
          disabled={atStart}
        >
          Back
        </Button>
        {atEnd ? (
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              await onRegenerate();
              setStepIndex(0);
            }}
            disabled={regenerating}
          >
            {regenerating && <Loader2 className="h-4 w-4 animate-spin" />}
            Regenerate content
          </Button>
        ) : (
          <Button
            size="sm"
            variant="brand"
            onClick={() => setStepIndex((i) => Math.min(totalSteps - 1, i + 1))}
          >
            Next
          </Button>
        )}
      </div>
    </div>
  );
}

function StepIntro({ count }: { count: number }) {
  return (
    <div className="space-y-2 text-sm">
      <p>
        Careero has prepared your LinkedIn content from your CV. We'll walk
        through <span className="font-semibold">{count} short steps</span> —
        one section at a time — so you can paste each piece into LinkedIn
        without feeling overwhelmed.
      </p>
      <p className="text-muted-foreground">
        You can jump back and forth any time. Nothing is sent to LinkedIn —
        you copy and paste yourself.
      </p>
    </div>
  );
}

function StepAccount() {
  return (
    <div className="space-y-2 text-sm">
      <p>Open a new tab and go to LinkedIn:</p>
      <ol className="list-decimal space-y-1 pl-5">
        <li>
          Visit{" "}
          <a
            href="https://www.linkedin.com/signup"
            target="_blank"
            rel="noreferrer"
            className="text-primary underline"
          >
            linkedin.com/signup
          </a>
          .
        </li>
        <li>Sign up with a personal email you check regularly.</li>
        <li>Pick a password you can remember.</li>
        <li>Verify your email when LinkedIn asks.</li>
      </ol>
      <p className="text-muted-foreground">
        Come back here when your account is ready. Careero never sees your
        LinkedIn password.
      </p>
    </div>
  );
}

function StepPhoto() {
  return (
    <div className="space-y-2 text-sm">
      <p>A clear profile photo makes recruiters trust the page.</p>
      <ul className="list-disc space-y-1 pl-5">
        <li>Face clearly visible, looking at the camera.</li>
        <li>Plain background — a wall or outdoors is fine.</li>
        <li>Neutral clothes. No sunglasses, no group photos.</li>
      </ul>
      <p className="text-muted-foreground">
        On LinkedIn: click your profile picture → the camera icon → upload.
      </p>
    </div>
  );
}

function StepPasteSection({
  instructions,
  label,
  text,
  multiline,
}: {
  instructions: string;
  label: string;
  text: string;
  multiline?: boolean;
}) {
  return (
    <div className="space-y-3 text-sm">
      <p>{instructions}</p>
      <FieldBlock label={label} text={text} multiline={multiline} subtle />
    </div>
  );
}

function StepSkills({ skills }: { skills: string[] }) {
  if (skills.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No skills to suggest yet — add some to your CV and regenerate.
      </p>
    );
  }
  return (
    <div className="space-y-3 text-sm">
      <p>
        On LinkedIn: <span className="font-medium">Add profile section → Core → Add skills</span>.
        Type each one below into the search box and pick it.
      </p>
      <BulletList label="Skills to add" items={skills} chip />
    </div>
  );
}

function StepSaveUrl({ onSaved }: { onSaved: () => void }) {
  const { data: pack } = useCareerPack();
  const [url, setUrl] = useState(pack?.linkedin_url ?? "");
  const updateProfile = useUpdateStudentProfile();

  async function save() {
    const trimmed = url.trim();
    if (trimmed && !isLinkedInUrl(trimmed)) {
      toast.error("That doesn't look like a LinkedIn profile URL.");
      return;
    }
    try {
      await updateProfile.mutateAsync({
        links: { linkedin: trimmed || null },
      });
      toast.success("Saved.");
      onSaved();
    } catch {
      toast.error("Couldn't save the link.");
    }
  }

  return (
    <div className="space-y-3 text-sm">
      <p>
        On LinkedIn, copy the URL from your browser once your profile is up
        (looks like <span className="font-mono">linkedin.com/in/your-name</span>).
        Paste it below so Careero remembers where your profile lives.
      </p>
      <Input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://linkedin.com/in/you"
      />
      <div className="flex justify-end">
        <Button
          size="sm"
          variant="brand"
          onClick={save}
          disabled={updateProfile.isPending}
        >
          {updateProfile.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          Save profile URL
        </Button>
      </div>
    </div>
  );
}

function LinkedInEnhance() {
  const { data: pack } = useCareerPack();
  const [url, setUrl] = useState(pack?.linkedin_url ?? "");
  const [file, setFile] = useState<File | null>(null);
  const review = useReviewLinkedIn();
  const recs = pack?.linkedin_recommendations ?? null;

  async function submitReview() {
    if (!isLinkedInUrl(url)) {
      toast.error("Enter your LinkedIn profile URL (linkedin.com/in/…).");
      return;
    }
    if (!file) {
      toast.error("Attach your LinkedIn PDF export.");
      return;
    }
    try {
      await review.mutateAsync({ linkedinUrl: url.trim(), file });
      toast.success("Review ready.");
      setFile(null);
    } catch (err) {
      toast.error(errText(err, "Couldn't review your LinkedIn profile."));
    }
  }

  return (
    <div className="space-y-3">
      <div className="rounded-md border border-primary/40 bg-primary/10 p-4 text-sm text-foreground">
        <p className="mb-2 font-semibold">
          How to export your LinkedIn profile
        </p>
        <ol className="list-decimal space-y-1 pl-5">
          <li>Open your LinkedIn profile page.</li>
          <li>
            Click <span className="font-semibold">Me</span> (top-right avatar)
            {" "}→ <span className="font-semibold">View Profile</span>.
          </li>
          <li>
            Click <span className="font-semibold">Resources</span> →{" "}
            <span className="font-semibold">Save to PDF</span>.
          </li>
          <li>Upload the downloaded PDF below.</li>
        </ol>
        <p className="mt-2 text-xs text-muted-foreground">
          Careero doesn't fetch or scrape LinkedIn. We only read the PDF you
          upload, then compare it against your CV.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="li-url" className="text-xs">
          LinkedIn profile URL
        </Label>
        <Input
          id="li-url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://linkedin.com/in/you"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="li-file" className="text-xs">
          LinkedIn PDF export
        </Label>
        <Input
          id="li-file"
          type="file"
          accept="application/pdf,.pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {file && (
          <p className="text-xs text-muted-foreground">
            Selected: {file.name}
          </p>
        )}
      </div>

      <div className="flex justify-end">
        <Button
          size="sm"
          variant="brand"
          onClick={submitReview}
          disabled={review.isPending}
        >
          {review.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {recs ? "Re-review" : "Review my LinkedIn"}
        </Button>
      </div>

      {recs && <LinkedInReviewView data={recs} />}
    </div>
  );
}

function LinkedInReviewView({ data }: { data: LinkedInReview }) {
  return (
    <div className="space-y-3 rounded-md border bg-card p-3">
      <div className="flex justify-end">
        <ClearButton side="linkedin" kind="recommendations" />
      </div>
      <p className="text-sm">{data.summary}</p>
      {data.current_headline_review && (
        <FieldBlock label="Headline review" text={data.current_headline_review} multiline />
      )}
      {data.suggested_headline && (
        <FieldBlock label="Suggested headline" text={data.suggested_headline} />
      )}
      {data.current_about_review && (
        <FieldBlock label="About review" text={data.current_about_review} multiline />
      )}
      {data.suggested_about && (
        <FieldBlock label="Suggested About" text={data.suggested_about} multiline />
      )}
      {data.missing_sections.length > 0 && (
        <BulletList label="Missing sections" items={data.missing_sections} />
      )}
      {data.skills_to_add.length > 0 && (
        <BulletList label="Skills to add" items={data.skills_to_add} chip />
      )}
      {data.projects_to_improve.length > 0 && (
        <BulletList label="Projects to improve" items={data.projects_to_improve} />
      )}
      {data.checklist.length > 0 && (
        <BulletList label="Change checklist" items={data.checklist} />
      )}
    </div>
  );
}

// ---- GitHub -------------------------------------------------------------

type GitHubMode = "auto" | "create" | "enhance";

function GitHubCard() {
  const { data: pack } = useCareerPack();
  const [manualMode, setManualMode] = useState<GitHubMode>("auto");
  const [showLinkForm, setShowLinkForm] = useState(false);

  if (!pack) return null;

  const hasUrl = !!pack.github_url;
  const effectiveMode: GitHubMode =
    manualMode !== "auto" ? manualMode : hasUrl ? "enhance" : "create";
  const status = pack.github_status;
  const meta = STATUS_META[status];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5">
            <CardTitle className="flex items-center gap-2 text-base">
              <Github className="h-4 w-4" />
              {effectiveMode === "create"
                ? "Create your GitHub profile"
                : "Improve your GitHub profile"}
            </CardTitle>
            <CardDescription>
              {effectiveMode === "create"
                ? "Prepare your bio, profile README, and project READMEs from your CV projects and skills."
                : "Review your public GitHub profile and repositories, then improve your bio, README files, and project descriptions."}
            </CardDescription>
          </div>
          <Badge variant={meta.variant}>{meta.label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!hasUrl && manualMode === "auto" && (
          <div className="rounded-md border bg-muted/40 p-3 text-sm">
            <p className="mb-2 font-medium">Do you already have a GitHub profile?</p>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setManualMode("enhance");
                  setShowLinkForm(true);
                }}
              >
                Yes, I have one
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setManualMode("create")}
              >
                No, help me create one
              </Button>
            </div>
          </div>
        )}

        {effectiveMode === "create" ? (
          <GitHubCreate onAddLink={() => setShowLinkForm(true)} />
        ) : (
          <GitHubEnhance />
        )}

        <div className="pt-1 text-xs text-muted-foreground">
          {effectiveMode === "enhance" ? (
            <button
              type="button"
              className="underline hover:text-foreground"
              onClick={() => setManualMode("create")}
            >
              I don't have a GitHub yet — help me create one
            </button>
          ) : (
            <button
              type="button"
              className="underline hover:text-foreground"
              onClick={() => {
                setManualMode("enhance");
                setShowLinkForm(true);
              }}
            >
              I actually have a GitHub — let me add it
            </button>
          )}
        </div>

        {(showLinkForm || (hasUrl && effectiveMode === "enhance")) && (
          <LinkUrlEditor
            side="github"
            initial={pack.github_url ?? ""}
            validator={isGitHubUrl}
            placeholder="https://github.com/you"
            onClose={() => setShowLinkForm(false)}
          />
        )}
      </CardContent>
    </Card>
  );
}

function GitHubCreate({ onAddLink }: { onAddLink: () => void }) {
  const { data: pack } = useCareerPack();
  const generate = useGenerateGitHub();
  const generated = pack?.github_generated ?? null;

  async function run() {
    try {
      await generate.mutateAsync();
      toast.success("GitHub starter kit ready.");
    } catch (err) {
      toast.error(errText(err, "Couldn't generate GitHub content."));
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="brand"
          onClick={run}
          disabled={generate.isPending}
        >
          {generate.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {generated ? "Regenerate GitHub Starter Kit" : "Generate GitHub Starter Kit"}
        </Button>
        <Button size="sm" variant="outline" onClick={onAddLink}>
          I already created one — add link
        </Button>
      </div>

      {generated && <GitHubGeneratedView data={generated} />}
    </div>
  );
}

function GitHubEnhance() {
  const { data: pack } = useCareerPack();
  const [identifier, setIdentifier] = useState(
    pack?.github_username ?? pack?.github_url ?? "",
  );
  const [showReviewForm, setShowReviewForm] = useState(false);
  const review = useReviewGitHub();
  const generate = useGenerateGitHub();
  const generated = pack?.github_generated ?? null;
  const recs = pack?.github_recommendations ?? null;

  async function submitReview() {
    if (!identifier.trim()) {
      toast.error("Enter your GitHub username or profile URL.");
      return;
    }
    try {
      await review.mutateAsync(identifier.trim());
      toast.success("Review ready.");
    } catch (err) {
      toast.error(errText(err, "Couldn't review your GitHub profile."));
    }
  }

  async function runGenerate() {
    try {
      await generate.mutateAsync();
      toast.success("Suggested content ready.");
    } catch (err) {
      toast.error(errText(err, "Couldn't generate GitHub content."));
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="brand"
          onClick={() => setShowReviewForm((v) => !v)}
        >
          Review my GitHub profile
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={runGenerate}
          disabled={generate.isPending}
        >
          {generate.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          Generate profile / project READMEs
        </Button>
      </div>

      {showReviewForm && (
        <div className="space-y-2">
          <Label htmlFor="gh-user" className="text-xs">
            GitHub username or profile URL. We only read public info from
            the GitHub API — no password required.
          </Label>
          <Input
            id="gh-user"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="octocat or https://github.com/octocat"
          />
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowReviewForm(false)}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={submitReview}
              disabled={review.isPending}
            >
              {review.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Review
            </Button>
          </div>
        </div>
      )}

      {recs && <GitHubReviewView data={recs} />}
      {generated && <GitHubGeneratedView data={generated} />}
    </div>
  );
}

function GitHubGeneratedView({ data }: { data: GitHubGenerated }) {
  return (
    <div className="space-y-3 rounded-md border bg-card p-3">
      <div className="flex justify-end">
        <ClearButton side="github" kind="generated" />
      </div>
      {data.username_suggestions.length > 0 && (
        <BulletList
          label="Username suggestions"
          items={data.username_suggestions}
          chip
        />
      )}
      {data.bio && <FieldBlock label="Bio" text={data.bio} />}
      {data.profile_readme && (
        <FieldBlock
          label="Profile README"
          text={data.profile_readme}
          multiline
          mono
        />
      )}
      {data.project_readmes.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Project READMEs
          </p>
          {data.project_readmes.map((r, i) => (
            <ProjectReadmeBlock key={`${r.project_title}-${i}`} readme={r} />
          ))}
        </div>
      )}
      {data.checklist.length > 0 && (
        <BulletList label="Setup checklist" items={data.checklist} />
      )}
    </div>
  );
}

function GitHubReviewView({ data }: { data: GitHubReview }) {
  return (
    <div className="space-y-3 rounded-md border bg-card p-3">
      <div className="flex justify-end">
        <ClearButton side="github" kind="recommendations" />
      </div>
      <p className="text-sm">{data.profile_summary}</p>
      {data.has_profile_readme === false && (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/10 p-2 text-xs">
          No profile README found. Adding one is the single highest-impact
          change you can make.
        </p>
      )}
      {data.suggested_bio && (
        <FieldBlock label="Suggested bio" text={data.suggested_bio} />
      )}
      {data.suggested_profile_readme && (
        <FieldBlock
          label="Suggested profile README"
          text={data.suggested_profile_readme}
          multiline
          mono
        />
      )}
      {data.project_readme_suggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Project README suggestions
          </p>
          {data.project_readme_suggestions.map((r, i) => (
            <ProjectReadmeBlock key={`${r.project_title}-${i}`} readme={r} />
          ))}
        </div>
      )}
      {data.cv_projects_to_add.length > 0 && (
        <BulletList
          label="CV projects to add as repos"
          items={data.cv_projects_to_add}
        />
      )}
      {data.repo_checklist.length > 0 && (
        <BulletList label="Repository improvements" items={data.repo_checklist} />
      )}
    </div>
  );
}

function ProjectReadmeBlock({ readme }: { readme: GitHubProjectReadme }) {
  return (
    <FieldBlock
      label={`${readme.project_title} · ${readme.filename}`}
      text={readme.body}
      multiline
      mono
      subtle
    />
  );
}

// ---- Shared primitives --------------------------------------------------

function FieldBlock({
  label,
  text,
  multiline,
  mono,
  subtle,
}: {
  label: string;
  text: string;
  multiline?: boolean;
  mono?: boolean;
  subtle?: boolean;
}) {
  return (
    <div className={subtle ? "rounded-md bg-muted/40 p-2" : ""}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <CopyButton text={text} />
      </div>
      <p
        className={`mt-1 text-sm ${multiline ? "whitespace-pre-wrap" : ""} ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {text}
      </p>
    </div>
  );
}

function BulletList({
  label,
  items,
  chip,
}: {
  label: string;
  items: string[];
  chip?: boolean;
}) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      {chip ? (
        <div className="mt-1 flex flex-wrap gap-1.5">
          {items.map((s, i) => (
            <Badge key={`${s}-${i}`} variant="secondary">
              {s}
            </Badge>
          ))}
        </div>
      ) : (
        <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">
          {items.map((s, i) => (
            <li key={`${s}-${i}`}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className="h-6 gap-1 px-2 text-xs"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          toast.success("Copied");
        } catch {
          toast.error("Copy failed — select the text manually.");
        }
      }}
    >
      <Copy className="h-3 w-3" />
      Copy
    </Button>
  );
}

function LinkUrlEditor({
  side,
  initial,
  validator,
  placeholder,
  onClose,
}: {
  side: "linkedin" | "github";
  initial: string;
  validator: (v: string) => boolean;
  placeholder: string;
  onClose: () => void;
}) {
  const [value, setValue] = useState(initial);
  const updateProfile = useUpdateStudentProfile();

  async function save() {
    const trimmed = value.trim();
    if (trimmed && !validator(trimmed)) {
      toast.error(
        side === "linkedin"
          ? "That doesn't look like a LinkedIn profile URL."
          : "That doesn't look like a GitHub profile URL.",
      );
      return;
    }
    try {
      await updateProfile.mutateAsync({
        links: { [side]: trimmed || null },
      });
      toast.success(trimmed ? "Link saved." : "Link cleared.");
      onClose();
    } catch {
      toast.error("Couldn't save the link.");
    }
  }

  return (
    <div className="rounded-md border bg-muted/30 p-3">
      <Label htmlFor={`${side}-url`} className="text-xs">
        {side === "linkedin" ? "LinkedIn profile URL" : "GitHub profile URL"}
      </Label>
      <Input
        id={`${side}-url`}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="mt-1"
      />
      <div className="mt-2 flex justify-end gap-2">
        <Button size="sm" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button size="sm" onClick={save} disabled={updateProfile.isPending}>
          {updateProfile.isPending && (
            <Loader2 className="h-4 w-4 animate-spin" />
          )}
          Save
        </Button>
      </div>
    </div>
  );
}

function ClearButton({
  side,
  kind,
  label = "Clear suggestions",
}: {
  side: "linkedin" | "github";
  kind: "generated" | "recommendations";
  label?: string;
}) {
  const clear = useClearCareerPack();

  async function run() {
    try {
      await clear.mutateAsync({ side, kind });
      toast.success("Cleared.");
    } catch {
      toast.error("Couldn't clear.");
    }
  }

  return (
    <Button
      size="sm"
      variant="brand"
      onClick={run}
      disabled={clear.isPending}
    >
      {clear.isPending ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Trash2 className="h-4 w-4" />
      )}
      {label}
    </Button>
  );
}

// ---- errors -------------------------------------------------------------

function errText(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail;
  return typeof detail === "string" && detail ? detail : fallback;
}
