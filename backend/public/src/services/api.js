import { API_BASE_URL } from "../config.js";

// Every backend call will live in this file. Keeping them together makes it
// easy to change the server address later without touching page code.
export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return response.json();
}
