import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { logoutCurrentSurface } from "@/app/apiClient";
import { FeedbackForm } from "@/features/student-wizard/feedback/FeedbackForm";

export function StudentFeedbackPage() {
  return (
    <div className="h-dvh overflow-y-auto bg-background [scrollbar-gutter:stable]">
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
          <CardContent>
            <FeedbackForm />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SignOutLink() {
  const navigate = useNavigate();
  const [signingOut, setSigningOut] = useState(false);
  return (
    <button
      type="button"
      disabled={signingOut}
      onClick={() => {
        setSigningOut(true);
        void logoutCurrentSurface().finally(() => navigate("/login", { replace: true }));
      }}
      className="text-xs text-muted-foreground hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
    >
      {signingOut ? "Signing out…" : "Sign out"}
    </button>
  );
}
