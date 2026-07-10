import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/getApiErrorMessage";
import { AuthShell } from "@/shared/ui/brand/AuthShell";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useLastProfileStore } from "@/features/auth/lastProfileStore";
import { api } from "@/app/apiClient";
import { useAuthStore, type AuthUser } from "@/features/auth/authStore";
import { DevOtpHint } from "@/features/auth/DevOtpHint";

interface AuthResponse {
  user: AuthUser;
  tokens: { access_token: string; refresh_token: string };
}

interface OtpRequestResponse {
  sent: boolean;
  expires_in_minutes: number;
}

type AuthMode = "password" | "otp";
type Step = "identity" | "code";

// Persona is hard-coded to Student for now — only the Student wizard
// surface is live. Switching back to multi-persona is a UI restore (the
// backend still accepts persona_kind="professional").
const PERSONA_KIND = "student";

export function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);

  // Login passes whatever the user already typed there as route state so
  // we don't make them re-enter it. Read once on mount; never round-trip.
  const carried = (location.state as { email?: string; password?: string } | null) ?? {};

  const [step, setStep] = useState<Step>("identity");
  const [authMode, setAuthMode] = useState<AuthMode>("password");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState(carried.email ?? "");
  const [password, setPassword] = useState(carried.password ?? "");
  const [code, setCode] = useState("");
  const [expiresMin, setExpiresMin] = useState(10);
  const credentialsCarriedOver = Boolean(carried.email && carried.password);

  const redirectAfter = (data: AuthResponse) => {
    setAuth(data.user, data.tokens.access_token, data.tokens.refresh_token);
    // Seed the login picker so the next visit greets them by name.
    // Photo is filled in later, on the wizard's next mount.
    useLastProfileStore.getState().remember({
      email: data.user.email,
      full_name: data.user.full_name,
      photo_data_uri: null,
      photo_offset_x: 50,
      photo_offset_y: 50,
      photo_zoom: 100,
    });
    navigate(data.user.selected_persona_kind === "student" ? "/student" : "/", {
      replace: true,
    });
  };

  const passwordRegister = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<AuthResponse>("/auth/register", {
        email,
        full_name: fullName || null,
        password,
        persona_kind: PERSONA_KIND,
      });
      return data;
    },
    onSuccess: redirectAfter,
    onError: (err: unknown) => {
      toast.error(getApiErrorMessage(err, "Could not register"));
    },
  });

  const requestCode = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<OtpRequestResponse>("/auth/request-code", {
        email,
        purpose: "register",
      });
      return data;
    },
    onSuccess: (data) => {
      setExpiresMin(data.expires_in_minutes);
      setStep("code");
    },
    onError: (err: unknown) => {
      toast.error(getApiErrorMessage(err, "Could not send code"));
    },
  });

  const verifyCode = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<AuthResponse>("/auth/verify-code", {
        email,
        code,
        purpose: "register",
        full_name: fullName || null,
        persona_kind: PERSONA_KIND,
      });
      return data;
    },
    onSuccess: redirectAfter,
    onError: (err: unknown) => {
      toast.error(getApiErrorMessage(err, "Invalid code"));
    },
  });

  const header = HEADERS[step];
  const description =
    step === "identity" && credentialsCarriedOver
      ? "We've got your email and password. Just need a name for your CV."
      : header.description;

  return (
    <AuthShell
      title="Join Careero"
      subtitle="Set up your account in under a minute — one email, and we'll take it from there."
    >
      <ProgressDots step={step} authMode={authMode} />
      <div className="mb-6 mt-4 space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">{header.title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div>
        {step === "identity" && (
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              if (authMode === "password") passwordRegister.mutate();
              else requestCode.mutate();
            }}
          >
            {credentialsCarriedOver && (
              <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
                <div className="font-medium">Using the email + password from sign-in</div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  {email}
                  {" · "}
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => navigate("/login")}
                  >
                    change
                  </button>
                </div>
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="r-name">What should we call you?</Label>
              <Input
                id="r-name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
                autoFocus
                placeholder="Sara Student"
              />
            </div>
            {!credentialsCarriedOver && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="r-email">Email</Label>
                  <Input
                    id="r-email"
                    type="email"
                    value={email}
                    required
                    autoComplete="email"
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="sara.student@school.edu"
                  />
                </div>
                {authMode === "password" ? (
                  <div className="space-y-2">
                    <Label htmlFor="r-password">Password</Label>
                    <Input
                      id="r-password"
                      type="password"
                      value={password}
                      required
                      minLength={8}
                      autoComplete="new-password"
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      At least 8 characters.{" "}
                      <button
                        type="button"
                        className="text-primary hover:underline"
                        onClick={() => setAuthMode("otp")}
                      >
                        Use email code instead
                      </button>
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    We'll send a 6-digit code — no password needed.{" "}
                    <button
                      type="button"
                      className="text-primary hover:underline"
                      onClick={() => setAuthMode("password")}
                    >
                      Use a password instead
                    </button>
                  </p>
                )}
              </>
            )}
            <Button
              type="submit"
              variant="brand"
              size="lg"
              className="w-full"
              disabled={
                !email ||
                (authMode === "password"
                  ? passwordRegister.isPending || password.length < 8
                  : requestCode.isPending)
              }
            >
              {authMode === "password"
                ? passwordRegister.isPending
                  ? "Creating…"
                  : "Create account"
                : requestCode.isPending
                  ? "Sending…"
                  : "Send code"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link className="text-primary hover:underline" to="/login">
                Sign in
              </Link>
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
              <Label htmlFor="r-code">6-digit code sent to {email}</Label>
              <Input
                id="r-code"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                value={code}
                required
                autoFocus
                className="text-center font-mono text-2xl tracking-[0.5em]"
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
            <DevOtpHint email={email} onCode={setCode} />
            <div className="flex gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setCode("");
                  setStep("identity");
                }}
              >
                Back
              </Button>
              <Button
                type="submit"
                variant="brand"
                size="lg"
                className="flex-1"
                disabled={verifyCode.isPending || code.length !== 6}
              >
                {verifyCode.isPending ? "Verifying…" : "Create account"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </AuthShell>
  );
}

const HEADERS: Record<Step, { title: string; description: string }> = {
  identity: {
    title: "Create your student account",
    description: "Just a name, email, and password.",
  },
  code: {
    title: "Check your inbox",
    description: "Enter the 6-digit code to finish creating your account.",
  },
};

function ProgressDots({ step, authMode }: { step: Step; authMode: AuthMode }) {
  // Password is a single step; OTP adds the code step.
  const order: Step[] = authMode === "password" ? ["identity"] : ["identity", "code"];
  const idx = order.indexOf(step);
  return (
    <div className="flex items-center gap-1.5">
      {order.map((s, i) => (
        <span
          key={s}
          className={"h-1.5 flex-1 rounded-full " + (i <= idx ? "bg-primary" : "bg-muted")}
        />
      ))}
    </div>
  );
}
