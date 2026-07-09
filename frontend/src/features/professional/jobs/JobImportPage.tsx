import { ArrowLeft, Image as ImageIcon, Loader2, MonitorUp, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useImportJobFromImage } from "@/features/professional/jobs/jobImportApi";
import { cn } from "@/shared/lib/utils";
import type { JobImportPreview } from "@/features/professional/apiTypes";

const ACCEPTED = "image/png,image/jpeg,image/jpg,image/webp";
const MAX_BYTES = 10 * 1024 * 1024;

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

/** Grab a single frame from a screen / window / tab the user picks.
 *
 * Uses `getDisplayMedia` — Chromium / Firefox / Safari support it. Returns
 * null on cancel or unsupported environments; the caller toasts on error.
 */
async function captureFromScreen(): Promise<File | null> {
  const md = navigator.mediaDevices as
    | (MediaDevices & { getDisplayMedia?: (c?: unknown) => Promise<MediaStream> })
    | undefined;
  if (!md?.getDisplayMedia) {
    toast.error("Screen capture isn't supported in this browser.");
    return null;
  }
  let stream: MediaStream | null = null;
  try {
    stream = await md.getDisplayMedia({
      video: { displaySurface: "browser" },
      audio: false,
    });
  } catch (err) {
    const name = (err as { name?: string } | null)?.name;
    if (name && name !== "AbortError" && name !== "NotAllowedError") {
      toast.error("Could not start screen capture.");
    }
    return null;
  }

  try {
    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.srcObject = stream;
    await video.play();
    // Wait until the video has real dimensions
    await new Promise<void>((resolve) => {
      if (video.videoWidth > 0) return resolve();
      video.addEventListener("loadedmetadata", () => resolve(), { once: true });
    });
    // Yield one animation frame so the first painted frame is captured
    await new Promise((r) => requestAnimationFrame(() => r(null)));

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      toast.error("Could not draw the captured frame.");
      return null;
    }
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((b) => resolve(b), "image/png", 1),
    );
    if (!blob) {
      toast.error("Could not encode the captured frame.");
      return null;
    }
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    return new File([blob], `upwork-capture-${stamp}.png`, { type: "image/png" });
  } finally {
    stream.getTracks().forEach((t) => t.stop());
  }
}

function PreviewPanel({ preview }: { preview: JobImportPreview }) {
  const empty =
    !preview.project_duration &&
    !preview.project_type &&
    !preview.experience_level &&
    !preview.location &&
    !preview.posted_at &&
    preview.mandatory_skills.length === 0 &&
    preview.nice_to_have_skills.length === 0 &&
    preview.questions.length === 0;

  if (empty) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Extracted fields</CardTitle>
        <CardDescription>
          What the AI pulled from the screenshot. The Job Detail page now has the full
          description with everything folded in.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Field label="Project type" value={preview.project_type} />
          <Field label="Duration" value={preview.project_duration} />
          <Field label="Experience" value={preview.experience_level} />
          <Field label="Location" value={preview.location} />
          <Field label="Posted" value={preview.posted_at} />
        </div>
        {preview.mandatory_skills.length > 0 && (
          <div>
            <div className="mb-1 text-xs uppercase tracking-wider text-muted-foreground">
              Mandatory skills
            </div>
            <div className="flex flex-wrap gap-1.5">
              {preview.mandatory_skills.map((s) => (
                <Badge key={s}>{s}</Badge>
              ))}
            </div>
          </div>
        )}
        {preview.nice_to_have_skills.length > 0 && (
          <div>
            <div className="mb-1 text-xs uppercase tracking-wider text-muted-foreground">
              Nice-to-have skills
            </div>
            <div className="flex flex-wrap gap-1.5">
              {preview.nice_to_have_skills.map((s) => (
                <Badge key={s} variant="outline">
                  {s}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {preview.questions.length > 0 && (
          <div>
            <div className="mb-1 text-xs uppercase tracking-wider text-muted-foreground">
              Pre-application questions
            </div>
            <ol className="list-decimal space-y-1 pl-5">
              {preview.questions.map((q) => (
                <li key={q}>{q}</li>
              ))}
            </ol>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="text-sm">{value || "—"}</div>
    </div>
  );
}

export function JobImportPage() {
  const navigate = useNavigate();
  const importMutation = useImportJobFromImage();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [sourceUrl, setSourceUrl] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleFile = (f: File | null | undefined) => {
    if (!f) return;
    if (f.size > MAX_BYTES) {
      toast.error(`Image is ${formatBytes(f.size)}, max is 10 MB`);
      return;
    }
    if (!ACCEPTED.split(",").includes(f.type) && !f.type.startsWith("image/")) {
      toast.error(`Unsupported file type ${f.type || "(unknown)"}`);
      return;
    }
    setFile(f);
  };

  // Cmd/Ctrl+V anywhere on the page → adopt the clipboard image
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const item = Array.from(e.clipboardData?.items ?? []).find((i) =>
        i.type.startsWith("image/"),
      );
      if (!item) return;
      const blob = item.getAsFile();
      if (blob) {
        e.preventDefault();
        handleFile(blob);
        toast.success("Pasted screenshot from clipboard");
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, []);

  const [capturing, setCapturing] = useState(false);
  const onCapture = async () => {
    setCapturing(true);
    try {
      const captured = await captureFromScreen();
      if (captured) {
        handleFile(captured);
        toast.success(`Captured ${formatBytes(captured.size)} from screen`);
      }
    } finally {
      setCapturing(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error(
        "Upload a screenshot first — pasting only the Upwork URL isn't enough (the platform never scrapes Upwork).",
      );
      // Pull the dropzone back into view so the user can act on the message.
      inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    importMutation.mutate(
      { file, sourceUrl: sourceUrl.trim() || undefined },
      {
        onSuccess: (data) => {
          toast.success(`Imported "${data.job.title.slice(0, 40)}"`);
          navigate(`/jobs/${data.job.id}`, { state: { import: data.preview } });
        },
        onError: (err: unknown) => {
          const detail =
            (err as { response?: { data?: { detail?: string } } } | undefined)?.response
              ?.data?.detail ?? "Could not import the screenshot";
          toast.error(detail);
        },
      },
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <Link
          to="/jobs"
          className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Jobs
        </Link>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Import a job from a screenshot
        </h1>
        <p className="text-sm text-muted-foreground">
          Upload an Upwork job-post screenshot. The AI extracts title, summary, budget,
          skills, and questions, then creates the job for you. Image is sent to the
          configured AI provider; with <code>AI_PROVIDER=mock</code> a clearly-labeled
          placeholder is returned instead.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <Card>
          <CardContent className="space-y-3 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-muted/40 p-3">
              <div className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Three ways to attach a screenshot:</span>{" "}
                drop a file below, capture without leaving the page, or paste from the clipboard
                with <kbd className="rounded border border-border/70 px-1 py-0.5 text-[10px]">⌘ V</kbd> /{" "}
                <kbd className="rounded border border-border/70 px-1 py-0.5 text-[10px]">Ctrl V</kbd>.
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={onCapture}
                disabled={capturing}
              >
                {capturing ? (
                  <>
                    <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                    Capturing…
                  </>
                ) : (
                  <>
                    <MonitorUp className="mr-2 h-3.5 w-3.5" />
                    Capture from screen
                  </>
                )}
              </Button>
            </div>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                handleFile(e.dataTransfer.files?.[0]);
              }}
              onClick={() => inputRef.current?.click()}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed p-8 text-center transition-colors",
                dragOver
                  ? "border-primary bg-primary/5"
                  : "border-border/70 hover:border-primary/40",
              )}
            >
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED}
                onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
                className="hidden"
              />
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="screenshot preview"
                  className="max-h-64 rounded-md border border-border/70 object-contain"
                />
              ) : (
                <ImageIcon className="h-10 w-10 text-muted-foreground" />
              )}
              <div className="text-sm">
                {file ? (
                  <>
                    <span className="font-medium">{file.name}</span>
                    <span className="text-muted-foreground"> · {formatBytes(file.size)}</span>
                  </>
                ) : (
                  <>
                    <span className="font-medium">Drop a screenshot here</span>
                    <span className="text-muted-foreground"> or click to pick a file</span>
                  </>
                )}
              </div>
              <div className="text-xs text-muted-foreground">
                PNG / JPEG / WebP · up to 10 MB
              </div>
            </div>
            {file && (
              <div className="mt-3 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setFile(null)}
                >
                  Remove
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-2">
          <Label htmlFor="source-url">Upwork job URL (optional)</Label>
          <Input
            id="source-url"
            type="url"
            placeholder="https://www.upwork.com/jobs/~01…"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Just saved on the job for traceability. The URL alone doesn't import
            anything — Upwork blocks automated access, so we need the screenshot
            above to read the post.
          </p>
        </div>

        <div className="flex items-center justify-between gap-3 rounded-md border border-border/70 bg-card/40 p-3">
          <div className="text-sm">
            {file ? (
              <span className="text-emerald-400">
                ✓ Ready to import — screenshot attached.
              </span>
            ) : (
              <span className="text-muted-foreground">
                <span className="font-medium text-foreground">Step 1:</span> upload
                a screenshot above. <span className="font-medium text-foreground">Step 2:</span> click Import.
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={() => navigate("/jobs")}>
              Cancel
            </Button>
            <Button type="submit" disabled={importMutation.isPending}>
              {importMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Importing…
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Import job
                </>
              )}
            </Button>
          </div>
        </div>
      </form>

      {importMutation.data && <PreviewPanel preview={importMutation.data.preview} />}
    </div>
  );
}
