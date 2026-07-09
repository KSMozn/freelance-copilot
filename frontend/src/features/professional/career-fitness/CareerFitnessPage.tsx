import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Github,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import {
  useCareerFitness,
  type CareerFitness,
  type MarketSkill,
  type SkillGap,
} from "@/features/professional/career-fitness/careerFitnessApi";

export function CareerFitnessPage() {
  const { data, isLoading, isError } = useCareerFitness();

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Computing market signals…</p>;
  }
  if (isError || !data) {
    return (
      <p className="text-sm text-muted-foreground">
        Could not load career fitness — analyze a few jobs first.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Career Fitness</h1>
        <p className="text-sm text-muted-foreground">
          Computed from your {data.total_jobs_analyzed} analyzed job
          {data.total_jobs_analyzed === 1 ? "" : "s"} and{" "}
          {data.total_applications} application
          {data.total_applications === 1 ? "" : "s"}. Refreshes whenever you
          analyze a new posting.
        </p>
      </header>

      <TopGapsCard data={data} />

      <div className="grid gap-4 lg:grid-cols-2">
        <MarketSkillsCard data={data} />
        <FeedbackCard data={data} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <RecurringGapsCard data={data} />
        <DomainDemandCard data={data} />
      </div>

      <RepoSuggestionsCard data={data} />
    </div>
  );
}

// ---- Cards ---------------------------------------------------------------

function TopGapsCard({ data }: { data: CareerFitness }) {
  if (data.top_gaps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            No critical gaps
          </CardTitle>
          <CardDescription>
            Every skill the market is asking for is already in your pot at
            proficiency 3 or higher.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Top gaps — skills the market wants
        </CardTitle>
        <CardDescription>
          Severity scales with how often the market asks for each skill and
          how present (or absent) it is in your pot.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {data.top_gaps.map((gap) => (
          <GapRow key={gap.name} gap={gap} />
        ))}
      </CardContent>
    </Card>
  );
}

function GapRow({ gap }: { gap: SkillGap }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm py-1 border-b last:border-b-0">
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{gap.name}</p>
        <p className="text-xs text-muted-foreground">
          market demand {gap.market_count.toFixed(1)}
          {gap.current_proficiency != null
            ? ` · you're at proficiency ${gap.current_proficiency}`
            : " · not in your pot"}
        </p>
      </div>
      <SeverityChip severity={gap.severity} />
    </div>
  );
}

function SeverityChip({ severity }: { severity: number }) {
  const palette = [
    "bg-muted text-muted-foreground",
    "bg-amber-500/10 text-amber-700 dark:text-amber-300",
    "bg-amber-500/20 text-amber-700 dark:text-amber-300",
    "bg-destructive/10 text-destructive",
    "bg-destructive/20 text-destructive",
  ];
  const idx = Math.max(0, Math.min(4, severity - 1));
  return (
    <span
      className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full ${palette[idx]}`}
    >
      Severity {severity}
    </span>
  );
}

function MarketSkillsCard({ data }: { data: CareerFitness }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          Market demand
        </CardTitle>
        <CardDescription>
          Top skills across your analyzed jobs, weighted (required 1.0,
          preferred 0.5).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        {data.market_skills.slice(0, 12).map((m) => (
          <MarketSkillRow key={m.name} m={m} />
        ))}
      </CardContent>
    </Card>
  );
}

function MarketSkillRow({ m }: { m: MarketSkill }) {
  return (
    <div className="flex items-center justify-between text-sm py-1">
      <div className="flex-1 min-w-0 flex items-center gap-2">
        <span className={m.in_your_pot ? "" : "text-muted-foreground"}>
          {m.name}
        </span>
        {m.in_your_pot && m.your_proficiency != null && (
          <Badge variant="outline" className="text-[10px]">
            P{m.your_proficiency}
          </Badge>
        )}
        {!m.in_your_pot && (
          <Badge variant="outline" className="text-[10px] text-destructive">
            missing
          </Badge>
        )}
      </div>
      <div className="text-xs text-muted-foreground tabular-nums">
        {m.market_count.toFixed(1)}
      </div>
    </div>
  );
}

function FeedbackCard({ data }: { data: CareerFitness }) {
  const positive = data.feedback.filter((f) => f.score > 0).slice(0, 8);
  const negative = data.feedback.filter((f) => f.score < 0).slice(0, 5);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <ThumbsUp className="h-4 w-4 text-emerald-500" />
          Application feedback
        </CardTitle>
        <CardDescription>
          Weighted by outcome — won/completed = +3, interview = +1,
          rejected/withdrawn = -1.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {positive.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
              Pulls you in
            </p>
            {positive.map((f) => (
              <div key={f.name} className="flex justify-between text-sm py-0.5">
                <span>{f.name}</span>
                <span className="text-emerald-600 dark:text-emerald-400 tabular-nums">
                  +{f.score}
                </span>
              </div>
            ))}
          </div>
        )}
        {negative.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1 flex items-center gap-1">
              <ThumbsDown className="h-3 w-3" />
              Cooler signals
            </p>
            {negative.map((f) => (
              <div key={f.name} className="flex justify-between text-sm py-0.5">
                <span className="text-muted-foreground">{f.name}</span>
                <span className="text-destructive tabular-nums">{f.score}</span>
              </div>
            ))}
          </div>
        )}
        {positive.length === 0 && negative.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No application outcomes yet — feedback shows up once you mark
            applications as won, interview, or lost.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function RecurringGapsCard({ data }: { data: CareerFitness }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingDown className="h-4 w-4 text-amber-500" />
          Recurring critical gaps
        </CardTitle>
        <CardDescription>
          Skills your match reports keep flagging as critical and missing.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        {data.recurring_gaps.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No recurring gaps — your match reports look clean.
          </p>
        )}
        {data.recurring_gaps.slice(0, 8).map((r) => (
          <div key={r.name} className="flex justify-between items-center text-sm py-0.5">
            <span>{r.name}</span>
            <span className="text-xs text-muted-foreground">
              flagged {r.count}× · avg importance {r.avg_importance.toFixed(1)}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DomainDemandCard({ data }: { data: CareerFitness }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-primary" />
          Business domain demand
        </CardTitle>
        <CardDescription>Where your analyzed jobs cluster.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        {data.domain_demand.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No business domain signal yet.
          </p>
        )}
        {data.domain_demand.slice(0, 8).map(([name, count]) => (
          <div key={name} className="flex justify-between text-sm py-0.5">
            <span>{name}</span>
            <span className="text-xs text-muted-foreground tabular-nums">
              {count}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function RepoSuggestionsCard({ data }: { data: CareerFitness }) {
  if (data.repo_suggestions.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Github className="h-4 w-4 text-primary" />
          GitHub README suggestions
        </CardTitle>
        <CardDescription>
          Repos that already demonstrate in-demand skills but whose READMEs
          don't call them out clearly.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.repo_suggestions.map((s) => (
          <div key={s.repository_id} className="rounded-md border bg-muted/30 p-3 space-y-2">
            <p className="text-sm font-medium">{s.repository_name}</p>
            <p className="text-sm">{s.suggestion}</p>
            {s.skills_covered.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {s.skills_covered.map((sk) => (
                  <Badge key={sk} variant="outline" className="text-[10px] gap-1">
                    <Sparkles className="h-2.5 w-2.5" />
                    {sk}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
