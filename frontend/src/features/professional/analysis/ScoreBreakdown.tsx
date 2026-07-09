import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { SCORE_DIMENSION_LABELS, SCORE_DIMENSION_MAX, type ScoreBreakdown as ScoreBreakdownT } from "@/features/professional/apiTypes";

const ORDER: (keyof ScoreBreakdownT)[] = [
  "technical_fit",
  "domain_fit",
  "proposal_count",
  "budget_attractiveness",
  "client_quality",
  "estimated_effort",
  "risk_level",
  "strategic_value",
];

function Bar({ value, max }: { value: number; max: number }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function ScoreBreakdown({ breakdown }: { breakdown: ScoreBreakdownT }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Score breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {ORDER.map((dim) => {
          const value = breakdown[dim];
          const max = SCORE_DIMENSION_MAX[dim];
          return (
            <div key={dim} className="space-y-1">
              <div className="flex items-baseline justify-between text-sm">
                <span className="text-muted-foreground">{SCORE_DIMENSION_LABELS[dim]}</span>
                <span className="tabular-nums">
                  <span className="font-medium">{value}</span>
                  <span className="text-muted-foreground"> / {max}</span>
                </span>
              </div>
              <Bar value={value} max={max} />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
