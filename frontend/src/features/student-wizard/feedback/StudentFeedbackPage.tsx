import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Textarea } from "@/shared/ui/textarea";
import { logoutCurrentSurface } from "@/app/apiClient";
import { useSubmitFeedback } from "@/features/student-wizard/feedback/feedbackApi";

const MIN_LEN = 10;

export function StudentFeedbackPage() {
  const [message, setMessage] = useState("");
  const [submittedAt, setSubmittedAt] = useState<Date | null>(null);
  const submit = useSubmitFeedback();

  const tooShort = message.trim().length < MIN_LEN;

  async function onSubmit() {
    if (tooShort) return;
    try {
      await submit.mutateAsync({ message: message.trim() });
      setSubmittedAt(new Date());
      setMessage("");
      toast.success("Thanks — we read every one.");
    } catch {
      toast.error("Couldn't submit — please try again.");
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-2xl px-4 py-8">
        <div className="mb-4 flex items-center justify-between gap-4">
          <Link to="/student" className="text-xs text-muted-foreground hover:text-foreground">
            ← Back to your CV
          </Link>
          <SignOutLink />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Feedback</CardTitle>
            <CardDescription>
              Bugs, gripes, features you wish existed, anything. Every message lands in our inbox.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="What's on your mind?"
              className="min-h-[160px]"
            />
            <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span>
                {tooShort
                  ? `Write at least ${MIN_LEN} characters.`
                  : `${message.trim().length} characters`}
              </span>
              <Button onClick={() => void onSubmit()} disabled={tooShort || submit.isPending}>
                {submit.isPending ? "Sending…" : "Send feedback"}
              </Button>
            </div>
            {submittedAt && (
              <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
                Submitted at {submittedAt.toLocaleTimeString()} — thanks. Feel free to send more.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SignOutLink() {
  const navigate = useNavigate();
  return (
    <button
      type="button"
      onClick={() => {
        void logoutCurrentSurface().finally(() => navigate("/login", { replace: true }));
      }}
      className="text-xs text-muted-foreground hover:text-foreground"
    >
      Sign out
    </button>
  );
}
