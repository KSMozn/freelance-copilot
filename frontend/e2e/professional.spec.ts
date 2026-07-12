import { expect, test } from "@playwright/test";

import { STUDENT_STATE } from "./helpers";

test.describe("professional surface stays dormant", () => {
  test("unauthenticated professional routes land on login", async ({ page }) => {
    for (const route of ["/jobs", "/portfolio", "/applications", "/analytics"]) {
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test.describe("authenticated", () => {
    test.use({ storageState: STUDENT_STATE });

    test("professional routes redirect to the student wizard", async ({ page }) => {
      for (const route of ["/jobs", "/personas", "/career-fitness", "/resumes"]) {
        await page.goto(route);
        await expect(page).toHaveURL(/\/student$/);
        await expect(page.getByRole("button", { name: "Career Starter Pack" })).toBeVisible();
      }
    });
  });
});
