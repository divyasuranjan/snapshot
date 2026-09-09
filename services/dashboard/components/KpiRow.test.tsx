import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { KpiRow } from "./KpiRow";

describe("KpiRow", () => {
  it("renders formatted values when data is present", () => {
    render(
      <KpiRow totalClicks={12345} topReferrer="google.com" topCountry="United States" topBrowser="Chrome" />,
    );

    expect(screen.getByText("12,345")).toBeInTheDocument();
    expect(screen.getByText("google.com")).toBeInTheDocument();
    expect(screen.getByText("United States")).toBeInTheDocument();
    expect(screen.getByText("Chrome")).toBeInTheDocument();
  });

  it("falls back to an em dash for missing values instead of blank or null text", () => {
    render(<KpiRow totalClicks={null} topReferrer={null} topCountry={null} topBrowser={null} />);

    expect(screen.getAllByText("—")).toHaveLength(4);
  });
});
