import { useLayoutEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/getApiErrorMessage";
import { AuthShell } from "@/shared/ui/brand/AuthShell";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useResetPassword } from "@/features/auth/authApi";
import { resetPasswordSchema } from "@/features/auth/authSchema";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    return params.get("token") ?? "";
  });

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{
    password?: string;
    confirmPassword?: string;
  }>({});
  const [done, setDone] = useState(false);

  useLayoutEffect(() => {
    const params = new URLSearchParams(location.hash.replace(/^#/, ""));
    const nextToken = params.get("token");
    if (!nextToken) return;

    setToken(nextToken);
    setPassword("");
    setConfirmPassword("");
    setFieldErrors({});
    setDone(false);
    navigate(`${location.pathname}${location.search}`, { replace: true });
  }, [location.hash, location.pathname, location.search, navigate]);

  const resetPassword = useResetPassword();

  const submit = () => {
    const parsed = resetPasswordSchema.safeParse({ password, confirmPassword });
    if (!parsed.success) {
      const errors: { password?: string; confirmPassword?: string } = {};
      for (const issue of parsed.error.issues) {
        const field = issue.path[0];
        if (field === "password" && !errors.password) errors.password = issue.message;
        if (field === "confirmPassword" && !errors.confirmPassword)
          errors.confirmPassword = issue.message;
      }
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    resetPassword.mutate(
      { token, newPassword: parsed.data.password },
      {
        onSuccess: () => setDone(true),
        onError: (err: unknown) => {
          toast.error(getApiErrorMessage(err, "Could not reset password"));
        },
      },
    );
  };

  // No token in the URL — the link is broken or was typed by hand.
  if (!token) {
    return (
      <AuthShell>
        <div className="mb-6 space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight">Invalid reset link</h2>
          <p className="text-sm text-muted-foreground">
            This link is missing its reset token. Request a new one and use the link from the email.
          </p>
        </div>
        <Button
          type="button"
          variant="brand"
          size="lg"
          className="w-full"
          onClick={() => navigate("/forgot-password")}
        >
          Request a new link
        </Button>
      </AuthShell>
    );
  }

  if (done) {
    return (
      <AuthShell>
        <div className="mb-6 space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight">Password updated</h2>
          <p className="text-sm text-muted-foreground">
            Your password has been changed. Other devices will need to sign in again when their
            current access expires.
          </p>
        </div>
        <Button
          type="button"
          variant="brand"
          size="lg"
          className="w-full"
          onClick={() => navigate("/login")}
        >
          Sign in
        </Button>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <div className="mb-6 space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">Choose a new password</h2>
        <p className="text-sm text-muted-foreground">
          It must be at least 8 characters. Existing refresh sessions will be revoked.
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
          <Label htmlFor="new-password">New password</Label>
          <Input
            id="new-password"
            type="password"
            value={password}
            required
            autoComplete="new-password"
            autoFocus
            onChange={(e) => setPassword(e.target.value)}
          />
          {fieldErrors.password && (
            <p className="text-xs text-destructive">{fieldErrors.password}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm-password">Confirm new password</Label>
          <Input
            id="confirm-password"
            type="password"
            value={confirmPassword}
            required
            autoComplete="new-password"
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          {fieldErrors.confirmPassword && (
            <p className="text-xs text-destructive">{fieldErrors.confirmPassword}</p>
          )}
        </div>
        <Button
          type="submit"
          variant="brand"
          size="lg"
          className="w-full"
          disabled={resetPassword.isPending}
        >
          {resetPassword.isPending ? "Updating…" : "Update password"}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          <button
            type="button"
            className="text-primary hover:underline"
            onClick={() => navigate("/forgot-password")}
          >
            Link expired? Request a new one
          </button>
        </p>
      </form>
    </AuthShell>
  );
}
