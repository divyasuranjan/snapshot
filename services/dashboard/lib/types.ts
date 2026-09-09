export type TimeRange = "24h" | "7d" | "30d";

export interface TimeseriesPoint {
  bucket: string;
  clicks: number;
}

export interface TimeseriesResponse {
  interval: "hour" | "day";
  hours: number;
  series: TimeseriesPoint[];
}

export interface ReferrerRow {
  referrer: string;
  clicks: number;
}

export interface ReferrersResponse {
  hours: number;
  referrers: ReferrerRow[];
}

export interface NamedCount {
  name: string;
  clicks: number;
}

export interface DevicesResponse {
  hours: number;
  by_device: NamedCount[];
  by_browser: NamedCount[];
  by_os: NamedCount[];
}

export interface CountryRow {
  country: string;
  country_code: string | null;
  clicks: number;
}

export interface CityRow {
  city: string;
  country_code: string | null;
  lat: number;
  lon: number;
  clicks: number;
}

export interface GeoResponse {
  hours: number;
  by_country: CountryRow[];
  top_cities: CityRow[];
}

export interface CreateLinkResponse {
  code: string;
  short_url: string;
  long_url: string;
  created_at: string;
}
