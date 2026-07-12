import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/getApiErrorMessage";
import { AuthShell } from "@/shared/ui/brand/AuthShell";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useForgotPassword } from "@/features/auth/authApi";
import { forgotPasswordSchema } from "@/features/auth/authSchema";
import { DevResetLinkHint } from "@/features/auth/DevResetLinkHint";

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [sentMessage, setSentMessage] = useState<string | null>(null);

  const forgotPassword = useForgotPassword();

  const submit = () => {
    const parsed = forgotPasswordSchema.safeParse({ email });
    if (!parsed.success) {
      setFieldError(parsed.error.issues[0]?.message ?? "Enter a valid email address");
      return;
    }
    setFieldError(null);
    forgotPassword.mutate(parsed.data, {
      onSuccess: (data) => setSentMessage(data.message),
      onError: (err: unknown) => {
        toast.error(getApiErrorMessage(err, "Could not send reset instructions"));
      },
    });
  };

  if (sentMessage) {
    return (
      <AuthShell>
        <div className="mb-6 space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight">Check your email</h2>
          <p className="text-sm text-muted-foreground">{sentMessage}</p>
        </div>
        <p className="text-sm text-muted-foreground">
          The link expires after a short while. If nothing arrives, check your spam folder or
          request a new link.
        </p>
        <DevResetLinkHint email={email} />
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="mt-6 w-full"
          onClick={() => navigate("/login")}
        >
          Back to sign in
        </Button>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <div className="mb-6 space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">Forgot your password?</h2>
        <p className="text-sm text-muted-foreground">
          Enter your email and we'll send you a link to reset it.
        </p>
      </div>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={email}
            required
            autoComplete="email"
            autoFocus
            onChange={(e) => setEmail(e.target.value)}
          />
          {fieldError && <p className="text-xs text-destructive">{fieldError}</p>}
        </div>
        <Button
          type="submit"
          variant="brand"
          size="lg"
          className="w-full"
          disabled={forgotPassword.isPending}
        >
          {forgotPassword.isPending ? "Sending…" : "Send reset link"}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          <button
            type="button"
            className="text-primary hover:underline"
            onClick={() => navigate("/login")}
          >
            Back to sign in
          </button>
        </p>
      </form>
    </AuthShell>
  );
}
