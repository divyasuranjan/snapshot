import { describe, expect, it } from "vitest";
import { countryFlag, formatBucketLabel, formatCount } from "./format";

describe("formatCount", () => {
  it("adds thousands separators", () => {
    expect(formatCount(1234567)).toBe("1,234,567");
  });

  it("handles zero", () => {
    expect(formatCount(0)).toBe("0");
  });
});

describe("formatBucketLabel", () => {
  it("formats hour buckets as a time", () => {
    const label = formatBucketLabel("2024-01-01T14:00:00Z", "hour");
    expect(label).toMatch(/\d{1,2}\s?(AM|PM)/);
  });

  it("formats day buckets as a short date", () => {
    const label = formatBucketLabel("2024-03-15T00:00:00Z", "day");
    expect(label).toMatch(/Mar/);
    expect(label).toMatch(/15/);
  });
});

describe("countryFlag", () => {
  it("converts a two-letter code into its regional-indicator flag", () => {
    expect(countryFlag("US")).toBe("🇺🇸");
    expect(countryFlag("gb")).toBe("🇬🇧");
  });

  it("returns empty string for missing or malformed codes", () => {
    expect(countryFlag(null)).toBe("");
    expect(countryFlag(undefined)).toBe("");
    expect(countryFlag("")).toBe("");
    expect(countryFlag("USA")).toBe("");
  });
});
