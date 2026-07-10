import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { expect, type Page } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "e2e.admin@example.com";
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "e2e-admin-pass-1";

/** Storage-state files written by the `setup` project, reused by specs. */
export const AUTH_DIR = path.join(__dirname, ".auth");
export const STUDENT_STATE = path.join(AUTH_DIR, "student.json");
export const ADMIN_STATE = path.join(AUTH_DIR, "admin.json");
export const STUDENT_EMAIL_FILE = path.join(AUTH_DIR, "student-email.txt");

/** The signed-in student's email for this run (specs look users up by it). */
export function studentEmail(): string {
  return fs.readFileSync(STUDENT_EMAIL_FILE, "utf-8").trim();
}

/** Path to the backend's mock-email outbox (EMAIL_PROVIDER=mock). */
export const MAILBOX = path.resolve(__dirname, "..", "..", "backend", "var", "dev-emails.jsonl");

/**
 * Unique per-run address. The OTP request limiter is 3/15min PER EMAIL, so
 * reusing a fixed address across runs trips 429s; a fresh local-part keeps
 * every run inside its own bucket. Domain must be a real-looking TLD —
 * Pydantic's EmailStr rejects reserved TLDs like `.test`.
 */
export function uniqueEmail(prefix: string): string {
  return `${prefix}.${Date.now().toString(36)}@example.com`;
}

/** Read the newest OTP code sent to `email` from the mock mailbox. */
export async function readOtpCode(email: string, timeoutMs = 10_000): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (fs.existsSync(MAILBOX)) {
      const lines = fs.readFileSync(MAILBOX, "utf-8").trim().split("\n");
      for (let i = lines.length - 1; i >= 0; i--) {
        try {
          const entry = JSON.parse(lines[i]) as { to?: string; subject?: string };
          if (entry.to === email) {
            const match = entry.subject?.match(/code: (\d{6})/);
            if (match) return match[1];
          }
        } catch {
          // partial line mid-write — retry
        }
      }
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(
    `No OTP email for ${email} in ${MAILBOX} — is the stack up (make up) with EMAIL_PROVIDER=mock?`,
  );
}

/** Read the newest password-reset token emailed to `email` from the mock mailbox. */
export async function readResetToken(email: string, timeoutMs = 10_000): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (fs.existsSync(MAILBOX)) {
      const lines = fs.readFileSync(MAILBOX, "utf-8").trim().split("\n");
      for (let i = lines.length - 1; i >= 0; i--) {
        try {
          const entry = JSON.parse(lines[i]) as { to?: string; text_body?: string };
          if (entry.to === email) {
            const match = entry.text_body?.match(/\/reset-password\?token=([A-Za-z0-9_-]+)/);
            if (match) return match[1];
          }
        } catch {
          // partial line mid-write — retry
        }
      }
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(
    `No password-reset email for ${email} in ${MAILBOX} — is the stack up (make up) with EMAIL_PROVIDER=mock?`,
  );
}

/** Full OTP sign-in for a fresh account; ends authenticated. */
export async function signInWithOtp(page: Page, email: string, fullName?: string): Promise<void> {
  await page.goto("/login");
  // A persisted lastProfile snapshot shows the returning-user picker first.
  const anotherProfile = page.getByRole("button", { name: "Use another profile" });
  if (await anotherProfile.isVisible().catch(() => false)) {
    await anotherProfile.click();
  }
  await page.getByRole("textbox", { name: "Email" }).fill(email);
  await page.getByRole("button", { name: "Send code" }).click();
  const code = await readOtpCode(email);
  await page.getByRole("textbox", { name: "6-digit code" }).fill(code);
  if (fullName) {
    await page.getByRole("textbox", { name: /Your name/ }).fill(fullName);
  }
  await page.getByRole("button", { name: "Verify & sign in" }).click();
  // New accounts land on /onboarding; returning ones on /student (or /).
  await expect(page).toHaveURL(/\/(onboarding|student)?$/, { timeout: 15_000 });
}

/** Password sign-in on the admin surface; ends on /overview. */
export async function signInAsAdmin(page: Page): Promise<void> {
  await page.goto("/login?surface=admin");
  await page.getByRole("textbox", { name: "Email" }).fill(ADMIN_EMAIL);
  await page.getByRole("textbox", { name: "Password" }).fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/overview$/, { timeout: 15_000 });
}
