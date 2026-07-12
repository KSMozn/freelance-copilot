import { LogOut, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { PersonaSwitcher } from "@/features/professional/personas/PersonaSwitcher";
import { Button } from "@/shared/ui/button";
import { logoutCurrentSurface } from "@/app/apiClient";
import { useAuthStore } from "@/features/auth/authStore";

export function Topbar() {
  const user = useAuthStore((s) => s.user);
  const logout = () => void logoutCurrentSurface();
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div className="text-sm text-muted-foreground">Engineering Career OS</div>
      <div className="flex items-center gap-3">
        <PersonaSwitcher />
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setDark((d) => !d)}
          aria-label="toggle theme"
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <div className="hidden text-sm md:block">{user?.email}</div>
        <Button variant="ghost" size="icon" onClick={logout} aria-label="log out">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
