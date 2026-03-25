import { test, expect } from "@playwright/test";

test.describe("Import-Wizard Seite", () => {
  test("ist über /import erreichbar", async ({ page }) => {
    await page.goto("/import");
    await expect(page.locator("h1")).toContainText("Import-Wizard");
  });

  test("zeigt drei Tabs (Jira, GitHub, Confluence)", async ({ page }) => {
    await page.goto("/import");
    await expect(page.getByText("Jira")).toBeVisible();
    await expect(page.getByText("GitHub")).toBeVisible();
    await expect(page.getByText("Confluence")).toBeVisible();
  });

  test("zeigt 'nicht verbunden' wenn keine Integration aktiv", async ({ page }) => {
    await page.goto("/import");
    // Default-Tab sollte einen Hinweis zeigen
    await expect(page.getByText("nicht verbunden")).toBeVisible();
    await expect(page.getByText("Zu den Einstellungen")).toBeVisible();
  });

  test("Tab-Wechsel funktioniert", async ({ page }) => {
    await page.goto("/import");
    await page.getByText("GitHub").click();
    // GitHub-Tab sollte aktiv sein
    await expect(page.getByText("GitHub")).toBeVisible();

    await page.getByText("Confluence").click();
    await expect(page.getByText("Confluence")).toBeVisible();
  });
});

test.describe("Sidebar Navigation", () => {
  test("Import-Link in der Sidebar vorhanden", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("aside");
    await expect(sidebar.getByText("Import")).toBeVisible();
  });

  test("Import-Link navigiert zu /import", async ({ page }) => {
    await page.goto("/");
    await page.locator("aside").getByText("Import").click();
    await expect(page).toHaveURL(/\/import/);
    await expect(page.locator("h1")).toContainText("Import-Wizard");
  });
});

test.describe("Einstellungen-Link", () => {
  test("Import-Wizard Link in Einstellungen sichtbar", async ({ page }) => {
    await page.goto("/einstellungen");
    await expect(page.getByText("Import-Wizard")).toBeVisible();
  });

  test("Import-Wizard Link navigiert zu /import", async ({ page }) => {
    await page.goto("/einstellungen");
    await page.getByText("Import-Wizard").click();
    await expect(page).toHaveURL(/\/import/);
  });
});
