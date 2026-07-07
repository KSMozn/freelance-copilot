import { Navigate, NavLink, Outlet, useNavigate } from "react-router-dom";

import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { useAdminAuthStore } from "@/stores/adminAuth";
import { cn } from "@/lib/utils";

export function AdminLayout() {
  const admin = useAdminAuthStore((s) => s.admin);
  const accessToken = useAdminAuthStore((s) => s.accessToken);
  const logout = useAdminAuthStore((s) => s.logout);
  const navigate = useNavigate();

  if (!accessToken || !admin) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="flex w-56 flex-col border-r bg-card">
        <div className="border-b p-4">
          <BrandWordmark variant="personaarmory-admin" size={22} />
          <div className="mt-1.5 truncate text-xs text-muted-foreground">
            {admin.email}
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-2">
          <SideLink to="/overview" label="Overview" />
          <SideLink to="/users" label="Users" />
          <SideLink to="/feedback" label="Feedback" />
          <SideLink to="/emails" label="Emails" />
          <SideLink to="/templates" label="Templates" />
          <SideLink to="/activity" label="Activity" />
        </nav>
        <div className="space-y-1 border-t p-2 text-xs">
          <button
            type="button"
            onClick={() => {
              logout();
              navigate("/login", { replace: true });
            }}
            className="block w-full rounded-md px-3 py-2 text-left hover:bg-muted"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-x-hidden">
        <div className="mx-auto max-w-6xl p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function SideLink({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "block rounded-md px-3 py-2 text-sm transition-colors",
          isActive
            ? "bg-primary/10 font-medium text-primary"
            : "text-muted-foreground hover:bg-muted",
        )
      }
    >
      {label}
    </NavLink>
  );
}
