import { expect, test } from "@playwright/test";

import { ADMIN_STATE, studentEmail } from "./helpers";

test.use({ storageState: ADMIN_STATE });

test("admin impersonates a student: mint → fragment decode → wizard", async ({ page }) => {
  // Regression guard for two real decoder bugs: URLSearchParams turning
  // base64 '+' into spaces (content-dependent atob failure) and the React
  // StrictMode double-mounted effect consuming the wiped fragment on its
  // second run and bouncing to /login. The dev server runs StrictMode, so a
  // pass here covers both.
  const email = studentEmail();
  await page.goto("/users?surface=admin");
  await page.getByRole("cell", { name: email, exact: true }).click();
  await page.getByRole("button", { name: "View as user" }).click();
  await expect(page).toHaveURL(/\/student$/, { timeout: 20_000 });
  // We are the student now: the wizard header shows the impersonated email
  // (.first() — the basics step's helper text also mentions the address).
  await expect(page.getByText(email).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Career Starter Pack" })).toBeVisible();
});
