import { expect, test } from "@playwright/test";

import { readResetToken, signInWithOtp, uniqueEmail } from "./helpers";

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

test.describe("password reset — end to end", () => {
  test("forgot → email link → new password → old session revoked → login", async ({
    page,
    request,
  }) => {
    const email = uniqueEmail("e2e.reset");
    const newPassword = "e2e-new-password-1";

    // Create a fresh account via OTP; this IS the "old session" whose
    // refresh token must die when the password is reset.
    await signInWithOtp(page, email, "Reset Tester");
    const oldRefresh = await page.evaluate(() => {
      const raw = localStorage.getItem("upwork-intel-auth");
      return raw
        ? ((JSON.parse(raw) as { state?: { refreshToken?: string } }).state?.refreshToken ?? null)
        : null;
    });
    expect(oldRefresh).toBeTruthy();

    // From here on the auth flow must be clean: no console errors, no
    // failed /auth requests.
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    const failedAuthRequests: string[] = [];
    page.on("response", (resp) => {
      if (resp.status() >= 400 && resp.url().includes("/auth/")) {
        failedAuthRequests.push(`${resp.status()} ${resp.url()}`);
      }
    });

    // Request the reset link.
    await page.goto("/forgot-password");
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send reset link" }).click();
    await expect(page.getByRole("heading", { name: "Check your email" })).toBeVisible();

    // Dev mode surfaces the captured reset email directly — open it from the
    // UI (this is the localhost self-service path; prod shows only the
    // generic message).
    await expect(page.getByText(/captured locally/)).toBeVisible();
    await page.getByRole("button", { name: "Open reset link" }).click();
    await expect(page).toHaveURL(/\/reset-password\?token=/);
    await page.getByRole("textbox", { name: "New password", exact: true }).fill(newPassword);
    await page.getByRole("textbox", { name: "Confirm new password" }).fill(newPassword);
    await page.getByRole("button", { name: "Update password" }).click();
    await expect(page.getByRole("heading", { name: "Password updated" })).toBeVisible();

    // The pre-reset refresh token is revoked server-side.
    const refreshResp = await request.post(`${API_BASE}/auth/refresh`, {
      data: { refresh_token: oldRefresh },
    });
    expect(refreshResp.status()).toBe(401);

    // Sign in with the new password.
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/login/);
    const anotherProfile = page.getByRole("button", { name: "Use another profile" });
    if (await anotherProfile.isVisible().catch(() => false)) await anotherProfile.click();
    await page.getByRole("button", { name: "Use a password instead" }).click();
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("textbox", { name: "Password", exact: true }).fill(newPassword);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/(student|onboarding)/, { timeout: 15_000 });

    expect(consoleErrors).toEqual([]);
    expect(failedAuthRequests).toEqual([]);
  });

  test("used reset link cannot be replayed", async ({ page }) => {
    const email = uniqueEmail("e2e.replay");
    const newPassword = "e2e-replay-password-1";

    await signInWithOtp(page, email, "Replay Tester");
    await page.goto("/forgot-password");
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send reset link" }).click();
    await expect(page.getByRole("heading", { name: "Check your email" })).toBeVisible();

    const token = await readResetToken(email);
    await page.goto(`/reset-password?token=${token}`);
    await page.getByRole("textbox", { name: "New password", exact: true }).fill(newPassword);
    await page.getByRole("textbox", { name: "Confirm new password" }).fill(newPassword);
    await page.getByRole("button", { name: "Update password" }).click();
    await expect(page.getByRole("heading", { name: "Password updated" })).toBeVisible();

    // Replaying the same link must fail and stay on the form.
    await page.goto(`/reset-password?token=${token}`);
    await page.getByRole("textbox", { name: "New password", exact: true }).fill("another-pass-1");
    await page.getByRole("textbox", { name: "Confirm new password" }).fill("another-pass-1");
    await page.getByRole("button", { name: "Update password" }).click();
    await expect(page.getByRole("heading", { name: "Choose a new password" })).toBeVisible();
  });

  test("login password step links to forgot-password", async ({ page }) => {
    await page.goto("/login");
    const anotherProfile = page.getByRole("button", { name: "Use another profile" });
    if (await anotherProfile.isVisible().catch(() => false)) await anotherProfile.click();
    await page.getByRole("button", { name: "Use a password instead" }).click();
    await page.getByRole("button", { name: "Forgot password?" }).click();
    await expect(page).toHaveURL(/\/forgot-password/);
    await expect(page.getByRole("heading", { name: "Forgot your password?" })).toBeVisible();
  });

  test("reset link without a token offers to request a new one", async ({ page }) => {
    await page.goto("/reset-password");
    await expect(page.getByRole("heading", { name: "Invalid reset link" })).toBeVisible();
    await page.getByRole("button", { name: "Request a new link" }).click();
    await expect(page).toHaveURL(/\/forgot-password/);
  });

  test("dev OTP hint shows the captured code and fills it in one click", async ({ page }) => {
    // Dev-stack-only DX: the hint polls GET /dev/emails (mock provider) so
    // localhost sign-in never requires shelling into the container.
    const email = uniqueEmail("e2e.devhint");
    await page.goto("/login");
    const anotherProfile = page.getByRole("button", { name: "Use another profile" });
    if (await anotherProfile.isVisible().catch(() => false)) await anotherProfile.click();
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send code" }).click();
    // The notice + latest code render without any interaction…
    await expect(page.getByText(/captured locally/)).toBeVisible();
    await expect(page.getByText(/Latest code:/)).toBeVisible();
    // …and one click fills the input.
    await page.getByRole("button", { name: "Use code" }).click();
    await expect(page.getByRole("textbox", { name: "6-digit code" })).toHaveValue(/^\d{6}$/);
  });
});
