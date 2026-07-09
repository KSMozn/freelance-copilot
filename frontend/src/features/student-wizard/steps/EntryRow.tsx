import { useState } from "react";

import { useDeleteStudentEntry } from "@/features/student-wizard/studentApi";
import type { StudentEntry, StudentEntryKind } from "@/features/student-wizard/studentTypes";

import { EntryForm } from "./EntryForm";

export function EntryRow({ entry, kind }: { entry: StudentEntry; kind: StudentEntryKind }) {
  const remove = useDeleteStudentEntry();
  const [editing, setEditing] = useState(false);

  if (editing) {
    return <EntryForm kind={kind} entry={entry} onCancel={() => setEditing(false)} />;
  }

  return (
    <div className="flex items-start justify-between gap-3 rounded-md border bg-muted/20 p-3">
      <div className="min-w-0">
        <div className="font-medium">{entry.title}</div>
        {kind === "language" && entry.details?.proficiency ? (
          <div className="text-xs text-muted-foreground">{String(entry.details.proficiency)}</div>
        ) : kind === "skill" && entry.details?.proficiency ? (
          <div className="text-xs text-muted-foreground">
            Proficiency {String(entry.details.proficiency)}/5
          </div>
        ) : entry.organization ? (
          <div className="text-xs text-muted-foreground">{entry.organization}</div>
        ) : null}
        {entry.description && (
          <div className="mt-1 line-clamp-2 text-sm text-muted-foreground">{entry.description}</div>
        )}
        {kind === "project" && Array.isArray(entry.details?.tech_stack) && (
          <div className="mt-1 flex flex-wrap gap-1">
            {(entry.details.tech_stack as unknown[]).map((t, i) => (
              <span
                key={i}
                className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] text-muted-foreground"
              >
                {String(t)}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="text-xs text-muted-foreground hover:text-primary"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => void remove.mutateAsync(entry.id)}
          className="text-xs text-muted-foreground hover:text-destructive"
        >
          Remove
        </button>
      </div>
    </div>
  );
}
