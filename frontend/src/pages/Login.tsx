import { useMutation } from "@tanstack/react-query";
import { ChevronLeft } from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { AuthShell } from "@/components/brand/AuthShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useAuthStore, type AuthUser } from "@/stores/auth";
import { useLastProfileStore } from "@/stores/lastProfile";

interface AuthResponse {
  user: AuthUser;
  tokens: { access_token: string; refresh_token: string };
}

interface OtpRequestResponse {
  sent: boolean;
  expires_in_minutes: number;
}

type Step = "picker" | "email" | "code" | "password";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const rememberLastProfile = useLastProfileStore((s) => s.remember);
  const lastProfile = useLastProfileStore((s) => s.profile);

  // If a previous session left a snapshot, greet the returner directly.
  // Fresh browsers skip straight to the email input (behavior parity with
  // the pre-picker version).
  const [step, setStep] = useState<Step>(() =>
    lastProfile ? "picker" : "email",
  );
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  // Prefill the name for returners so they don't type it twice. Reset
  // only when the student explicitly types a different email at the
  // email step (see the "Use a different email" handler).
  const [fullName, setFullName] = useState(lastProfile?.full_name ?? "");
  const [password, setPassword] = useState("");
  const [expiresMin, setExpiresMin] = useState(10);

  const redirectAfter = (data: AuthResponse) => {
    setAuth(data.user, data.tokens.access_token, data.tokens.refresh_token);
    // Save a snapshot for the next visit's picker. Photo comes later —
    // the wizard fetches it on mount and patches this store then.
    rememberLastProfile({
      email: data.user.email,
      full_name: data.user.full_name,
      photo_data_uri: null,
      photo_offset_x: 50,
      photo_offset_y: 50,
      photo_zoom: 100,
    });
    // First-ever sign-in (last_login_at is null in the response because the
    // server records it AFTER constructing the response). Funnel new users
    // through the compact onboarding page.
    const fromState = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    const target = data.user.last_login_at == null ? "/onboarding" : (fromState ?? "/");
    navigate(target, { replace: true });
  };

  const requestCode = useMutation({
    mutationFn: async (vars: { email: string }) => {
      const { data } = await api.post<OtpRequestResponse>("/auth/request-code", {
        email: vars.email,
        purpose: "login",
      });
      return data;
    },
    onSuccess: (data, vars) => {
      setExpiresMin(data.expires_in_minutes);
      setEmail(vars.email);
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
        // Careero is currently a student-only shell. If the OTP verify
        // is the first time we've seen this email, the backend creates
        // the account with this persona. Ignored for existing users.
        persona_kind: "student",
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

  // Show a back-arrow that returns to the picker whenever a snapshot is
  // available AND we're not currently on the picker itself.
  const canReturnToPicker = !!lastProfile && step !== "picker";
  const backToPicker = () => {
    setCode("");
    setPassword("");
    setStep("picker");
  };

  return (
    <AuthShell>
      {canReturnToPicker && (
        <button
          type="button"
          onClick={backToPicker}
          className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
          aria-label="Back"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>
      )}

      {step === "picker" && lastProfile && (
        <PickerStep
          profile={lastProfile}
          continuing={requestCode.isPending}
          onContinue={() =>
            requestCode.mutate({ email: lastProfile.email })
          }
          onUseAnother={() => {
            setEmail("");
            setFullName("");
            setStep("email");
          }}
          onCreateAccount={() => navigate("/register")}
        />
      )}

      {step === "email" && (
        <>
          <div className="mb-6 space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">Sign in</h2>
            <p className="text-sm text-muted-foreground">
              We'll send a 6-digit code to your email.
            </p>
          </div>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              requestCode.mutate({ email });
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
            <Button
              type="submit"
              variant="brand"
              size="lg"
              className="w-full"
              disabled={requestCode.isPending}
            >
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
        </>
      )}

      {step === "code" && (
        <>
          <div className="mb-6 space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">
              Check your email
            </h2>
            <p className="text-sm text-muted-foreground">
              Enter the code we sent to {email}.
            </p>
          </div>
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
                  onClick={() => requestCode.mutate({ email })}
                  disabled={requestCode.isPending}
                >
                  Resend
                </button>
              </p>
            </div>
            {/* New signups only — a returning student (whose email matches
                the picker snapshot) already has a name on file. */}
            {(!lastProfile || lastProfile.email !== email) && (
              <div className="space-y-2">
                <Label htmlFor="name">Your name (optional, for new accounts)</Label>
                <Input
                  id="name"
                  value={fullName}
                  autoComplete="name"
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
            )}
            <Button
              type="submit"
              variant="brand"
              size="lg"
              className="w-full"
              disabled={verifyCode.isPending || code.length !== 6}
            >
              {verifyCode.isPending ? "Verifying…" : "Verify & sign in"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              <button
                type="button"
                className="text-primary hover:underline"
                onClick={() => {
                  setCode("");
                  setFullName("");
                  setStep("email");
                }}
              >
                Use a different email
              </button>
            </p>
          </form>
        </>
      )}

      {step === "password" && (
        <>
          <div className="mb-6 space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">Sign in</h2>
            <p className="text-sm text-muted-foreground">
              Use your password to sign in.
            </p>
          </div>
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
            <Button
              type="submit"
              variant="brand"
              size="lg"
              className="w-full"
              disabled={passwordLogin.isPending}
            >
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
              <button
                type="button"
                className="text-primary hover:underline"
                onClick={() =>
                  navigate("/register", {
                    // Carry what they've already typed so /register
                    // doesn't make them re-enter it. Password is
                    // intentionally passed in route state (not query
                    // string) — never URL-logged.
                    state: { email, password },
                  })
                }
              >
                Register
              </button>
            </p>
          </form>
        </>
      )}
    </AuthShell>
  );
}

// ---- picker step ------------------------------------------------------

interface PickerStepProps {
  profile: {
    email: string;
    full_name: string | null;
    photo_data_uri: string | null;
    photo_offset_x: number;
    photo_offset_y: number;
    photo_zoom: number;
  };
  continuing: boolean;
  onContinue: () => void;
  onUseAnother: () => void;
  onCreateAccount: () => void;
}

function PickerStep({
  profile,
  continuing,
  onContinue,
  onUseAnother,
  onCreateAccount,
}: PickerStepProps) {
  const displayName = profile.full_name?.trim() || profile.email;
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-3 pt-2">
        <Avatar
          photoDataUri={profile.photo_data_uri}
          name={profile.full_name}
          email={profile.email}
          offsetX={profile.photo_offset_x}
          offsetY={profile.photo_offset_y}
          zoom={profile.photo_zoom}
        />
        <div className="text-center">
          <div className="text-2xl font-semibold tracking-tight">
            {displayName}
          </div>
          {profile.full_name && (
            <div className="mt-0.5 text-sm text-muted-foreground">
              {profile.email}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <Button
          type="button"
          variant="brand"
          size="lg"
          className="w-full"
          onClick={onContinue}
          disabled={continuing}
        >
          {continuing ? "Sending code…" : "Continue"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="w-full"
          onClick={onUseAnother}
        >
          Use another profile
        </Button>
      </div>

      <div className="border-t pt-4 text-center text-sm text-muted-foreground">
        <button
          type="button"
          className="text-primary hover:underline"
          onClick={onCreateAccount}
        >
          Create new account
        </button>
      </div>
    </div>
  );
}

function Avatar({
  photoDataUri,
  name,
  email,
  offsetX,
  offsetY,
  zoom,
}: {
  photoDataUri: string | null;
  name: string | null;
  email: string;
  offsetX: number;
  offsetY: number;
  zoom: number;
}) {
  // 96 px circle with a subtle brand-gradient ring. Falls back to
  // initials in a gradient-filled circle when there's no photo cached.
  const initials = deriveInitials(name, email);
  return (
    <div className="relative">
      <div
        aria-hidden
        className="absolute inset-0 rounded-full bg-brand-gradient p-[2px]"
      />
      <div className="relative h-24 w-24 overflow-hidden rounded-full bg-background">
        {photoDataUri ? (
          // Match the CV renderer's crop: background-image + size + position.
          <div
            className="h-full w-full"
            style={{
              backgroundImage: `url("${photoDataUri}")`,
              backgroundPosition: `${offsetX}% ${offsetY}%`,
              backgroundSize: `${zoom}%`,
              backgroundRepeat: "no-repeat",
            }}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-brand-gradient text-xl font-semibold text-white">
            {initials}
          </div>
        )}
      </div>
    </div>
  );
}

function deriveInitials(name: string | null, email: string): string {
  const clean = name?.trim();
  if (clean) {
    const parts = clean.split(/\s+/).filter(Boolean);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  const local = email.split("@")[0] ?? "";
  return local.slice(0, 2).toUpperCase() || "•";
}
