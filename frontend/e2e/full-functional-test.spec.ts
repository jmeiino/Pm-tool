import { test, expect } from "@playwright/test";

test.describe("1. Seitennavigation", () => {
  const pages = [
    { name: "Dashboard", path: "/", heading: "Dashboard" },
    { name: "Projekte", path: "/projekte", heading: "Projekte" },
    { name: "Aufgaben", path: "/todos", heading: "Aufgaben" },
    { name: "Tagesplan", path: "/planung/tagesplan", heading: "Tagesplan" },
    { name: "Wochenplan", path: "/planung/wochenplan", heading: "Wochenplan" },
    { name: "GitHub", path: "/github", heading: "GitHub" },
    { name: "Agents", path: "/agents", heading: "Agentische Firma" },
    { name: "Import", path: "/import", heading: "Import" },
    { name: "Einstellungen", path: "/einstellungen", heading: "Einstellungen" },
  ];

  for (const p of pages) {
    test(`${p.name} (${p.path}) ist erreichbar`, async ({ page }) => {
      await page.goto(p.path);
      await expect(page.getByRole("heading", { name: p.heading })).toBeVisible();
    });
  }
});

test.describe("2. Sidebar Navigation", () => {
  test("alle Links vorhanden und klickbar", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("aside");
    const links = [
      "Dashboard", "Projekte", "Aufgaben", "Tagesplan", "Wochenplan",
      "Confluence", "GitHub", "Agents", "Import", "Kalender", "Einstellungen",
    ];
    for (const name of links) {
      await expect(sidebar.getByRole("link", { name })).toBeVisible();
    }
  });

  test("Sidebar-Klick navigiert korrekt", async ({ page }) => {
    await page.goto("/");
    await page.locator("aside").getByRole("link", { name: "Projekte" }).click();
    await expect(page).toHaveURL(/\/projekte/, { timeout: 10000 });
    await page.locator("aside").getByRole("link", { name: "Aufgaben" }).click();
    await expect(page).toHaveURL(/\/todos/, { timeout: 10000 });
  });
});

test.describe("3. Dashboard", () => {
  test("zeigt Metriken-Karten", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Offene Aufgaben")).toBeVisible();
    await expect(page.getByText("Aktive Projekte")).toBeVisible();
    await expect(page.getByText("Heute geplant")).toBeVisible();
    await expect(page.getByText("Überfällig")).toBeVisible();
  });

  test("zeigt Heutige Aufgaben und Projekte Sektionen", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Heutige Aufgaben" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Projekte" })).toBeVisible();
  });

  test("KI-Tagesplan Button vorhanden", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: /KI-Tagesplan/i })).toBeVisible();
  });
});

test.describe("4. Projekte", () => {
  test("zeigt Projekt-Liste mit erstelltem Projekt", async ({ page }) => {
    await page.goto("/projekte");
    await expect(page.getByText("Funktionstest-Projekt")).toBeVisible();
  });

  test("Neues Projekt Dialog öffnet sich", async ({ page }) => {
    await page.goto("/projekte");
    await page.getByRole("button", { name: /Neues Projekt/i }).click();
    await expect(page.getByRole("heading", { name: "Neues Projekt" })).toBeVisible();
  });

  test("Projekt-Detail ist erreichbar", async ({ page }) => {
    await page.goto("/projekte");
    await page.getByText("Funktionstest-Projekt").first().click();
    await expect(page).toHaveURL(/\/projekte\/\d+/, { timeout: 10000 });
    await expect(page.getByRole("button", { name: /Issues/ })).toBeVisible();
  });
});

test.describe("5. Aufgaben", () => {
  test("zeigt Aufgaben-Liste", async ({ page }) => {
    await page.goto("/todos");
    await expect(page.getByText("Funktionstest-Aufgabe")).toBeVisible();
  });

  test("Neue Aufgabe Dialog öffnet sich", async ({ page }) => {
    await page.goto("/todos");
    await page.getByRole("button", { name: /Neue Aufgabe/i }).click();
    await expect(page.getByRole("heading", { name: "Neue Aufgabe" })).toBeVisible();
  });
});

test.describe("6. Einstellungen", () => {
  test("Profil-Sektion vorhanden", async ({ page }) => {
    await page.goto("/einstellungen");
    await expect(page.getByRole("heading", { name: "Profil" })).toBeVisible();
    await expect(page.getByText("Vorname")).toBeVisible();
    await expect(page.getByText("Nachname")).toBeVisible();
  });

  test("KI-Provider-Sektion vorhanden", async ({ page }) => {
    await page.goto("/einstellungen");
    await expect(page.getByRole("heading", { name: "KI-Provider" })).toBeVisible();
    await expect(page.getByText("Aktiver Provider")).toBeVisible();
  });

  test("Integrationen-Sektion vorhanden", async ({ page }) => {
    await page.goto("/einstellungen");
    await expect(page.getByRole("heading", { name: "Integrationen" })).toBeVisible();
    await expect(page.getByText("Jira").first()).toBeVisible();
    await expect(page.getByText("Confluence").first()).toBeVisible();
    await expect(page.getByText("GitHub").first()).toBeVisible();
    await expect(page.getByText("Microsoft 365")).toBeVisible();
  });

  test("KI-Provider wechselbar", async ({ page }) => {
    await page.goto("/einstellungen");
    await page.getByText("Claude (Anthropic)").click();
    await expect(page.getByText("API-Key", { exact: true })).toBeVisible();
  });
});

test.describe("7. Import-Wizard", () => {
  test("Dashboard und Wizard Toggle", async ({ page }) => {
    await page.goto("/import");
    await expect(page.getByRole("button", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Import-Wizard" })).toBeVisible();
  });

  test("Wizard zeigt Tabs und nicht-verbunden Hinweis", async ({ page }) => {
    await page.goto("/import");
    await page.getByRole("button", { name: "Import-Wizard" }).click();
    await expect(page.getByText("ist nicht verbunden")).toBeVisible();
    await expect(page.getByText("Zu den Einstellungen")).toBeVisible();
  });
});

test.describe("8. Header", () => {
  test("Sync-Button vorhanden", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Synchronisieren" })).toBeVisible();
  });

  test("Benachrichtigungs-Button vorhanden", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Benachrichtigungen" })).toBeVisible();
  });

  test("Benachrichtigungs-Dropdown öffnet sich", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Benachrichtigungen" }).click();
    await expect(
      page.getByRole("heading", { name: "Benachrichtigungen" })
    ).toBeVisible();
  });
});

test.describe("9. Design System Konformität", () => {
  test("Sidebar hat dunklen Hintergrund", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("aside").first();
    const bg = await sidebar.evaluate((el) => getComputedStyle(el).backgroundColor);
    // #0A0C0F = rgb(10, 12, 15)
    expect(bg).toBe("rgb(10, 12, 15)");
  });

  test("Header hat Brand-Akzent-Linie", async ({ page }) => {
    await page.goto("/");
    const header = page.locator("header");
    const borderColor = await header.evaluate((el) => getComputedStyle(el).borderBottomColor);
    // #009EE3 = rgb(0, 158, 227)
    expect(borderColor).toBe("rgb(0, 158, 227)");
  });

  test("IBM Plex Sans Font geladen", async ({ page }) => {
    await page.goto("/");
    const font = await page.locator("body").evaluate((el) => getComputedStyle(el).fontFamily);
    expect(font).toContain("IBM Plex Sans");
  });

  test("Buttons haben Brand-Farbe", async ({ page }) => {
    await page.goto("/");
    const btn = page.getByRole("button", { name: /KI-Tagesplan/i });
    const bg = await btn.evaluate((el) => getComputedStyle(el).backgroundColor);
    // #009EE3 = rgb(0, 158, 227)
    expect(bg).toBe("rgb(0, 158, 227)");
  });
});
