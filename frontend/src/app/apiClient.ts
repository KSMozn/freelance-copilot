import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAdminAuthStore } from "@/features/admin/adminAuthStore";
import { useAuthStore } from "@/features/auth/authStore";

// Pick the backend URL from the current frontend host so the same bundle
// works on all three deploys without a rebuild:
//   *.careero.app          -> https://api.careero.app/api/v1
//   *.personaarmory.com    -> https://api.personaarmory.com/api/v1
//   *.run.app              -> the paired Cloud Run backend URL
//   anything else (dev)    -> VITE_API_BASE_URL or localhost fallback
function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
  }
  const host = window.location.hostname;
  if (host.endsWith("careero.app")) return "https://api.careero.app/api/v1";
  if (host.endsWith("personaarmory.com")) return "https://api.personaarmory.com/api/v1";
  if (host.endsWith(".run.app")) {
    // Frontend service name pattern: freelance-copilot-frontend-<hash>-<region>.a.run.app
    // Paired backend swaps 'frontend' for 'backend', same hash + region.
    const backendHost = host.replace("freelance-copilot-frontend", "freelance-copilot-backend");
    return `https://${backendHost}/api/v1`;
  }
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
}

const baseURL = resolveApiBaseUrl();

// Which auth store is authoritative depends on the subdomain the SPA
// is being served from. Bundle-loaded on `admin.*` -> talk to
// /admin/auth/*; bundle-loaded on `app.*` -> talk to /auth/*.
//
// Escape hatch for the raw Cloud Run URL (where custom-domain hostnames
// are unavailable): pass `?surface=admin` once, we sticky-store the choice
// in sessionStorage so subsequent client-side navigations stay in admin
// mode. `?surface=app` clears it.
function detectAdminSurface(): boolean {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  if (host === "admin.personaarmory.com" || host.startsWith("admin.")) return true;
  try {
    const params = new URLSearchParams(window.location.search);
    const override = params.get("surface");
    if (override === "admin") sessionStorage.setItem("surface", "admin");
    else if (override === "app") sessionStorage.removeItem("surface");
    return sessionStorage.getItem("surface") === "admin";
  } catch {
    return false;
  }
}

export const isAdminSurface = detectAdminSurface();

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = isAdminSurface
    ? useAdminAuthStore.getState().accessToken
    : useAuthStore.getState().accessToken;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshInFlight: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  if (isAdminSurface) {
    const refreshToken = useAdminAuthStore.getState().refreshToken;
    if (!refreshToken) return null;
    try {
      const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
        `${baseURL}/admin/auth/refresh`,
        { refresh_token: refreshToken },
      );
      useAdminAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } catch {
      useAdminAuthStore.getState().logout();
      return null;
    }
  }
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
      `${baseURL}/auth/refresh`,
      { refresh_token: refreshToken },
    );
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    useAuthStore.getState().logout();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      refreshInFlight ??= tryRefresh().finally(() => {
        refreshInFlight = null;
      });
      const newToken = await refreshInFlight;
      if (newToken) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return api.request(original);
      }
    }
    return Promise.reject(error);
  },
);

/**
 * Log out of the surface this bundle is serving. Best-effort: revokes the
 * refresh token's whole family server-side (so it can't be replayed) before
 * clearing local state. Network failure still clears locally.
 */
export async function logoutCurrentSurface(): Promise<void> {
  const store = isAdminSurface ? useAdminAuthStore : useAuthStore;
  const path = isAdminSurface ? "/admin/auth/logout" : "/auth/logout";
  const refreshToken = store.getState().refreshToken;
  if (refreshToken) {
    try {
      await axios.post(`${baseURL}${path}`, { refresh_token: refreshToken });
    } catch {
      // Server-side revoke is best-effort; the local clear below is what the
      // user sees. A stale token self-expires within its TTL regardless.
    }
  }
  store.getState().logout();
}
