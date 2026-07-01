import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

interface AdminAuthState {
  admin: AdminUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (admin: AdminUser, access: string, refresh: string) => void;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
}

// Separate store from the student auth store because localStorage is
// origin-scoped anyway (app.* vs admin.*) — but even if they ever share
// an origin (dev), the two stores can't clobber each other.
export const useAdminAuthStore = create<AdminAuthState>()(
  persist(
    (set) => ({
      admin: null,
      accessToken: null,
      refreshToken: null,
      setAuth: (admin, accessToken, refreshToken) =>
        set({ admin, accessToken, refreshToken }),
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      logout: () => set({ admin: null, accessToken: null, refreshToken: null }),
    }),
    { name: "persona-armory-admin-auth" },
  ),
);
