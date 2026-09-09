import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReferrersList } from "./ReferrersList";

describe("ReferrersList", () => {
  it("renders each referrer with its click count", () => {
    render(
      <ReferrersList
        referrers={[
          { referrer: "google.com", clicks: 100 },
          { referrer: "Direct", clicks: 50 },
        ]}
      />,
    );

    expect(screen.getByText("google.com")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("Direct")).toBeInTheDocument();
    expect(screen.getByText("50")).toBeInTheDocument();
  });

  it("sizes bars proportionally to the largest value", () => {
    const { container } = render(
      <ReferrersList
        referrers={[
          { referrer: "google.com", clicks: 100 },
          { referrer: "twitter.com", clicks: 25 },
        ]}
      />,
    );

    const bars = container.querySelectorAll(".bg-accent");
    expect(bars).toHaveLength(2);
    expect((bars[0] as HTMLElement).style.width).toBe("100%");
    expect((bars[1] as HTMLElement).style.width).toBe("25%");
  });
});
