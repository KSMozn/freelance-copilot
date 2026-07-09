import { Card, CardContent } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";
import type { OpportunityScore, Recommendation } from "@/features/professional/apiTypes";

const REC_STYLES: Record<Recommendation, string> = {
  "Strong Apply": "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  Apply: "bg-blue-500/15 text-blue-400 ring-blue-500/30",
  Maybe: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
  Skip: "bg-rose-500/15 text-rose-400 ring-rose-500/30",
};

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 65) return "text-blue-400";
  if (score >= 50) return "text-amber-400";
  return "text-rose-400";
}

export function ScoreCard({ score }: { score: OpportunityScore }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 p-6 md:flex-row md:items-center">
        <div className="flex items-baseline gap-2">
          <div className={cn("text-6xl font-semibold tabular-nums leading-none", scoreColor(score.score))}>
            {score.score}
          </div>
          <div className="text-sm text-muted-foreground">/ 100</div>
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "rounded-full px-2.5 py-1 text-xs font-semibold ring-1",
                REC_STYLES[score.recommendation],
              )}
            >
              {score.recommendation}
            </span>
            <span className="text-xs text-muted-foreground">
              confidence: {score.confidence}
            </span>
            <span className="text-xs text-muted-foreground">
              profile: {score.profile_version}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">{score.reasoning}</p>
        </div>
      </CardContent>
    </Card>
  );
}
