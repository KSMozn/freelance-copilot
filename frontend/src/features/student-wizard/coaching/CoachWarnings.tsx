import type { CoachSuggestion, CoachWarning } from "@/features/student-wizard/coaching/coachingTypes";

export function CoachWarnings({
  warnings,
  suggestions,
  onApplySuggestion,
}: {
  warnings: CoachWarning[];
  suggestions?: CoachSuggestion[];
  onApplySuggestion?: (value: string) => void;
}) {
  if (warnings.length === 0 && (!suggestions || suggestions.length === 0)) return null;
  return (
    <div className="space-y-2 rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-sm">
      {warnings.map((w, i) => (
        <div
          key={`${w.code}-${i}`}
          className={
            "flex items-start gap-2 " +
            (w.severity === "block"
              ? "text-destructive"
              : w.severity === "info"
                ? "text-muted-foreground"
                : "text-amber-600 dark:text-amber-400")
          }
        >
          <span aria-hidden>!</span>
          <span>{w.message}</span>
        </div>
      ))}
      {suggestions && suggestions.length > 0 && (
        <div className="border-t border-amber-500/30 pt-2">
          <div className="mb-1 text-xs font-medium text-muted-foreground">Try one of these:</div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => onApplySuggestion?.(s.value)}
                className="rounded-md border border-border bg-background px-2 py-1 text-xs hover:bg-muted"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
