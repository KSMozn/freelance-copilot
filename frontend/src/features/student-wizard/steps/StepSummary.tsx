import { useEffect, useState } from "react";
import { toast } from "sonner";

import { useDraftSummary } from "@/features/student-wizard/coaching/coachingApi";
import {
  useStudentProfile,
  useUpdateStudentProfile,
} from "@/features/student-wizard/studentApi";
import type { StudentLinks } from "@/features/student-wizard/studentTypes";
import { useAutoSave } from "@/shared/hooks/useAutoSave";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";

export function StepSummary({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();
  const draft = useDraftSummary();
  const [headline, setHeadline] = useState(profile?.headline ?? "");
  const [summary, setSummary] = useState(profile?.summary ?? "");
  const [links, setLinks] = useState<StudentLinks>(profile?.links ?? {});
  const [draftedNotes, setDraftedNotes] = useState<string[]>([]);
  const [autoDraftAttempted, setAutoDraftAttempted] = useState(false);

  useEffect(() => {
    if (!profile) return;
    setHeadline((current) => current || profile.headline || "");
    setSummary((current) => current || profile.summary || "");
    setLinks(profile.links ?? {});
  }, [profile?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (autoDraftAttempted) return;
    if (!profile) return;
    if (profile.headline || profile.summary) return;
    setAutoDraftAttempted(true);
    void generateDraft({ silent: true });
  }, [profile?.user_id]);  // eslint-disable-line react-hooks/exhaustive-deps

  useAutoSave({ headline, summary, links }, async ({ headline, summary, links }) => {
    try {
      await update.mutateAsync({
        headline: headline || null,
        summary: summary || null,
        links,
      });
    } catch {
      // silent
    }
  });

  async function generateDraft({ silent }: { silent?: boolean } = {}) {
    const res = await draft.mutateAsync();
    if (!res.ok) {
      setDraftedNotes(res.notes);
      if (!silent) toast.error(res.notes[0] ?? "Coach couldn't draft yet — try again.");
      return;
    }
    setDraftedNotes(res.notes);
    setHeadline(res.headline);
    setSummary(res.summary);
  }

  async function save() {
    await update.mutateAsync({
      headline: headline || null,
      summary: summary || null,
      links,
    });
    await onSaved();
  }

  const drafting = draft.isPending;

  return (
    <div className="space-y-5">
      <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
        <div className="font-medium">Coach draft</div>
        <div className="mt-1 text-xs text-muted-foreground">
          {drafting
            ? "Drafting from your education, skills, projects, and the rest…"
            : "We drafted a starter headline + summary from what you've shared. Edit anything below; nothing is locked in until you continue."}
        </div>
        <div className="mt-2 flex gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => void generateDraft()}
            disabled={drafting}
          >
            {drafting ? "Thinking…" : "Regenerate draft"}
          </Button>
        </div>
        {draftedNotes.length > 0 && (
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
            {draftedNotes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-2">
        <Label>Headline</Label>
        <Input
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder={drafting ? "Drafting…" : "CS undergrad — backend & ML side-projects"}
          disabled={drafting && !headline}
        />
      </div>
      <div className="space-y-2">
        <Label>Summary</Label>
        <Textarea
          rows={6}
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder={drafting ? "Drafting…" : "A short paragraph about who you are and what you care about."}
          disabled={drafting && !summary}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>GitHub URL</Label>
          <Input
            value={links.github ?? ""}
            onChange={(e) => setLinks({ ...links, github: e.target.value || null })}
            placeholder="https://github.com/you"
          />
        </div>
        <div className="space-y-2">
          <Label>LinkedIn URL</Label>
          <Input
            value={links.linkedin ?? ""}
            onChange={(e) => setLinks({ ...links, linkedin: e.target.value || null })}
            placeholder="https://linkedin.com/in/you"
          />
        </div>
        <div className="space-y-2">
          <Label>Personal website</Label>
          <Input
            value={links.website ?? ""}
            onChange={(e) => setLinks({ ...links, website: e.target.value || null })}
          />
        </div>
        <div className="space-y-2">
          <Label>Portfolio URL</Label>
          <Input
            value={links.portfolio ?? ""}
            onChange={(e) => setLinks({ ...links, portfolio: e.target.value || null })}
          />
        </div>
      </div>
      <div>
        <Button onClick={() => void save()} disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}
