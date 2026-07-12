import { defineConfig, devices } from "@playwright/test";

/**
 * E2E suite against the LOCAL DEV STACK (deliberately un-mocked):
 *
 *   make up                      # postgres + backend + frontend (docker)
 *   npx playwright test          # from frontend/
 *
 * - OTP sign-in reads codes from the mock mailbox the backend writes to
 *   backend/var/dev-emails.jsonl (EMAIL_PROVIDER=mock).
 * - The admin account is created idempotently by global-setup via
 *   `docker compose exec backend python -m app.scripts.create_admin`
 *   (override with E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD).
 * - Workers = 1: auth endpoints are rate-limited per-IP and the suite
 *   shares one mailbox file — parallelism would trip 429s.
 */
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  fullyParallel: false,
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
  },
  globalSetup: "./e2e/global-setup.ts",
  projects: [
    // Authenticates once (student via OTP, admin via password) and saves
    // storage states so specs don't burn the OTP rate limit per test.
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
      dependencies: ["setup"],
    },
  ],
});
