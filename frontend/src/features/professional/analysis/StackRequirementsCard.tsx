import { Layers } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  STACK_CATEGORY_LABELS,
  STACK_CATEGORY_ORDER,
  type JobAnalysis,
  type StackCategory,
  type StackRequirement,
} from "@/features/professional/apiTypes";

function Stars({ importance }: { importance: number }) {
  return (
    <span className="font-mono text-xs tabular-nums" aria-label={`${importance} of 5`}>
      <span className="text-primary">{"★".repeat(importance)}</span>
      <span className="text-muted-foreground/40">{"★".repeat(5 - importance)}</span>
    </span>
  );
}

function groupByCategory(items: StackRequirement[]): Map<StackCategory, StackRequirement[]> {
  const map = new Map<StackCategory, StackRequirement[]>();
  for (const item of items) {
    const list = map.get(item.category) ?? [];
    list.push(item);
    map.set(item.category, list);
  }
  for (const list of map.values()) {
    list.sort((a, b) => b.importance - a.importance);
  }
  return map;
}

export function StackRequirementsCard({ analysis }: { analysis: JobAnalysis }) {
  const items = analysis.stack_requirements ?? [];
  if (!items.length) return null;

  const grouped = groupByCategory(items);
  const orderedCategories = STACK_CATEGORY_ORDER.filter((c) => grouped.has(c));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Layers className="h-4 w-4 text-primary" />
          Stack requirements
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          {orderedCategories.map((category) => {
            const rows = grouped.get(category) ?? [];
            return (
              <div key={category}>
                <div className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  {STACK_CATEGORY_LABELS[category]}
                </div>
                <ul className="space-y-1">
                  {rows.map((row) => (
                    <li
                      key={`${row.category}:${row.name}`}
                      className="flex items-center justify-between gap-3 text-sm"
                    >
                      <span className="truncate text-foreground">{row.name}</span>
                      <Stars importance={row.importance} />
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
