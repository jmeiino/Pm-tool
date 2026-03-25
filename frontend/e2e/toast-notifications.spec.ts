import { test, expect } from "@playwright/test";

test.describe("Toast Notifications", () => {
  test("Toast-Container ist im DOM vorhanden", async ({ page }) => {
    await page.goto("/import");
    // Der Toast-Container (fixed bottom-4 right-4) sollte existieren
    const toastContainer = page.locator(".fixed.bottom-4.right-4");
    await expect(toastContainer).toBeAttached();
  });
});
