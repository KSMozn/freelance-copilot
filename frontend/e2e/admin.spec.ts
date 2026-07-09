import { expect, test } from "@playwright/test";

import { ADMIN_STATE, studentEmail } from "./helpers";

test.use({ storageState: ADMIN_STATE });

test.describe("admin console", () => {
  test("overview renders KPIs, funnel, and LLM spend", async ({ page }) => {
    await page.goto("/overview?surface=admin");
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
    await expect(page.getByText("Users", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Wizard funnel" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /LLM spend/ })).toBeVisible();
  });

  test("users table lists this run's student; search filter lives in the URL", async ({
    page,
  }) => {
    const email = studentEmail();
    await page.goto("/users?surface=admin");
    await expect(page.getByRole("cell", { name: email, exact: true })).toBeVisible();
    await page.getByRole("textbox", { name: /Search by email/ }).fill(email);
    await expect(page).toHaveURL(new RegExp(`search=`));
    await expect(page.getByRole("cell", { name: email, exact: true })).toBeVisible();
  });

  test("user detail shows actions, CV preview card, and the LLM spend card", async ({ page }) => {
    const email = studentEmail();
    await page.goto("/users?surface=admin");
    await page.getByRole("cell", { name: email, exact: true }).click();
    await expect(page.getByRole("heading", { name: email })).toBeVisible();
    await expect(page.getByRole("button", { name: "View as user" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "CV preview" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /LLM spend/ })).toBeVisible();
  });

  test("feedback, emails, templates, and activity pages all render", async ({ page }) => {
    await page.goto("/feedback?surface=admin");
    await expect(page.getByRole("heading", { name: "Feedback" })).toBeVisible();
    await page.goto("/emails?surface=admin");
    await expect(page.getByRole("heading", { name: /Email/ })).toBeVisible();
    await page.goto("/templates?surface=admin");
    await expect(page.getByRole("heading", { name: /Templates|CV templates/ })).toBeVisible();
    await page.goto("/activity?surface=admin");
    await expect(page.getByRole("heading", { name: "Activity" })).toBeVisible();
  });
});
