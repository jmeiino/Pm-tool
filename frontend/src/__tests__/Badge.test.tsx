import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/Badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>Aktiv</Badge>);
    expect(screen.getByText("Aktiv")).toBeInTheDocument();
  });

  it("applies default variant classes", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default").className).toContain("bg-gray-100");
  });

  it("applies success variant", () => {
    render(<Badge variant="success">Erledigt</Badge>);
    expect(screen.getByText("Erledigt").className).toContain("bg-green-100");
  });

  it("applies danger variant", () => {
    render(<Badge variant="danger">Fehler</Badge>);
    expect(screen.getByText("Fehler").className).toContain("bg-red-100");
  });

  it("accepts additional className", () => {
    render(<Badge className="ml-2">Custom</Badge>);
    expect(screen.getByText("Custom").className).toContain("ml-2");
  });
});
