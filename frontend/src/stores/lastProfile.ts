import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Snapshot of the most-recent student who signed in on this browser.
 *
 * This store is *intentionally* independent of `useAuthStore`. Signing out
 * wipes the auth store (tokens + user), but this snapshot survives so the
 * Facebook-style /login picker can greet the returning student by name +
 * photo. Cleared only via `forget()` — no timeout, no size-limit rotation
 * (only one slot is kept, latest wins).
 *
 * Kept intentionally small: email, full name, and a base64 data URI of
 * the profile photo. The data URI is capped at ~200 KB by the photo
 * capture helper (`lib/photoCache.ts`) so we don't blow past
 * localStorage's ~5 MB budget on a single key.
 */
export interface LastProfile {
  email: string;
  full_name: string | null;
  photo_data_uri: string | null;
  // Crop transform — same three fields the CV renders read on the
  // server. Cached here so the login picker's avatar matches the crop
  // the student set in the wizard, even before they sign in.
  photo_offset_x: number;
  photo_offset_y: number;
  photo_zoom: number;
  captured_at: string; // ISO
}

interface LastProfileState {
  profile: LastProfile | null;
  /** Overwrite the snapshot (single slot — most-recent wins). */
  remember: (p: Omit<LastProfile, "captured_at">) => void;
  /** Update just the photo without touching identity fields. */
  patchPhoto: (data_uri: string | null) => void;
  /** Explicit forget — used by a "not you?" affordance on the picker. */
  forget: () => void;
}

export const useLastProfileStore = create<LastProfileState>()(
  persist(
    (set) => ({
      profile: null,
      remember: (p) =>
        set({
          profile: {
            email: p.email,
            full_name: p.full_name,
            photo_data_uri: p.photo_data_uri,
            photo_offset_x: p.photo_offset_x,
            photo_offset_y: p.photo_offset_y,
            photo_zoom: p.photo_zoom,
            captured_at: new Date().toISOString(),
          },
        }),
      patchPhoto: (data_uri) =>
        set((state) =>
          state.profile
            ? {
                profile: {
                  ...state.profile,
                  photo_data_uri: data_uri,
                  captured_at: new Date().toISOString(),
                },
              }
            : state,
        ),
      forget: () => set({ profile: null }),
    }),
    { name: "careero-last-profile" },
  ),
);
