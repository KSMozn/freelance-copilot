import { expect, test } from "@playwright/test";

import { STUDENT_STATE } from "./helpers";

test.use({ storageState: STUDENT_STATE });

test.describe("student wizard", () => {
  test("all 13 steps render with the correct save-model caption per step", async ({ page }) => {
    await page.goto("/student");
    for (const label of [
      "About you",
      "Where you study",
      "Profile photo",
      "Skills",
      "Coursework",
      "Projects",
      "Internships",
      "Volunteer work",
      "Languages",
      "Certificates",
      "Summary",
      "Preview & download",
      "Career Starter Pack",
    ]) {
      await expect(page.getByRole("button", { name: label })).toBeVisible();
    }
    // Autosave step (basics) tells the truth…
    await expect(page.getByText("Changes auto-saved")).toBeVisible();
    // …manual entry steps tell a different truth…
    await page.getByRole("button", { name: "Skills" }).click();
    await expect(page.getByText("Click save to keep your changes")).toBeVisible();
    // …and consume-only steps make no save claim.
    await page.getByRole("button", { name: "Career Starter Pack" }).click();
    await expect(page.getByText(/Step 13 of 13/)).toBeVisible();
    await expect(page.getByText(/auto-saved|Click save/)).toHaveCount(0);
  });

  test("profile autosave persists across a reload", async ({ page }) => {
    await page.goto("/student?step=basics");
    const name = page.getByRole("textbox", { name: "Full name" });
    await name.fill("E2E Autosave Check");
    // useAutoSave debounce is 700ms — give it a beat, then reload.
    await page.waitForTimeout(1500);
    await page.reload();
    await page.goto("/student?step=basics");
    await expect(page.getByRole("textbox", { name: "Full name" })).toHaveValue(
      "E2E Autosave Check",
    );
  });

  test("entry CRUD on a manual-save step", async ({ page }) => {
    await page.goto("/student?step=skills");
    await page.getByRole("textbox", { name: "Python" }).fill("Playwright");
    await page.getByRole("button", { name: "Add skill" }).click();
    await expect(page.getByText("Playwright", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Remove" }).last().click();
    await expect(page.getByText("Playwright", { exact: true })).toHaveCount(0);
  });

  test("first landing on Preview stays on Preview (auto-advance regression)", async ({ page }) => {
    // Regression: Preview auto-marks itself complete on first land; the old
    // resume effect re-fired on that change and yanked the student to the
    // Starter Pack. Resume must be hydration-only.
    await page.goto("/student");
    await page.getByRole("button", { name: "Preview & download" }).click();
    await expect(page.getByRole("heading", { name: "Preview & download" })).toBeVisible();
    // Give the auto-mark round-trip time to complete, then re-assert.
    await page.waitForTimeout(2500);
    await expect(page.getByRole("heading", { name: "Preview & download" })).toBeVisible();
    await expect(page.getByText(/Step 12 of 13/)).toBeVisible();
  });

  test("CV preview renders and DOCX downloads", async ({ page }) => {
    await page.goto("/student?step=preview");
    await expect(page.frameLocator("iframe[title='CV preview']").locator("body")).toBeVisible({
      timeout: 15_000,
    });
    await page.getByRole("button", { name: "Download CV" }).click();
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("menuitem", { name: /DOCX/ }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.docx$/);
  });
});
