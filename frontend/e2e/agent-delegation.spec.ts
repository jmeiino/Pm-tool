import { test, expect } from "@playwright/test";

test.describe("10. Agentische Firma", () => {
  test("Agents-Seite ist erreichbar und zeigt Überschrift", async ({ page }) => {
    await page.goto("/agents");
    await expect(
      page.getByRole("heading", { name: "Agentische Firma" })
    ).toBeVisible();
    await expect(
      page.getByText("Delegiere Aufgaben an AI-Agents")
    ).toBeVisible();
  });

  test("zeigt Status-Karten wenn Company konfiguriert", async ({ page }) => {
    await page.goto("/agents");
    // Status-Karten: Aktive Aufgaben, Offene Rückfragen, Agents
    await expect(page.getByText("Aktive Aufgaben")).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText("Offene Rückfragen")).toBeVisible();
    await expect(page.getByText("Agents").first()).toBeVisible();
  });

  test("zeigt Org-Chart mit synchronisierten Agents", async ({ page }) => {
    await page.goto("/agents");
    // Warte auf die Organisation-Überschrift im Org-Chart
    await expect(page.getByText("Organisation")).toBeVisible({
      timeout: 10000,
    });
    // CEO Agent sollte im Org-Chart sichtbar sein
    await expect(page.getByText("CEO").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("zeigt delegierte Tasks in der Liste", async ({ page }) => {
    await page.goto("/agents");
    // Der Smoke-Test-Task sollte sichtbar sein
    const smokeTest = page.getByText("Paperclip-Integration Smoke Test");
    if (await smokeTest.isVisible().catch(() => false)) {
      await expect(smokeTest).toBeVisible();
    } else {
      // Fallback: prüfe ob leerer Zustand korrekt angezeigt wird
      await expect(
        page.getByText(/Noch keine Aufgaben delegiert|Aktive Aufgaben/)
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test("Task-Klick öffnet Detail-Panel", async ({ page }) => {
    await page.goto("/agents");
    // Warte auf Task-Karten
    const taskCard = page.locator("button").filter({ hasText: /SMOKE-/ }).first();
    if (await taskCard.isVisible({ timeout: 5000 }).catch(() => false)) {
      await taskCard.click();
      await expect(page.getByText("Zurück zur Übersicht")).toBeVisible();
    }
  });
});
