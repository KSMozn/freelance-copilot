import { useMemo } from "react";

import { Button } from "@/shared/ui/button";
import { useStudentEntries } from "@/features/student-wizard/studentApi";
import type { StudentEntryKind } from "@/features/student-wizard/studentTypes";

import { EntryForm } from "./EntryForm";
import { EntryRow } from "./EntryRow";

export function StepEntries({
  kind,
  onSaved,
}: {
  kind: StudentEntryKind;
  onSaved: () => Promise<void> | void;
}) {
  const { data: entries = [] } = useStudentEntries();
  const items = useMemo(() => entries.filter((e) => e.kind === kind), [entries, kind]);

  return (
    <div className="space-y-5">
      {items.length > 0 && (
        <div className="space-y-2">
          {items.map((e) => (
            <EntryRow key={e.id} entry={e} kind={kind} />
          ))}
        </div>
      )}

      <EntryForm kind={kind} />

      <div>
        <Button onClick={() => void onSaved()}>Continue</Button>
      </div>
    </div>
  );
}
