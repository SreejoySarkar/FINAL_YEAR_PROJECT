import axios from "axios";
import { handle as mockHandle } from "./mockBackend";
export { API_PATHS, delay } from "./apiPaths";

/**
 * Centralised API configuration for the Django REST Framework backend.
 *
 * - Set VITE_API_BASE_URL (see .env.example) to point the app at your Django server.
 * - When VITE_API_BASE_URL is NOT set, the app runs in DEMO MODE with clearly
 *   labelled in-browser mock data (see mockBackend.js). No real votes or
 *   results exist in demo mode.
 *
 * ALL endpoint paths used by the frontend are declared in API_PATHS below.
 * If your Django url names differ, adjust them in this single place only.
 */

export const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || "").trim().replace(/\/+$/, "");
export const DEMO_MODE = !API_BASE_URL;



/* ------------------------------------------------------------------ */
/* Token handling                                                      */
/* The auth token is kept in memory and sessionStorage (NOT local-     */
/* storage, so no voting/auth data survives the browser profile).      */
/* ------------------------------------------------------------------ */
let memoryToken = sessionStorage.getItem("ev_session_token") || "";
let memoryRefreshToken = sessionStorage.getItem("ev_refresh_token") || "";

export const getToken = () => memoryToken;
export const getRefreshToken = () => memoryRefreshToken;

export const setToken = (t) => {
  memoryToken = t || "";
  if (memoryToken) sessionStorage.setItem("ev_session_token", memoryToken);
  else sessionStorage.removeItem("ev_session_token");
};

export const setRefreshToken = (t) => {
  memoryRefreshToken = t || "";
  if (memoryRefreshToken) sessionStorage.setItem("ev_refresh_token", memoryRefreshToken);
  else sessionStorage.removeItem("ev_refresh_token");
};

export const clearToken = () => {
  setToken(null);
  setRefreshToken(null);
};

/* Auth-expiry hook — wired up by AuthContext on mount. */
let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};
export const notifyUnauthorized = () => {
  if (onUnauthorized) onUnauthorized();
};

/* ------------------------------------------------------------------ */
/* Axios instance (used only when a real backend URL is configured)    */
/* ------------------------------------------------------------------ */
const api = axios.create({
  baseURL: API_BASE_URL || undefined,
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const t = getToken();
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config || {};
    if (err.response?.status === 401 && getToken() && getRefreshToken() && !original._retry) {
      original._retry = true;
      try {
        const refreshed = await axios.post(
          `${API_BASE_URL}/api/admin/token/refresh`,
          { refresh: getRefreshToken() },
          { timeout: 15000 }
        );
        setToken(refreshed.data.access);
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${refreshed.data.access}`;
        return api(original);
      } catch {
        clearToken();
        notifyUnauthorized();
      }
    } else if (err.response?.status === 401 && getToken()) {
      clearToken();
      notifyUnauthorized();
    }
    return Promise.reject(err);
  }
);

/* ------------------------------------------------------------------ */
/* request() — single entry point for every service                    */
/* ------------------------------------------------------------------ */
export async function request(path, { method = "get", data, isForm = false } = {}) {
  const hadToken = !!getToken();
  if (DEMO_MODE) {
    const { data: payload, status, error } = await mockHandle(method, path, data, getToken());
    if (error) {
      const e = new Error(error);
      e.status = status;
      if (status === 401 && hadToken) {
        clearToken();
        notifyUnauthorized();
      }
      throw e;
    }
    return payload;
  }

  try {
    const res = await api.request({
      method,
      url: path,
      data,
      headers: isForm ? { "Content-Type": "multipart/form-data" } : undefined,
    });
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
}

/* ------------------------------------------------------------------ */
/* Error helpers — friendly, safe messages (no stack traces shown)     */
/* ------------------------------------------------------------------ */
export function normalizeError(err) {
  const e = new Error(friendlyMessage(err));
  e.status = err.response ? err.response.status : err.code === "ERR_NETWORK" ? 0 : 500;
  e.raw = err;
  return e;
}

export function friendlyMessage(err) {
  if (err?.response) {
    const { status, data } = err.response;
    // DRF style errors: {detail}, {non_field_errors}, {field: [msgs]}
    if (data?.detail) return String(data.detail);
    if (data?.non_field_errors) return String(data.non_field_errors[0]);
    if (data) {
      const first = Object.values(data).find((v) => Array.isArray(v) ? v[0] : v);
      if (typeof first === "string") return first;
      if (Array.isArray(first) && first[0]) return String(first[0]);
    }
    if (status === 400) return "The server rejected the request. Please check your input.";
    if (status === 401) return "Your session has expired or the credentials were rejected. Please log in again.";
    if (status === 403) return "You do not have permission to perform this action.";
    if (status === 404) return "The requested resource was not found.";
    if (status === 409) return "This action conflicts with the current state of the election.";
    if (status >= 500) return "The voting server encountered an error. Please try again.";
  }
  if (err?.code === "ERR_NETWORK" || err?.status === 0) {
    return `Unable to reach the voting server at ${API_BASE_URL || "the configured address"}. Please check that the Django backend is running.`;
  }
  if (err?.code === "ECONNABORTED") return "The request timed out. Please try again.";
  return err?.message || "Something went wrong. Please try again.";
}

/** Some DRF list endpoints wrap items in {results: [...]} — normalise both. */
export const asList = (data) =>
  Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : Array.isArray(data?.data) ? data.data : [];

/** Small delay helper used only by the demo backend to simulate latency. */

