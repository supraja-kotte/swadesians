// Private browser keys for equipment listings and enquiries. There is still no
// farmer login. A key never leaves this browser except in an API header or
// request body, and the server stores only its hash.

const OWNER_KEY = "agriguide.equipmentOwnerKey";
const FARMER_KEY = "agriguide.equipmentFarmerKey";
const FARMER_NAME = "agriguide.farmerName";
const FARMER_PHONE = "agriguide.farmerPhone";

function randomKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
}

function read(key) {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // The app still works for this page view if storage is blocked.
  }
  return value;
}

function getOrCreate(key) {
  const existing = read(key);
  if (existing) return existing;
  return write(key, randomKey());
}

export function ownerKey() {
  return getOrCreate(OWNER_KEY);
}

export function farmerKey() {
  return getOrCreate(FARMER_KEY);
}

export function farmerName() {
  return read(FARMER_NAME);
}

export function farmerPhone() {
  return read(FARMER_PHONE);
}

export function saveFarmerContact(name, phone) {
  write(FARMER_NAME, name);
  write(FARMER_PHONE, phone);
}
