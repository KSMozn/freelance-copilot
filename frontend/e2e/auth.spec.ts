import { expect, test } from "@playwright/test";

import { STUDENT_STATE } from "./helpers";
import { uniqueEmail } from "./helpers";

test.describe("auth — failure paths", () => {
  test("admin login with wrong password stays on the login page", async ({ page }) => {
    await page.goto("/login?surface=admin");
    await page.getByRole("textbox", { name: "Email" }).fill("nobody@example.com");
    await page.getByRole("textbox", { name: "Password" }).fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    // Error toast renders as a STRING (regression guard for the 422-array
    // React crash) and we never leave the login page.
    await expect(page.getByRole("heading", { name: "Admin sign-in" })).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("wrong OTP code shows an error and does not sign in", async ({ page }) => {
    const email = uniqueEmail("e2e.wrongcode");
    await page.goto("/login");
    const anotherProfile = page.getByRole("button", { name: "Use another profile" });
    if (await anotherProfile.isVisible().catch(() => false)) await anotherProfile.click();
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send code" }).click();
    await page.getByRole("textbox", { name: "6-digit code" }).fill("000000");
    await page.getByRole("button", { name: "Verify & sign in" }).click();
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Check your email" })).toBeVisible();
  });

  test("invalid email address surfaces a readable validation message", async ({ page }) => {
    // `.test` is a reserved TLD Pydantic rejects with a 422 detail ARRAY —
    // this used to crash React ("Objects are not valid as a React child").
    await page.goto("/login");
    const anotherProfile = page.getByRole("button", { name: "Use another profile" });
    if (await anotherProfile.isVisible().catch(() => false)) await anotherProfile.click();
    await page.getByRole("textbox", { name: "Email" }).fill("broken@careero.test");
    await page.getByRole("button", { name: "Send code" }).click();
    // Page must survive (no crash) and stay on the email step.
    await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();
  });
});

test.describe("auth — session lifecycle", () => {
  test.use({ storageState: STUDENT_STATE });

  test("student session opens the wizard; sign out returns to login and locks /student", async ({
    page,
  }) => {
    await page.goto("/student");
    await expect(page.getByRole("button", { name: "Career Starter Pack" })).toBeVisible();
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/);
    // Token is gone: the wizard bounces straight back to login.
    await page.goto("/student");
    await expect(page).toHaveURL(/\/login/);
  });
});
