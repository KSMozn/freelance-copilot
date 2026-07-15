/**
 * Central brand constants. The product ships under two names — "Careero" for
 * the student surface, "PersonaArmory" for the company and the admin surface
 * — while the git repo and the GCP deploy identifiers still carry the
 * pre-pivot name (they are external, immutable, and out of this repo's
 * control). This file makes that drift deliberate and single-sourced instead
 * of scattered string literals.
 */
export const BRAND = {
  product: "Careero",
  company: "Careero",
  adminProduct: "Careero Admin",
  adminWordmark: "Careero · Admin",
  tagline: "Equip. Empower. Elevate.",
  adminTagline: "Signal in. Insight out.",
} as const;

export const STORAGE_KEYS = {
  auth: "upwork-intel-auth",
  adminAuth: "careero-admin-auth",
  lastProfile: "careero-last-profile",
} as const;
