import { test as setup, expect } from "@playwright/test";

const AUTH_FILE = "e2e/.auth/user.json";

setup("Login und Auth-State speichern", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("textbox").first().fill("default");
  await page.locator('input[type="password"]').fill("testpass123");
  await page.getByRole("button", { name: "Anmelden" }).click();

  // Warten bis Dashboard geladen ist
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({
    timeout: 15000,
  });

  // Auth-State speichern (Cookies + localStorage)
  await page.context().storageState({ path: AUTH_FILE });
});
