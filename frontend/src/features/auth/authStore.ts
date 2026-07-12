import { STORAGE_KEYS } from "@/shared/config/brand";
import { clearSessionCache } from "@/app/queryClient";
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  email_verified_at: string | null;
  last_login_at: string | null;
  selected_persona_kind: "professional" | "student";
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  // Phase C — id of the persona the user is currently "wearing." Drives which
  // pot/weights/tone downstream calls use. Hydrated from /personas/current
  // after login; user can switch via the topbar.
  activePersonaId: string | null;
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setActivePersonaId: (id: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      activePersonaId: null,
      setAuth: (user, accessToken, refreshToken) => {
        clearSessionCache();
        set({ user, accessToken, refreshToken, activePersonaId: null });
      },
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setActivePersonaId: (id) => set({ activePersonaId: id }),
      logout: () => {
        clearSessionCache();
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          activePersonaId: null,
        });
      },
    }),
    { name: STORAGE_KEYS.auth },
  ),
);
