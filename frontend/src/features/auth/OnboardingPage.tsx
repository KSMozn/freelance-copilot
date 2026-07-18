import { ArrowRight, FileDown, GraduationCap, Sparkles, UserRound } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

export function OnboardingPage() {
  const navigate = useNavigate();
  return (
    <div className="h-dvh overflow-y-auto bg-background [scrollbar-gutter:stable]">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="w-full max-w-3xl space-y-6">
          <div className="space-y-2 text-center">
            <h1 className="text-2xl font-semibold">Welcome — let&apos;s build your first CV.</h1>
            <p className="text-sm text-muted-foreground">
              Work through the guided steps in any order. Your profile changes save automatically.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <SourceCard
              icon={<UserRound className="h-6 w-6" />}
              title="Start with the basics"
              description="Add your name, contact details, and location for the CV header."
              cta="Add my details"
              onClick={() => navigate("/student?step=basics")}
            />
            <SourceCard
              icon={<GraduationCap className="h-6 w-6" />}
              title="Add your education"
              description="Capture your university, degree, major, and expected graduation year."
              cta="Add education"
              variant="outline"
              onClick={() => navigate("/student?step=education")}
            />
            <SourceCard
              icon={<FileDown className="h-6 w-6" />}
              title="See the finished result"
              description="Preview the five ATS-friendly designs and export your CV as PDF or DOCX."
              cta="View preview"
              variant="outline"
              onClick={() => navigate("/student?step=preview")}
            />
          </div>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="h-4 w-4 text-primary" />
                What happens next
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1 text-sm text-muted-foreground">
              <p>
                The wizard guides you through education, skills, projects, internships, activities,
                languages, certificates, and a professional summary.
              </p>
              <p>
                Coaching helps strengthen your wording without inventing experience, tools, or
                results you did not provide.
              </p>
            </CardContent>
          </Card>

          <p className="text-center text-xs text-muted-foreground">
            <Link
              to="/student?step=basics"
              className="inline-flex items-center gap-1 hover:underline"
            >
              Start building my CV <ArrowRight className="h-3 w-3" />
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

interface SourceCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  cta?: string;
  onClick?: () => void;
  variant?: "default" | "outline";
}

function SourceCard({
  icon,
  title,
  description,
  cta,
  onClick,
  variant = "default",
}: SourceCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="rounded-lg bg-muted p-2 text-primary">{icon}</div>
        </div>
        <CardTitle className="mt-3 text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {cta && (
          <Button variant={variant} className="w-full" onClick={onClick}>
            {cta}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
