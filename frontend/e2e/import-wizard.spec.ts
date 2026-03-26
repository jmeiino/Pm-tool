import { test, expect } from "@playwright/test";

test.describe("Import-Seite", () => {
  test("ist über /import erreichbar", async ({ page }) => {
    await page.goto("/import");
    await expect(
      page.getByRole("heading", { name: "Import" })
    ).toBeVisible();
  });

  test("zeigt Dashboard und Import-Wizard Toggle", async ({ page }) => {
    await page.goto("/import");
    await expect(page.getByRole("button", { name: "Dashboard" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Import-Wizard" })
    ).toBeVisible();
  });

  test("zeigt drei Tabs im Wizard-Modus (Jira, GitHub, Confluence)", async ({
    page,
  }) => {
    await page.goto("/import");
    // Wechsel in den Wizard-Modus
    await page.getByRole("button", { name: "Import-Wizard" }).click();
    // Tab-Buttons prüfen (enthalten Icon + Label + ggf. "nicht verbunden")
    const tabBar = page.locator(".flex.gap-2.border-b");
    await expect(tabBar.getByRole("button", { name: /Jira/ })).toBeVisible();
    await expect(tabBar.getByRole("button", { name: /GitHub/ })).toBeVisible();
    await expect(tabBar.getByRole("button", { name: /Confluence/ })).toBeVisible();
  });

  test("zeigt 'nicht verbunden' im Wizard wenn keine Integration aktiv", async ({
    page,
  }) => {
    await page.goto("/import");
    await page.getByRole("button", { name: "Import-Wizard" }).click();
    await expect(page.getByText("ist nicht verbunden")).toBeVisible();
    await expect(page.getByText("Zu den Einstellungen")).toBeVisible();
  });
});

test.describe("Sidebar Navigation", () => {
  test("Import-Link in der Sidebar vorhanden", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.locator("aside").getByRole("link", { name: "Import" })
    ).toBeVisible();
  });

  test("Import-Link navigiert zu /import", async ({ page }) => {
    await page.goto("/");
    await page.locator("aside").getByRole("link", { name: "Import" }).click();
    await expect(page).toHaveURL(/\/import/);
    await expect(
      page.getByRole("heading", { name: "Import" })
    ).toBeVisible();
  });
});

test.describe("Einstellungen-Link", () => {
  test("Import-Wizard Link in Einstellungen sichtbar", async ({ page }) => {
    await page.goto("/einstellungen");
    await expect(page.getByText("Import-Wizard")).toBeVisible();
  });

  test("Import-Wizard Link navigiert zu /import", async ({ page }) => {
    await page.goto("/einstellungen");
    await page.getByText("Import-Wizard").first().click();
    await expect(page).toHaveURL(/\/import/);
  });
});
