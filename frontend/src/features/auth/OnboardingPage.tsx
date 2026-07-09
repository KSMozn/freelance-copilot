import { ArrowRight, FileUp, Github, SkipForward, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

/**
 * Compact "one thing" onboarding page. The user has just verified their email
 * via OTP — instead of forcing a multi-step wizard, ask them to pick ONE
 * starting source. Whichever they pick (or skip), they land on the dashboard
 * and can add more sources in-context later.
 *
 * The CV-upload and GitHub cards target the professional surface
 * (/sources, /repositories), which is dormant — its routes are not
 * registered, so those cards are shown disabled with a "Coming soon"
 * badge instead of navigating into the wildcard redirect. Re-enable them
 * when the professional surface is mounted again.
 */
export function OnboardingPage() {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-3xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-semibold">Welcome — let&apos;s build your profile.</h1>
          <p className="text-sm text-muted-foreground">
            Pick one thing to start with. You can add the others anytime.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <SourceCard
            icon={<FileUp className="h-6 w-6" />}
            title="Upload your CV"
            description="PDF, DOCX, or paste plain text. We'll extract experiences, skills, and projects into your graph."
            cta="Upload CV"
            badge="Coming soon"
            disabled
          />
          <SourceCard
            icon={<Github className="h-6 w-6" />}
            title="Connect GitHub"
            description="We'll scan your repos for languages, frameworks, and architecture patterns."
            cta="Connect GitHub"
            badge="Coming soon"
            disabled
          />
          <SourceCard
            icon={<SkipForward className="h-6 w-6" />}
            title="Skip for now"
            description="Go straight to the dashboard. Add sources whenever you're ready."
            cta="Continue to dashboard"
            variant="outline"
            onClick={() => navigate("/")}
          />
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              What happens next
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-1">
            <p>
              Whatever you add today becomes part of your <strong>professional knowledge graph</strong> —
              experiences, projects, skills, and certificates that future personas draw from.
            </p>
            <p>
              When you paste your first job, we&apos;ll match it against the graph and generate a
              tailored proposal with evidence chips citing your real work.
            </p>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          <Link to="/" className="hover:underline inline-flex items-center gap-1">
            Skip everything and explore the dashboard <ArrowRight className="h-3 w-3" />
          </Link>
        </p>
      </div>
    </div>
  );
}

interface SourceCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  badge?: string;
  cta?: string;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "default" | "outline";
}

function SourceCard({
  icon,
  title,
  description,
  badge,
  cta,
  onClick,
  disabled,
  variant = "default",
}: SourceCardProps) {
  return (
    <Card className={disabled ? "opacity-60" : ""}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="rounded-lg bg-muted p-2 text-primary">{icon}</div>
          {badge && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
              {badge}
            </span>
          )}
        </div>
        <CardTitle className="text-base mt-3">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {cta && (
          <Button
            variant={variant}
            className="w-full"
            disabled={disabled}
            onClick={onClick}
          >
            {cta}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
