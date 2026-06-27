import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function PlaceholderPage({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <Card>
        <CardHeader>
          <CardTitle>Coming in {phase}</CardTitle>
          <CardDescription>
            This screen is reserved in Phase 1. See <code>docs/ROADMAP.md</code> for the full plan.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          The Phase-1 database already contains every table this module will use, so adding the
          backend logic and UI later is a pure additive change — no migrations to backfill.
        </CardContent>
      </Card>
    </div>
  );
}
