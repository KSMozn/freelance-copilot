import { BookOpen, Copy, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { usePortfolioStory } from "@/features/professional/portfolio/portfolioStoryApi";

export function PortfolioStoryCard({
  jobId,
  hasAnalysis,
}: {
  jobId: string | undefined;
  hasAnalysis: boolean;
}) {
  const generate = usePortfolioStory(jobId);
  const isPending = generate.isPending;
  const story = generate.data;

  const run = () =>
    generate.mutate(undefined, {
      onSuccess: (data) => {
        if (data === null) toast.info("No portfolios to pick from yet.");
        else toast.success(`Lead story: ${data.portfolio_title}`);
      },
      onError: (err: unknown) => {
        const detail =
          (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data
            ?.detail ?? "Story generation failed";
        toast.error(detail);
      },
    });

  const copy = (text: string, label: string) => {
    navigator.clipboard
      .writeText(text)
      .then(() => toast.success(`${label} copied`))
      .catch(() => toast.error("Copy failed"));
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <BookOpen className="h-4 w-4 text-primary" />
            Lead with this story
          </CardTitle>
          <CardDescription className="text-xs">
            Best-fit portfolio for this job, with a tailored opener the proposal can quote verbatim.
          </CardDescription>
        </div>
        <Button onClick={run} disabled={!hasAnalysis || isPending} size="sm">
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              Picking…
            </>
          ) : story ? (
            <>
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
              Re-pick
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-3.5 w-3.5" />
              Build story
            </>
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {!hasAnalysis ? (
          <div className="text-sm text-muted-foreground">
            Run <span className="font-medium text-foreground">Analyze job</span> first — picking
            uses the extracted skills + portfolio matches.
          </div>
        ) : !story ? (
          <div className="text-sm text-muted-foreground">
            Click <span className="font-medium text-foreground">Build story</span> to pick the
            strongest portfolio for this job and tailor a lead-with paragraph.
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between gap-2">
              <Link
                to={`/portfolio/${story.portfolio_id}`}
                className="text-sm font-medium hover:underline"
              >
                {story.portfolio_title}
              </Link>
              <div className="flex items-center gap-2">
                {story.business_domain && (
                  <Badge variant="secondary">{story.business_domain}</Badge>
                )}
                <Badge variant="outline">{Math.round(story.match_score * 100)}% match</Badge>
              </div>
            </div>

            <div className="rounded-md border border-primary/30 bg-primary/5 p-3">
              <div className="mb-1 flex items-center justify-between gap-2 text-xs uppercase tracking-wide text-primary">
                <span>Opener</span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 px-2"
                  onClick={() => copy(story.opener, "Opener")}
                >
                  <Copy className="mr-1 h-3 w-3" />
                  Copy
                </Button>
              </div>
              <p className="text-sm italic">“{story.opener}”</p>
            </div>

            <div>
              <div className="mb-1 flex items-center justify-between gap-2 text-xs uppercase tracking-wide text-muted-foreground">
                <span>Body</span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 px-2"
                  onClick={() => copy(story.body, "Body")}
                >
                  <Copy className="mr-1 h-3 w-3" />
                  Copy
                </Button>
              </div>
              <p className="text-sm">{story.body}</p>
            </div>

            <div className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Why this fit:</span>{" "}
              {story.why_this_fit}
            </div>

            {story.relevant_skills.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {story.relevant_skills.slice(0, 8).map((s) => (
                  <Badge key={s} variant="outline" className="text-xs">
                    {s}
                  </Badge>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
