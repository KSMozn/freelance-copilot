import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { useProofread } from "@/features/student-wizard/coaching/coachingApi";
import type { ProofreadFix } from "@/features/student-wizard/coaching/coachingTypes";
import { PostDownloadSurvey } from "@/features/student-wizard/feedback/PostDownloadSurvey";
import {
  downloadStudentCv,
  downloadStudentCvDocx,
  fetchCvPreviewHtml,
  useCvTemplates,
  useStudentEntries,
  useStudentProfile,
  useUpdateStudentEntry,
  useUpdateStudentProfile,
} from "@/features/student-wizard/studentApi";
import type { StudentProfileUpdate } from "@/features/student-wizard/studentTypes";
import { AboutFooter } from "@/shared/ui/brand/AboutFooter";
import { Button } from "@/shared/ui/button";

export function StepPreview() {
  const { data: profile } = useStudentProfile();
  const { data: entries = [] } = useStudentEntries();
  const { data: templatesResp } = useCvTemplates();
  const updateProfile = useUpdateStudentProfile();
  const updateEntry = useUpdateStudentEntry();
  const proofread = useProofread();
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // null when idle; "pdf" or "docx" while that format is being built.
  // A single field so the menu can label just the clicked row.
  const [downloadingFormat, setDownloadingFormat] = useState<"pdf" | "docx" | null>(null);
  // Currently previewed template slug. Not necessarily saved — user
  // must click "Set as default" to persist the choice.
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  // Flipped true after a successful download; drives the survey card.
  // Local state only — refreshing the page hides the card, and it
  // returns on the next successful download.
  const [showSurvey, setShowSurvey] = useState(false);
  // Fixes returned by the coach that the student hasn't acted on yet.
  const [fixes, setFixes] = useState<ProofreadFix[]>([]);
  const [proofreadNotes, setProofreadNotes] = useState<string[]>([]);
  // Track which fix is currently being applied so we can disable its
  // button without re-rendering the whole list unnecessarily.
  const [applyingIndex, setApplyingIndex] = useState<number | null>(null);

  // Seed selection from profile → template list default. Runs whenever
  // the templates list resolves — first render just sees `null`.
  useEffect(() => {
    if (selectedSlug) return;
    const seed =
      profile?.cv_template_slug ??
      templatesResp?.default_slug ??
      templatesResp?.items[0]?.slug ??
      null;
    if (seed) setSelectedSlug(seed);
  }, [profile?.cv_template_slug, templatesResp, selectedSlug]);

  async function loadPreview(slug: string | null = selectedSlug) {
    setLoading(true);
    try {
      const h = await fetchCvPreviewHtml(slug ?? undefined);
      setHtml(h);
    } catch {
      toast.error("Could not load preview");
    } finally {
      setLoading(false);
    }
  }

  // Reload preview when the picked template changes.
  useEffect(() => {
    if (selectedSlug) void loadPreview(selectedSlug);
  }, [selectedSlug]); // eslint-disable-line react-hooks/exhaustive-deps

  const savedSlug = profile?.cv_template_slug ?? templatesResp?.default_slug ?? null;
  const canSaveAsDefault = !!selectedSlug && selectedSlug !== profile?.cv_template_slug;

  async function saveAsDefault() {
    if (!selectedSlug) return;
    try {
      await updateProfile.mutateAsync({ cv_template_slug: selectedSlug });
      toast.success("Saved — this is now your default template.");
    } catch {
      toast.error("Couldn't save your default template.");
    }
  }

  async function download(format: "pdf" | "docx") {
    setDownloadingFormat(format);
    try {
      const blob =
        format === "pdf"
          ? await downloadStudentCv(selectedSlug ?? undefined)
          : await downloadStudentCvDocx(selectedSlug ?? undefined);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const fname = (profile?.full_name ?? "cv").replace(/\s+/g, "_");
      a.download = format === "pdf" ? `${fname}.pdf` : `${fname}_CV.docx`;
      a.click();
      URL.revokeObjectURL(url);
      // Prompt for a rating right after a successful download.
      setShowSurvey(true);
    } catch (err) {
      const status = (err as { response?: { status?: number } } | undefined)?.response?.status;
      if (format === "pdf" && status === 503) {
        toast.error(
          "PDF renderer isn't installed in this environment. Rebuild the backend image to install WeasyPrint system deps.",
        );
      } else {
        toast.error(format === "pdf" ? "Could not download PDF" : "Could not download DOCX");
      }
    } finally {
      setDownloadingFormat(null);
    }
  }

  async function runProofread() {
    const res = await proofread.mutateAsync();
    setProofreadNotes(res.notes);
    setFixes(res.fixes);
    if (res.ok && res.fixes.length === 0) {
      toast.success("Looks good — no fixes to suggest.");
    }
    if (!res.ok && res.notes.length > 0) {
      toast.error(res.notes[0]);
    }
  }

  async function applyFix(fix: ProofreadFix, i: number) {
    setApplyingIndex(i);
    try {
      if (fix.entity_kind === "profile") {
        const patch: StudentProfileUpdate =
          fix.field === "summary" ? { summary: fix.suggested } : { headline: fix.suggested };
        await updateProfile.mutateAsync(patch);
      } else if (fix.entity_kind === "entry" && fix.entity_id) {
        const entry = entries.find((e) => e.id === fix.entity_id);
        if (!entry) {
          toast.error("That entry no longer exists — skipped.");
          setFixes((prev) => prev.filter((_, idx) => idx !== i));
          return;
        }
        const nextTitle = fix.field === "title" ? fix.suggested : entry.title;
        const nextDesc = fix.field === "description" ? fix.suggested : entry.description;
        await updateEntry.mutateAsync({
          id: entry.id,
          payload: {
            kind: entry.kind,
            title: nextTitle,
            organization: entry.organization,
            start_date: entry.start_date,
            end_date: entry.end_date,
            is_current: entry.is_current,
            description: nextDesc,
            url: entry.url,
            details: entry.details,
            sort_order: entry.sort_order,
          },
        });
      }
      setFixes((prev) => prev.filter((_, idx) => idx !== i));
      // Refresh the preview so the student sees the improvement immediately.
      void loadPreview();
    } catch {
      toast.error("Couldn't apply that one — try again.");
    } finally {
      setApplyingIndex(null);
    }
  }

  function ignoreFix(i: number) {
    setFixes((prev) => prev.filter((_, idx) => idx !== i));
  }

  const templates = templatesResp?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <p className="flex-1 text-sm text-muted-foreground">
          This is what recruiters will see. Give it one last polish, then download.
        </p>
        <Button
          type="button"
          variant="outline"
          onClick={() => void runProofread()}
          disabled={proofread.isPending}
        >
          {proofread.isPending ? "Proofreading…" : "Proofread with AI"}
        </Button>
        <DownloadCvMenu busyFormat={downloadingFormat} onDownload={(fmt) => void download(fmt)} />
      </div>

      {templates.length > 1 && (
        <div className="space-y-3 rounded-2xl border border-border/60 bg-muted/20 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-medium">Template</div>
              <div className="text-xs text-muted-foreground">
                Click any style to preview it. Set as default to save your choice — Download uses
                whatever is showing.
              </div>
            </div>
            {canSaveAsDefault && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void saveAsDefault()}
                disabled={updateProfile.isPending}
              >
                {updateProfile.isPending ? "Saving…" : "Set as default"}
              </Button>
            )}
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {templates.map((t) => {
              const active = selectedSlug === t.slug;
              const isSaved = savedSlug === t.slug;
              return (
                <button
                  key={t.slug}
                  type="button"
                  onClick={() => setSelectedSlug(t.slug)}
                  className={`group relative min-w-[200px] flex-shrink-0 overflow-hidden rounded-xl border p-3 text-left transition-all ${
                    active
                      ? "border-transparent bg-background shadow-md ring-2 ring-primary/60"
                      : "border-border/70 bg-background hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-sm"
                  }`}
                >
                  {active && (
                    <span
                      aria-hidden
                      className="bg-brand-gradient pointer-events-none absolute inset-x-0 top-0 h-0.5"
                    />
                  )}
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold tracking-tight">{t.display_name}</div>
                    {isSaved && (
                      <span className="bg-brand-gradient rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                        Default
                      </span>
                    )}
                  </div>
                  <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                    {t.description}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {(fixes.length > 0 || proofreadNotes.length > 0) && (
        <div className="space-y-2 rounded-md border border-primary/30 bg-primary/5 p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">
              Coach found {fixes.length} suggestion{fixes.length === 1 ? "" : "s"}
            </div>
            {fixes.length > 0 && (
              <button
                type="button"
                className="text-xs text-muted-foreground hover:text-foreground"
                onClick={() => setFixes([])}
              >
                Dismiss all
              </button>
            )}
          </div>
          {proofreadNotes.map((n, i) => (
            <div key={i} className="text-xs text-muted-foreground">
              {n}
            </div>
          ))}
          <div className="space-y-2">
            {fixes.map((fix, i) => (
              <FixCard
                key={i}
                fix={fix}
                applying={applyingIndex === i}
                onApply={() => void applyFix(fix, i)}
                onIgnore={() => ignoreFix(i)}
              />
            ))}
          </div>
        </div>
      )}

      {showSurvey && (
        <PostDownloadSurvey templateSlug={selectedSlug} onDismiss={() => setShowSurvey(false)} />
      )}

      <div className="overflow-hidden rounded-2xl border border-border/40 bg-white shadow-xl">
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading…</div>
        ) : html ? (
          <iframe
            title="CV preview"
            srcDoc={html}
            className="h-[900px] w-full"
            sandbox="allow-same-origin"
          />
        ) : (
          <div className="p-8 text-center text-sm text-muted-foreground">No preview</div>
        )}
      </div>

      <AboutFooter className="pt-2" />
    </div>
  );
}

function DownloadCvMenu({
  busyFormat,
  onDownload,
}: {
  busyFormat: "pdf" | "docx" | null;
  onDownload: (format: "pdf" | "docx") => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  // Click-outside closes the menu — same pattern as Combobox.
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const busy = busyFormat !== null;
  const label = busy
    ? busyFormat === "pdf"
      ? "Preparing PDF…"
      : "Preparing DOCX…"
    : "Download CV";

  return (
    <div ref={rootRef} className="relative">
      <Button
        variant="brand"
        size="lg"
        onClick={() => setOpen((o) => !o)}
        disabled={busy}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {label}{" "}
        {!busy && (
          <span aria-hidden className="ml-1">
            ▾
          </span>
        )}
      </Button>
      {open && !busy && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-1 w-56 overflow-hidden rounded-md border bg-card text-card-foreground shadow-lg"
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onDownload("pdf");
            }}
            className="block w-full px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
          >
            <div className="font-medium">PDF</div>
            <div className="text-xs text-muted-foreground">Final, print-ready</div>
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onDownload("docx");
            }}
            className="block w-full border-t border-border/60 px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
          >
            <div className="font-medium">DOCX</div>
            <div className="text-xs text-muted-foreground">Editable in Word or Google Docs</div>
          </button>
        </div>
      )}
    </div>
  );
}

function FixCard({
  fix,
  applying,
  onApply,
  onIgnore,
}: {
  fix: ProofreadFix;
  applying: boolean;
  onApply: () => void;
  onIgnore: () => void;
}) {
  const badge = CATEGORY_BADGE[fix.category];
  const where = LOCATION_LABEL[fix.field] + (fix.entity_kind === "entry" ? " (entry)" : "");
  return (
    <div className="rounded-md border bg-background p-3 text-sm">
      <div className="mb-1 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={
              "rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide " +
              badge.className
            }
          >
            {badge.label}
          </span>
          <span className="text-xs text-muted-foreground">{where}</span>
        </div>
        <div className="flex gap-1">
          <Button size="sm" onClick={onApply} disabled={applying}>
            {applying ? "…" : "Apply"}
          </Button>
          <Button size="sm" variant="ghost" onClick={onIgnore} disabled={applying}>
            Ignore
          </Button>
        </div>
      </div>
      <div className="text-xs text-muted-foreground">{fix.reason}</div>
      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Original</div>
          <div className="mt-0.5 whitespace-pre-wrap rounded bg-destructive/5 p-2 text-xs">
            {fix.original}
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Suggested</div>
          <div className="mt-0.5 whitespace-pre-wrap rounded bg-primary/5 p-2 text-xs">
            {fix.suggested}
          </div>
        </div>
      </div>
    </div>
  );
}

const CATEGORY_BADGE: Record<ProofreadFix["category"], { label: string; className: string }> = {
  typo: { label: "Typo", className: "bg-destructive/10 text-destructive" },
  grammar: { label: "Grammar", className: "bg-amber-500/10 text-amber-600" },
  clarity: { label: "Clarity", className: "bg-primary/10 text-primary" },
  style: { label: "Style", className: "bg-muted text-foreground" },
};

const LOCATION_LABEL: Record<ProofreadFix["field"], string> = {
  summary: "Summary",
  headline: "Headline",
  description: "Description",
  title: "Title",
};
