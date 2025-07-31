// src/utils/api.js
const BASE = import.meta.env.BASE_URL || "/";

export function apiFetch(url, options = {}) {
  return fetch(`${BASE}api/${url}`, options);
}
