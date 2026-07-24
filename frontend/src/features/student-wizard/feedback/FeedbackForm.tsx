import { useRef, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import { cn } from "@/shared/lib/utils";
import { useSubmitFeedback } from "@/features/student-wizard/feedback/feedbackApi";
import {
  FEEDBACK_MESSAGE_MAX,
  FEEDBACK_MESSAGE_MIN,
  validateDescription,
  validateScreenshot,
} from "@/features/student-wizard/feedback/feedbackSchema";
import { ScreenshotUpload } from "@/features/student-wizard/feedback/ScreenshotUpload";

export function FeedbackForm() {
  const [description, setDescription] = useState("");
  const [descriptionError, setDescriptionError] = useState<string | null>(null);
  const [screenshot, setScreenshot] = useState<File | null>(null);
  const [screenshotError, setScreenshotError] = useState<string | null>(null);
  const [submittedAt, setSubmittedAt] = useState<Date | null>(null);

  const submit = useSubmitFeedback();
  const descriptionRef = useRef<HTMLTextAreaElement>(null);

  function handleScreenshot(file: File | null) {
    setSubmittedAt(null);
    if (!file) {
      setScreenshot(null);
      setScreenshotError(null);
      return;
    }
    setScreenshot(file);
    setScreenshotError(validateScreenshot(file));
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const descErr = validateDescription(description);
    const shotErr = screenshot ? validateScreenshot(screenshot) : null;
    setDescriptionError(descErr);
    setScreenshotError(shotErr);

    if (descErr) {
      descriptionRef.current?.focus();
      return;
    }

    if (shotErr) return;

    try {
      await submit.mutateAsync({
        message: description.trim(),
        screenshot: screenshot ?? undefined,
      });
      setDescription("");
      setDescriptionError(null);
      setScreenshot(null);
      setScreenshotError(null);
      setSubmittedAt(new Date());
      toast.success("Thanks — we read every one.");
    } catch {
      // Preserve the user's input so they can retry.
      toast.error("Couldn't submit — please try again.");
    }
  }

  const pending = submit.isPending;
  const overLimit = description.length > FEEDBACK_MESSAGE_MAX;

  return (
    <form className="space-y-4" onSubmit={onSubmit} noValidate>
      <div className="space-y-1.5">
        <Label htmlFor="feedback-description">Describe the issue</Label>
        <Textarea
          id="feedback-description"
          ref={descriptionRef}
          value={description}
          onChange={(e) => {
            setDescription(e.target.value);
            if (descriptionError) setDescriptionError(null);
            if (submittedAt) setSubmittedAt(null);
          }}
          placeholder="Please explain what happened, how to reproduce it, and what you expected."
          maxLength={FEEDBACK_MESSAGE_MAX}
          required
          aria-required="true"
          aria-invalid={descriptionError ? true : undefined}
          aria-describedby={
            descriptionError ? "feedback-description-error" : "feedback-description-hint"
          }
          disabled={pending}
          className="min-h-[140px]"
        />
        <div className="flex items-start justify-between gap-3 text-xs">
          {descriptionError ? (
            <p id="feedback-description-error" role="alert" className="text-destructive">
              {descriptionError}
            </p>
          ) : (
            <p id="feedback-description-hint" className="text-muted-foreground">
              At least {FEEDBACK_MESSAGE_MIN} characters.
            </p>
          )}
          <span
            className={cn(
              "shrink-0 tabular-nums text-muted-foreground",
              overLimit && "text-destructive",
            )}
          >
            {description.length}/{FEEDBACK_MESSAGE_MAX}
          </span>
        </div>
      </div>

      <div className="space-y-1.5">
        <span id="feedback-screenshot-label" className="text-sm font-medium leading-none">
          Screenshot <span className="font-normal text-muted-foreground">(optional)</span>
        </span>
        <ScreenshotUpload
          value={screenshot}
          onSelect={handleScreenshot}
          error={screenshotError}
          disabled={pending}
          labelId="feedback-screenshot-label"
        />
      </div>

      {submittedAt && (
        <p
          role="status"
          className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm text-foreground"
        >
          Submitted at {submittedAt.toLocaleTimeString()} — thanks. Feel free to send more.
        </p>
      )}

      <div className="flex justify-end">
        <Button type="submit" disabled={pending}>
          {pending ? "Sending…" : "Send feedback"}
        </Button>
      </div>
    </form>
  );
}
