import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { useSubmitSurvey } from "@/features/student-wizard/feedback/feedbackApi";

interface PostDownloadSurveyProps {
  templateSlug: string | null;
  // Called after successful send OR skip — parent hides the card.
  onDismiss: () => void;
}

/**
 * Non-blocking card that appears in the Preview step right after the
 * student downloads a CV. Asks for a 1..5 star rating + optional
 * comment. Both Send and Skip dismiss the card for the current session.
 */
export function PostDownloadSurvey({ templateSlug, onDismiss }: PostDownloadSurveyProps) {
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [hover, setHover] = useState<number | null>(null);
  const submit = useSubmitSurvey();

  async function send() {
    if (!rating) return;
    try {
      await submit.mutateAsync({
        rating,
        comment: comment.trim() || null,
        template_slug: templateSlug,
      });
      toast.success("Thanks for rating!");
      onDismiss();
    } catch {
      toast.error("Couldn't submit — try again.");
    }
  }

  const highlightTo = hover ?? rating ?? 0;

  return (
    <div className="rounded-md border border-primary/30 bg-primary/5 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-medium">How was this template?</div>
        <button
          type="button"
          onClick={onDismiss}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          Skip
        </button>
      </div>
      <div className="mt-2 flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            aria-label={`${n} star${n === 1 ? "" : "s"}`}
            onMouseEnter={() => setHover(n)}
            onMouseLeave={() => setHover(null)}
            onClick={() => setRating(n)}
            className="text-2xl leading-none transition"
          >
            <span className={n <= highlightTo ? "text-amber-500" : "text-muted-foreground/40"}>
              ★
            </span>
          </button>
        ))}
        <span className="ml-2 text-xs text-muted-foreground">
          {rating ? `${rating}/5` : "Tap a star"}
        </span>
      </div>
      <Textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Anything you'd like to add? (optional)"
        className="mt-3 min-h-[64px]"
      />
      <div className="mt-3 flex justify-end">
        <Button size="sm" onClick={() => void send()} disabled={!rating || submit.isPending}>
          {submit.isPending ? "Sending…" : "Send"}
        </Button>
      </div>
    </div>
  );
}
