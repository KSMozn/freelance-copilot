import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { AuthShell } from "@/shared/ui/brand/AuthShell";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { api } from "@/app/apiClient";
import { useAdminAuthStore, type AdminUser } from "@/stores/adminAuth";

interface AdminLoginResponse {
  user: AdminUser;
  tokens: { access_token: string; refresh_token: string };
}

export function AdminLoginPage() {
  const navigate = useNavigate();
  const setAuth = useAdminAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<AdminLoginResponse>("/admin/auth/login", {
        email,
        password,
      });
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.tokens.access_token, data.tokens.refresh_token);
      navigate("/overview", { replace: true });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } } | undefined)?.response
        ?.data?.detail;
      toast.error(detail ?? "Invalid credentials");
    },
  });

  return (
    <AuthShell
      variant="personaarmory-admin"
      title="PersonaArmory Admin"
      subtitle="Operate the platform. Curate templates. Watch the numbers."
      slogan="Signal in. Insight out."
    >
      <div className="mb-6 space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">Admin sign-in</h2>
        <p className="text-sm text-muted-foreground">
          Admin identity is separate from your student account.
        </p>
      </div>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="a-email">Email</Label>
          <Input
            id="a-email"
            type="email"
            value={email}
            required
            autoComplete="email"
            autoFocus
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="a-password">Password</Label>
          <Input
            id="a-password"
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
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}
