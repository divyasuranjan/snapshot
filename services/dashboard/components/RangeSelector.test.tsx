import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { RangeSelector } from "./RangeSelector";

describe("RangeSelector", () => {
  it("marks the current range as active and links to the others", () => {
    render(<RangeSelector current="7d" />);

    const active = screen.getByRole("link", { name: "7d" });
    expect(active.className).toContain("bg-accent");

    const inactive = screen.getByRole("link", { name: "24h" });
    expect(inactive.className).not.toContain("bg-accent");
    expect(inactive).toHaveAttribute("href", "/?range=24h");
  });

  it("links every range to its own query param", () => {
    render(<RangeSelector current="24h" />);

    expect(screen.getByRole("link", { name: "24h" })).toHaveAttribute("href", "/?range=24h");
    expect(screen.getByRole("link", { name: "7d" })).toHaveAttribute("href", "/?range=7d");
    expect(screen.getByRole("link", { name: "30d" })).toHaveAttribute("href", "/?range=30d");
  });
});
