import { useMemo, useState } from "react";

import { useDeleteStudentEntry, useStudentEntries } from "@/features/student-wizard/studentApi";
import { INTERNSHIP_WORK_MODES } from "@/features/student-wizard/studentSuggestions";
import type {
  InternshipDetails,
  InternshipWorkMode,
  StudentEntry,
} from "@/features/student-wizard/studentTypes";
import { Button } from "@/shared/ui/button";

import { InternshipCard } from "./InternshipCard";

export function StepInternships({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: entries = [] } = useStudentEntries();
  const items = useMemo(() => entries.filter((e) => e.kind === "internship"), [entries]);
  const [adding, setAdding] = useState(false);

  return (
    <div className="space-y-5">
      {items.length === 0 && !adding && (
        <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
          Internships are optional. If you don't have one yet, skip this section — your projects,
          skills, and education can still make your CV strong.
        </div>
      )}

      {items.length > 0 && (
        <div className="space-y-3">
          {items.map((e) => (
            <InternshipRow key={e.id} entry={e} />
          ))}
        </div>
      )}

      {adding ? (
        <InternshipCard onDone={() => setAdding(false)} />
      ) : (
        <Button type="button" variant="outline" onClick={() => setAdding(true)}>
          + Add internship
        </Button>
      )}

      <div>
        <Button onClick={() => void onSaved()}>Continue</Button>
      </div>
    </div>
  );
}

function InternshipRow({ entry }: { entry: StudentEntry }) {
  const [editing, setEditing] = useState(false);
  const remove = useDeleteStudentEntry();
  const details = (entry.details ?? {}) as InternshipDetails;
  const aiBullets = details.ai_bullets ?? [];

  if (editing) {
    return <InternshipCard entry={entry} onDone={() => setEditing(false)} />;
  }

  const dates = _fmtRange(entry.start_date, entry.end_date, entry.is_current);

  return (
    <div className="rounded-lg border bg-muted/10 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-medium">{entry.title}</div>
          <div className="text-xs text-muted-foreground">
            {entry.organization}
            {dates ? ` · ${dates}` : ""}
            {details.work_mode ? ` · ${_workModeLabel(details.work_mode)}` : ""}
          </div>
        </div>
        <div className="flex gap-2">
          <Button type="button" size="sm" variant="outline" onClick={() => setEditing(true)}>
            Edit
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => {
              if (confirm("Remove this internship?")) {
                void remove.mutateAsync(entry.id);
              }
            }}
          >
            Delete
          </Button>
        </div>
      </div>
      {details.ai_summary && (
        <div className="mt-2 text-sm italic text-muted-foreground">{details.ai_summary}</div>
      )}
      {aiBullets.length > 0 && (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-foreground">
          {aiBullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function _fmtRange(start: string | null, end: string | null, isCurrent: boolean): string {
  if (!start && !end && !isCurrent) return "";
  const s = start ?? "";
  const e = isCurrent ? "Present" : (end ?? "");
  if (s && e) return `${s} – ${e}`;
  return s || e;
}

function _workModeLabel(mode: InternshipWorkMode): string {
  const found = INTERNSHIP_WORK_MODES.find((m) => m.value === mode);
  return found?.label ?? mode;
}
