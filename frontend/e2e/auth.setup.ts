import fs from "node:fs";

import { expect, test as setup } from "@playwright/test";

import {
  ADMIN_STATE,
  AUTH_DIR,
  STUDENT_EMAIL_FILE,
  STUDENT_STATE,
  signInAsAdmin,
  signInWithOtp,
  uniqueEmail,
} from "./helpers";

setup("authenticate student via OTP", async ({ page }) => {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
  const email = uniqueEmail("e2e.student");
  await signInWithOtp(page, email, "E2E Student");
  // Save step 1 once so the student PROFILE row exists — admin specs run
  // alphabetically before the wizard specs, and the user-detail CV-preview
  // card only renders for users with a profile.
  await page.goto("/student");
  await page.getByRole("textbox", { name: "Full name" }).fill("E2E Student");
  await page
    .getByRole("textbox", { name: "Email shown on your CV" })
    .fill("e2e.student@example.com");
  await page.getByRole("button", { name: "Save & continue" }).click();
  await expect(page.getByRole("heading", { name: "Where you study" })).toBeVisible({
    timeout: 15_000,
  });
  fs.writeFileSync(STUDENT_EMAIL_FILE, email);
  await page.context().storageState({ path: STUDENT_STATE });
});

setup("authenticate admin via password", async ({ page }) => {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
  await signInAsAdmin(page);
  await page.context().storageState({ path: ADMIN_STATE });
});
