import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { GeoList } from "./GeoList";

describe("GeoList", () => {
  it("renders the flag, country name, and count", () => {
    render(
      <GeoList
        countries={[{ country: "United States", country_code: "US", clicks: 42 }]}
      />,
    );

    expect(screen.getByText(/United States/)).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("🇺🇸")).toBeInTheDocument();
  });

  it("renders without a flag when country_code is missing", () => {
    render(<GeoList countries={[{ country: "Unknown", country_code: null, clicks: 5 }]} />);
    expect(screen.getByText(/Unknown/)).toBeInTheDocument();
  });
});
