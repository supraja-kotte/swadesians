// Shared helper for pages that need current weather. There is no demo
// fallback: if no location is saved, the caller gets null and shows a hint.

import { API_BASE_URL } from "../config.js";

export const LOCATION_KEY = "agriguide.location";

export function getSavedLocation() {
  try {
    const saved = JSON.parse(localStorage.getItem(LOCATION_KEY) ?? "null");
    if (saved && typeof saved.lat === "number" && typeof saved.lon === "number") {
      return saved;
    }
  } catch {
    // Invalid or blocked storage is treated as no location.
  }
  return null;
}

export async function fetchLiveWeather(crop = "") {
  const location = getSavedLocation();
  if (!location) return null;

  const params = new URLSearchParams({
    lat: String(location.lat),
    lon: String(location.lon),
  });
  if (crop) params.set("crop", crop);

  const response = await fetch(`${API_BASE_URL}/api/weather?${params.toString()}`);
  if (!response.ok) throw new Error("weather request failed");
  const data = await response.json();
  if (data.is_demo) throw new Error("demo weather is not used");
  return { ...data, placeName: location.name ?? "" };
}
