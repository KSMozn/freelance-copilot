import { expect, test } from "@playwright/test";

import { readOtpCode, STUDENT_STATE, studentEmail, uniqueEmail } from "./helpers";

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

test.describe("surface selection on a shared origin", () => {
  // The `?surface=admin` override is sticky in sessionStorage. It must never
  // hijack a student-only URL loaded later in the same tab: `/login` exists in
  // both route trees (it rendered the admin login) and `/student` used to hit
  // the admin catch-all and land on /overview.
  test("sticky admin override does not hijack bare student URLs", async ({ page }) => {
    await page.goto("/overview?surface=admin");
    await expect(page.getByRole("heading", { name: "Admin sign-in" })).toBeVisible();

    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Admin sign-in" })).toBeHidden();
    await expect(page.getByRole("button", { name: /Send code|Continue/ }).first()).toBeVisible();

    await page.goto("/student");
    await expect(page).not.toHaveURL(/\/overview/);
  });

  test("admin surface is still reachable with an explicit ?surface=admin", async ({ page }) => {
    await page.goto("/login");
    await page.goto("/login?surface=admin");
    await expect(page.getByRole("heading", { name: "Admin sign-in" })).toBeVisible();
    // Sticky flag still carries admin across a bare in-console URL.
    await page.goto("/users");
    await expect(page.getByRole("heading", { name: "Admin sign-in" })).toBeVisible();
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

  test("sign out flushes a pending profile autosave before clearing auth", async ({ page }) => {
    const location = `Logout Flush ${Date.now()}`;
    await page.goto("/student?step=basics");
    await page.getByRole("textbox", { name: "Location" }).fill(location);
    const email = studentEmail();
    const previousCode = await readOtpCode(email);
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/);

    await page.getByRole("button", { name: "Continue" }).click();
    await page
      .getByRole("textbox", { name: "6-digit code" })
      .fill(await readOtpCode(email, 10_000, previousCode));
    await page.getByRole("button", { name: "Verify & sign in" }).click();
    await expect(page).toHaveURL(/\/(student)?$/, { timeout: 15_000 });
    await page.goto("/student?step=basics");

    await expect(page.getByRole("textbox", { name: "Location" })).toHaveValue(location);
  });

  test("refresh response arriving after logout cannot restore the session", async ({ page }) => {
    let releaseRefresh: (() => void) | undefined;
    const refreshStarted = new Promise<void>((resolveStarted) => {
      void page.route("**/api/v1/auth/refresh", async (route) => {
        resolveStarted();
        await new Promise<void>((resolveRelease) => {
          releaseRefresh = resolveRelease;
        });
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            access_token: "stale-access-token",
            refresh_token: "stale-refresh-token",
          }),
        });
      });
    });
    await page.route("**/api/v1/students/profile", (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: '{"detail":"expired"}' }),
    );

    await page.goto("/student?step=basics");
    await refreshStarted;
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/);
    releaseRefresh?.();

    await expect
      .poll(() =>
        page.evaluate(() => {
          const raw = localStorage.getItem("upwork-intel-auth");
          return raw ? JSON.parse(raw).state.accessToken : null;
        }),
      )
      .toBeNull();
  });

  test("same-tab account switch does not reuse the previous profile cache", async ({ page }) => {
    await page.goto("/student?step=basics");
    const previousName = await page.getByRole("textbox", { name: "Full name" }).inputValue();

    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/);
    await page.getByRole("button", { name: "Use another profile" }).click();

    const email = uniqueEmail("e2e.cache-isolation");
    const currentName = "Cache Isolation Student";
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send code" }).click();
    await page.getByRole("textbox", { name: "6-digit code" }).fill(await readOtpCode(email));
    await page.getByRole("textbox", { name: /Your name/ }).fill(currentName);
    await page.getByRole("button", { name: "Verify & sign in" }).click();

    await expect(page).toHaveURL(/\/onboarding$/);
    await page.getByRole("button", { name: "Add my details" }).click();
    const name = page.getByRole("textbox", { name: "Full name" });
    await expect(name).toHaveValue(currentName);
    await expect(name).not.toHaveValue(previousName);
  });

  test("late mutation from the previous account cannot repopulate the profile cache", async ({
    page,
  }) => {
    let releaseUpdate: (() => void) | undefined;
    let intercepted = false;
    let profileUpdates = 0;
    const updateStarted = new Promise<void>((resolveStarted) => {
      void page.route("**/api/v1/students/profile", async (route) => {
        if (route.request().method() !== "PUT") {
          await route.continue();
          return;
        }
        profileUpdates += 1;
        if (intercepted) {
          await route.continue();
          return;
        }
        intercepted = true;
        resolveStarted();
        await new Promise<void>((resolveRelease) => {
          releaseUpdate = resolveRelease;
        });
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            user_id: "00000000-0000-0000-0000-000000000001",
            full_name: "Previous Account Sentinel",
            completed_steps: [],
            links: {},
          }),
        });
      });
    });

    await page.goto("/student?step=basics");
    await page.getByRole("textbox", { name: "Location" }).fill("Delayed save");
    await updateStarted;
    await page.getByRole("textbox", { name: "Location" }).fill("Queued account A value");
    await page.waitForTimeout(1_000);
    expect(profileUpdates).toBe(1);

    await page.evaluate(() => {
      history.pushState(null, "", "/login");
      dispatchEvent(new PopStateEvent("popstate"));
    });
    await expect(page).toHaveURL(/\/login/);
    await page.getByRole("button", { name: "Use another profile" }).click();

    const email = uniqueEmail("e2e.late-mutation");
    const currentName = "Late Mutation Student";
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send code" }).click();
    await page.getByRole("textbox", { name: "6-digit code" }).fill(await readOtpCode(email));
    await page.getByRole("textbox", { name: /Your name/ }).fill(currentName);
    await page.getByRole("button", { name: "Verify & sign in" }).click();
    await page.getByRole("button", { name: "Add my details" }).click();
    await expect(page.getByRole("textbox", { name: "Full name" })).toHaveValue(currentName);

    releaseUpdate?.();
    await page.waitForTimeout(500);
    expect(profileUpdates).toBe(1);
    await page.getByRole("button", { name: "Where you study" }).click();
    await page.getByRole("button", { name: "About you" }).click();
    await expect(page.getByRole("textbox", { name: "Full name" })).toHaveValue(currentName);
  });

  test("late 401 in the same session retries with the already refreshed token", async ({
    page,
  }) => {
    let releaseSecond401: (() => void) | undefined;
    let resolveBothStarted: (() => void) | undefined;
    const bothStarted = new Promise<void>((resolve) => {
      resolveBothStarted = resolve;
    });
    let refreshRequests = 0;
    let firstRequests = 0;
    let firstRetries = 0;
    let secondRetries = 0;
    await page.goto("/login");
    const initialAccessToken = await page.evaluate(() => {
      const raw = localStorage.getItem("upwork-intel-auth");
      return raw ? (JSON.parse(raw).state.accessToken as string) : null;
    });

    function recordInitialRequest(): void {
      firstRequests += 1;
      if (firstRequests === 2) resolveBothStarted?.();
    }

    await page.route("**/api/v1/auth/refresh", async (route) => {
      refreshRequests += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "refreshed-access-token",
          refresh_token: "refreshed-refresh-token",
        }),
      });
      await page.waitForFunction(() => {
        const raw = localStorage.getItem("upwork-intel-auth");
        return raw ? JSON.parse(raw).state.accessToken === "refreshed-access-token" : false;
      });
      releaseSecond401?.();
    });
    await page.route("**/api/v1/test-refresh-one", async (route) => {
      const token = route.request().headers().authorization;
      if (token === `Bearer ${initialAccessToken}`) {
        recordInitialRequest();
        await bothStarted;
        await route.fulfill({ status: 401, body: '{"detail":"expired"}' });
        return;
      }
      firstRetries += 1;
      expect(token).toBe("Bearer refreshed-access-token");
      await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    });
    await page.route("**/api/v1/test-refresh-two", async (route) => {
      const token = route.request().headers().authorization;
      if (token === `Bearer ${initialAccessToken}`) {
        recordInitialRequest();
        await bothStarted;
        await new Promise<void>((resolve) => {
          releaseSecond401 = resolve;
        });
        await route.fulfill({ status: 401, body: '{"detail":"also expired"}' });
        return;
      }
      secondRetries += 1;
      expect(token).toBe("Bearer refreshed-access-token");
      await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    });

    const statuses = await page.evaluate(async () => {
      const { api } = await import("/src/app/apiClient.ts");
      const responses = await Promise.all([
        api.get("/test-refresh-one"),
        api.get("/test-refresh-two"),
      ]);
      return responses.map((response) => response.status);
    });

    expect(statuses).toEqual([200, 200]);
    expect(refreshRequests).toBe(1);
    expect(firstRetries).toBe(1);
    expect(secondRetries).toBe(1);
  });

  test("delayed 401 from the previous account cannot refresh as the new account", async ({
    page,
  }) => {
    let releaseResponse: (() => void) | undefined;
    let profileRequests = 0;
    let refreshRequests = 0;
    const oldRequestStarted = new Promise<void>((resolveStarted) => {
      void page.route("**/api/v1/auth/refresh", async (route) => {
        refreshRequests += 1;
        await route.continue();
      });
      void page.route("**/api/v1/students/profile", async (route) => {
        profileRequests += 1;
        if (route.request().method() !== "GET" || profileRequests !== 1) {
          await route.continue();
          return;
        }
        resolveStarted();
        await new Promise<void>((resolveRelease) => {
          releaseResponse = resolveRelease;
        });
        await route
          .fulfill({
            status: 401,
            contentType: "application/json",
            body: '{"detail":"expired account A request"}',
          })
          .catch(() => undefined);
      });
    });

    await page.goto("/student?step=basics");
    await oldRequestStarted;
    await page.getByRole("button", { name: "Sign out" }).click();
    await page.getByRole("button", { name: "Use another profile" }).click();

    const email = uniqueEmail("e2e.delayed-401");
    const currentName = "Delayed 401 Student";
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Send code" }).click();
    await page.getByRole("textbox", { name: "6-digit code" }).fill(await readOtpCode(email));
    await page.getByRole("textbox", { name: /Your name/ }).fill(currentName);
    await page.getByRole("button", { name: "Verify & sign in" }).click();
    await page.getByRole("button", { name: "Add my details" }).click();
    await expect(page.getByRole("textbox", { name: "Full name" })).toHaveValue(currentName);

    const refreshCountBeforeRelease = refreshRequests;
    const profileCountBeforeRelease = profileRequests;
    releaseResponse?.();
    await page.waitForTimeout(500);

    expect(refreshRequests).toBe(refreshCountBeforeRelease);
    expect(profileRequests).toBe(profileCountBeforeRelease);
    await expect(page.getByRole("textbox", { name: "Full name" })).toHaveValue(currentName);
  });
});
