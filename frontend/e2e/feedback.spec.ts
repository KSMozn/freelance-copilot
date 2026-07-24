import { expect, test } from "@playwright/test";

import { STUDENT_STATE } from "./helpers";

test.use({ storageState: STUDENT_STATE });

// A real 1x1 transparent PNG — exercises the screenshot upload path.
const PNG_1x1 = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64",
);

async function openFeedback(page: import("@playwright/test").Page) {
  await page.goto("/student");
  await page
    .getByRole("button", { name: /Send feedback/ })
    .first()
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  return dialog;
}

test.describe("feedback dialog", () => {
  test("opens as an overlay above the wizard", async ({ page }) => {
    const dialog = await openFeedback(page);
    await expect(dialog.getByRole("heading", { name: "Feedback" })).toBeVisible();
    await expect(dialog.getByRole("textbox", { name: "Describe the issue" })).toBeVisible();
  });

  test("blocks submission when the description is empty", async ({ page }) => {
    const dialog = await openFeedback(page);
    await dialog.getByRole("button", { name: "Send feedback", exact: true }).click();
    // Inline validation shows and the dialog stays open (nothing submitted).
    await expect(dialog.getByText(/at least 10 characters/i)).toBeVisible();
    await expect(dialog).toBeVisible();
  });

  test("blocks submission for a whitespace-only description", async ({ page }) => {
    const dialog = await openFeedback(page);
    await dialog.getByRole("textbox", { name: "Describe the issue" }).fill("          ");
    await dialog.getByRole("button", { name: "Send feedback", exact: true }).click();
    await expect(dialog.getByText(/at least 10 characters/i)).toBeVisible();
  });

  test("submits without a screenshot and resets the form", async ({ page }) => {
    const dialog = await openFeedback(page);
    const textarea = dialog.getByRole("textbox", { name: "Describe the issue" });
    await textarea.fill("The preview button does nothing on step six of the wizard.");
    await dialog.getByRole("button", { name: "Send feedback", exact: true }).click();
    await expect(dialog.getByText(/Submitted at/)).toBeVisible();
    await expect(textarea).toHaveValue("");
  });

  test("previews and removes an uploaded screenshot", async ({ page }) => {
    const dialog = await openFeedback(page);
    await dialog
      .locator('input[type="file"]')
      .setInputFiles({ name: "bug.png", mimeType: "image/png", buffer: PNG_1x1 });
    await expect(dialog.getByText("bug.png")).toBeVisible();
    await expect(dialog.getByRole("img", { name: /Preview of bug.png/ })).toBeVisible();

    await dialog.getByRole("button", { name: "Remove screenshot" }).click();
    await expect(dialog.getByText("bug.png")).toHaveCount(0);
    await expect(dialog.getByText(/Drag & drop or click to upload/)).toBeVisible();
  });

  test("rejects a non-image screenshot with an inline error", async ({ page }) => {
    const dialog = await openFeedback(page);
    await dialog
      .locator('input[type="file"]')
      .setInputFiles({ name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("hello") });
    await expect(dialog.getByText("Screenshot must be a PNG, JPEG, or WebP image.")).toBeVisible();
  });

  test("submits with a screenshot attached", async ({ page }) => {
    const dialog = await openFeedback(page);
    await dialog
      .getByRole("textbox", { name: "Describe the issue" })
      .fill("Layout breaks on the summary step — see the attached screenshot.");
    await dialog
      .locator('input[type="file"]')
      .setInputFiles({ name: "bug.png", mimeType: "image/png", buffer: PNG_1x1 });
    await expect(dialog.getByText("bug.png")).toBeVisible();
    await dialog.getByRole("button", { name: "Send feedback", exact: true }).click();
    await expect(dialog.getByText(/Submitted at/)).toBeVisible();
  });
});
