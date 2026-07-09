/**
 * Central brand constants. The product currently ships under two names —
 * "Careero" for the student surface, "PersonaArmory" for the company and
 * the admin surface — while the repo/package keep legacy names
 * (the repo is still named freelance-copilot). This file makes that drift
 * deliberate and single-sourced instead of scattered string literals.
 */
export const BRAND = {
  /** Student-facing product name. */
  product: "Careero",
  /** Company / admin-surface brand. */
  company: "PersonaArmory",
  /** Admin surface product title (auth shell heading). */
  adminProduct: "PersonaArmory Admin",
  /** Admin wordmark label (sidebar). */
  adminWordmark: "PersonaArmory · Admin",
  tagline: "Equip. Empower. Elevate.",
  adminTagline: "Signal in. Insight out.",
} as const;

/**
 * Persisted zustand storage keys.
 *
 * ⚠️ FROZEN — these values are written into users' localStorage. Changing
 * any of them logs every existing user out (and orphans their stored
 * state). They intentionally do NOT derive from BRAND above; the
 * inconsistent prefixes are historical and must stay.
 */
export const STORAGE_KEYS = {
  auth: "upwork-intel-auth",
  adminAuth: "persona-armory-admin-auth",
  lastProfile: "careero-last-profile",
} as const;
