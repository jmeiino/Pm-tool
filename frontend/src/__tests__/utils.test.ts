import { describe, it, expect } from "vitest";
import { cn, priorityLabels, statusLabels, formatDate } from "@/lib/utils";

describe("cn (classname merge)", () => {
  it("merges multiple class strings", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "visible")).toBe("base visible");
  });

  it("deduplicates tailwind classes", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});

describe("priorityLabels", () => {
  it("maps priority numbers to German labels", () => {
    expect(priorityLabels[1]).toBe("Dringend");
    expect(priorityLabels[2]).toBe("Hoch");
    expect(priorityLabels[3]).toBe("Mittel");
    expect(priorityLabels[4]).toBe("Niedrig");
  });
});

describe("statusLabels", () => {
  it("maps status keys to German labels", () => {
    expect(statusLabels["pending"]).toBe("Offen");
    expect(statusLabels["in_progress"]).toBe("In Bearbeitung");
    expect(statusLabels["done"]).toBe("Erledigt");
    expect(statusLabels["active"]).toBe("Aktiv");
  });
});

describe("formatDate", () => {
  it("formats ISO date string to German format", () => {
    const result = formatDate("2026-03-15T10:00:00Z");
    expect(result).toMatch(/15\.03\.2026/);
  });
});
