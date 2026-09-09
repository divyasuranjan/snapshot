import { afterEach, describe, expect, it, vi } from "vitest";
import { getDevices, getGeo, getReferrers, getTimeseries, rangeToParams } from "./api";

describe("rangeToParams", () => {
  it("maps 24h to hourly buckets over 24 hours", () => {
    expect(rangeToParams("24h")).toEqual({ interval: "hour", hours: 24 });
  });

  it("maps 7d to daily buckets over 168 hours", () => {
    expect(rangeToParams("7d")).toEqual({ interval: "day", hours: 168 });
  });

  it("maps 30d to daily buckets over 720 hours", () => {
    expect(rangeToParams("30d")).toEqual({ interval: "day", hours: 720 });
  });
});

describe("stats fetchers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns ok:true with the parsed body on a 200", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ hours: 24, series: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getTimeseries("24h");

    expect(result).toEqual({ ok: true, data: { hours: 24, series: [] } });
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/stats/timeseries?interval=hour&hours=24");
  });

  it("returns ok:false on a non-2xx response, without throwing", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));

    const result = await getReferrers("7d");

    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toContain("503");
  });

  it("returns ok:false when the network request itself fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("ECONNREFUSED")));

    const result = await getDevices("30d");

    expect(result.ok).toBe(false);
  });

  it("passes limit and city_limit query params through", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    vi.stubGlobal("fetch", fetchMock);

    await getGeo("24h", 15);

    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("city_limit=15");
  });
});
