import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useAuthStore, type AuthUser } from "@/stores/auth";

interface AuthResponse {
  user: AuthUser;
  tokens: { access_token: string; refresh_token: string };
}

interface OtpRequestResponse {
  sent: boolean;
  expires_in_minutes: number;
}

type Step = "email" | "code" | "password";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [expiresMin, setExpiresMin] = useState(10);

  const redirectAfter = (data: AuthResponse) => {
    setAuth(data.user, data.tokens.access_token, data.tokens.refresh_token);
    // First-ever sign-in (last_login_at is null in the response because the
    // server records it AFTER constructing the response). Funnel new users
    // through the compact onboarding page.
    const fromState = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    const target = data.user.last_login_at == null ? "/onboarding" : (fromState ?? "/");
    navigate(target, { replace: true });
  };

  const requestCode = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<OtpRequestResponse>("/auth/request-code", {
        email,
        purpose: "login",
      });
      return data;
    },
    onSuccess: (data) => {
      setExpiresMin(data.expires_in_minutes);
      setStep("code");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail ?? "Could not send code");
    },
  });

  const verifyCode = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<AuthResponse>("/auth/verify-code", {
        email,
        code,
        purpose: "login",
        full_name: fullName || null,
      });
      return data;
    },
    onSuccess: redirectAfter,
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail ?? "Invalid code");
    },
  });

  const passwordLogin = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<AuthResponse>("/auth/login", { email, password });
      return data;
    },
    onSuccess: redirectAfter,
    onError: () => toast.error("Invalid email or password"),
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            {step === "email" && "We'll send a 6-digit code to your email."}
            {step === "code" && `Enter the code we sent to ${email}.`}
            {step === "password" && "Use your password to sign in."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === "email" && (
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                requestCode.mutate();
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
              </div>
              <Button type="submit" className="w-full" disabled={requestCode.isPending}>
                {requestCode.isPending ? "Sending…" : "Send code"}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                <button
                  type="button"
                  className="text-primary hover:underline"
                  onClick={() => setStep("password")}
                >
                  Use a password instead
                </button>
              </p>
            </form>
          )}

          {step === "code" && (
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                verifyCode.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="code">6-digit code</Label>
                <Input
                  id="code"
                  inputMode="numeric"
                  pattern="\d{6}"
                  maxLength={6}
                  value={code}
                  required
                  autoFocus
                  className="text-center text-2xl tracking-[0.5em] font-mono"
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                />
                <p className="text-xs text-muted-foreground">
                  Expires in {expiresMin} min. Didn't get it?{" "}
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => requestCode.mutate()}
                    disabled={requestCode.isPending}
                  >
                    Resend
                  </button>
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Your name (optional, for new accounts)</Label>
                <Input
                  id="name"
                  value={fullName}
                  autoComplete="name"
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full" disabled={verifyCode.isPending || code.length !== 6}>
                {verifyCode.isPending ? "Verifying…" : "Verify & sign in"}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                <button
                  type="button"
                  className="text-primary hover:underline"
                  onClick={() => {
                    setCode("");
                    setStep("email");
                  }}
                >
                  Use a different email
                </button>
              </p>
            </form>
          )}

          {step === "password" && (
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                passwordLogin.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="email-pw">Email</Label>
                <Input
                  id="email-pw"
                  type="email"
                  value={email}
                  required
                  autoComplete="email"
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  required
                  autoComplete="current-password"
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full" disabled={passwordLogin.isPending}>
                {passwordLogin.isPending ? "Signing in…" : "Sign in"}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                <button
                  type="button"
                  className="text-primary hover:underline"
                  onClick={() => setStep("email")}
                >
                  Use an email code instead
                </button>
              </p>
              <p className="text-center text-sm text-muted-foreground">
                No account?{" "}
                <Link className="text-primary hover:underline" to="/register">
                  Register
                </Link>
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
