import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { useAuthStore, type AuthUser } from "@/stores/auth";

/**
 * Cross-subdomain impersonation landing page.
 *
 * When a superuser clicks "View as user" on admin.personaarmory.com, the
 * admin page fetches a token pair for the target and window.locations to
 * https://app.personaarmory.com/impersonate#p=<base64-json>. localStorage
 * is origin-scoped so we can't hand off directly; the URL fragment is
 * the transport. Fragments are never sent to the server and get cleared
 * immediately after use.
 */
export function ImpersonateLanding() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  useEffect(() => {
    const raw = window.location.hash.replace(/^#/, "");
    const params = new URLSearchParams(raw);
    const encoded = params.get("p");
    if (!encoded) {
      toast.error("No impersonation payload found");
      navigate("/login", { replace: true });
      return;
    }
    try {
      const decoded = JSON.parse(
        decodeURIComponent(escape(atob(encoded))),
      ) as {
        id: string;
        email: string;
        full_name: string | null;
        persona_kind: "student" | "professional";
        created_at: string;
        access_token: string;
        refresh_token: string;
      };
      const user: AuthUser = {
        id: decoded.id,
        email: decoded.email,
        full_name: decoded.full_name,
        is_active: true,
        is_superuser: false,
        created_at: decoded.created_at,
        email_verified_at: null,
        last_login_at: null,
        selected_persona_kind: decoded.persona_kind,
      };
      setAuth(user, decoded.access_token, decoded.refresh_token);
      // Wipe the fragment so a browser back-nav doesn't re-fire this.
      window.history.replaceState(null, "", window.location.pathname);
      toast.success(`Now viewing as ${decoded.email}`);
      navigate(decoded.persona_kind === "student" ? "/student" : "/", {
        replace: true,
      });
    } catch (err) {
      console.error("Failed to decode impersonation payload", err);
      toast.error("Invalid impersonation payload");
      navigate("/login", { replace: true });
    }
  }, [setAuth, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-sm text-muted-foreground">Signing you in as user…</div>
    </div>
  );
}
