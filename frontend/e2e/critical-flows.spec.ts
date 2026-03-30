import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("zeigt Statistik-Karten und Projekte", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByText("Offene Aufgaben")).toBeVisible();
    await expect(page.getByText("Aktive Projekte")).toBeVisible();
    await expect(page.getByText("Heute geplant")).toBeVisible();
    await expect(page.getByText("Projekte")).toBeVisible();
  });

  test("KI-Tagesplan Button ist sichtbar", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("button", { name: /KI-Tagesplan/i })
    ).toBeVisible();
  });
});

test.describe("Projekte", () => {
  test("zeigt Projektliste mit Filter", async ({ page }) => {
    await page.goto("/projekte");
    await expect(page.getByRole("heading", { name: "Projekte" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Alle" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Aktiv" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Neues Projekt" })).toBeVisible();
  });

  test("Projekt-Detail oeffnen", async ({ page }) => {
    await page.goto("/projekte");
    const projectLink = page.locator("a[href^='/projekte/']").first();
    if (await projectLink.isVisible()) {
      await projectLink.click();
      await expect(page.getByRole("heading", { level: 2 })).toBeVisible();
    }
  });
});

test.describe("Aufgaben", () => {
  test("zeigt Aufgabenliste mit Filter", async ({ page }) => {
    await page.goto("/todos");
    await expect(page.getByRole("heading", { name: "Aufgaben" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Neue Aufgabe" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Alle" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Offen" })).toBeVisible();
    await expect(page.getByRole("button", { name: "In Bearbeitung" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Erledigt" })).toBeVisible();
  });
});

test.describe("Planung", () => {
  test("Tagesplan laedt ohne Fehler", async ({ page }) => {
    await page.goto("/planung/tagesplan");
    await expect(page.getByRole("heading", { name: "Tagesplan" })).toBeVisible();
    await expect(page.getByText("Zeitblöcke")).toBeVisible();
  });

  test("Wochenplan zeigt Wochentage", async ({ page }) => {
    await page.goto("/planung/wochenplan");
    await expect(page.getByRole("heading", { name: "Wochenplan" })).toBeVisible();
    await expect(page.getByText("Montag")).toBeVisible();
    await expect(page.getByText("Freitag")).toBeVisible();
  });
});

test.describe("Integrationen", () => {
  test("GitHub-Seite zeigt Aktivitaeten-Tabs", async ({ page }) => {
    await page.goto("/github");
    await expect(page.getByRole("heading", { name: "GitHub" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Aktivitaeten" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Repository-Analyse" })).toBeVisible();
  });

  test("Import-Seite zeigt Sync-Status", async ({ page }) => {
    await page.goto("/import");
    await expect(page.getByRole("heading", { name: "Import" })).toBeVisible();
  });

  test("Confluence-Seite laedt", async ({ page }) => {
    await page.goto("/confluence");
    await expect(page.getByRole("heading", { name: "Confluence" })).toBeVisible();
  });

  test("Kalender zeigt Wochenansicht", async ({ page }) => {
    await page.goto("/kalender");
    await expect(page.getByRole("heading", { name: "Kalender" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Woche" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Monat" })).toBeVisible();
  });
});

test.describe("Einstellungen", () => {
  test("zeigt alle Sektionen", async ({ page }) => {
    await page.goto("/einstellungen");
    await expect(page.getByRole("heading", { name: "Einstellungen" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Profil" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Passwort/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "KI-Provider" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Integrationen" })).toBeVisible();
  });
});

test.describe("Admin", () => {
  test("Dashboard zeigt Systemstatistiken", async ({ page }) => {
    await page.goto("/admin");
    await expect(page.getByRole("heading", { name: "Admin Dashboard" })).toBeVisible();
    await expect(page.getByText("Benutzer")).toBeVisible();
    await expect(page.getByText("Projekte")).toBeVisible();
  });

  test("Benutzerverwaltung zeigt Tabelle", async ({ page }) => {
    await page.goto("/admin/benutzer");
    await expect(page.getByRole("heading", { name: "Benutzerverwaltung" })).toBeVisible();
    await expect(page.getByText("Max Mustermann")).toBeVisible();
  });

  test("System zeigt Health-Status", async ({ page }) => {
    await page.goto("/admin/system");
    await expect(page.getByRole("heading", { name: /System/i })).toBeVisible();
    await expect(page.getByText("Systemstatus")).toBeVisible();
  });
});

test.describe("Navigation", () => {
  test("Sidebar enthaelt alle Links", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("nav");
    for (const label of [
      "Dashboard", "Projekte", "Aufgaben", "Tagesplan", "Wochenplan",
      "Confluence", "GitHub", "Agents", "Import", "Kalender", "Einstellungen",
    ]) {
      await expect(sidebar.getByText(label, { exact: true })).toBeVisible();
    }
  });

  test("Abmelden-Button leitet zum Login weiter", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Abmelden" }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
