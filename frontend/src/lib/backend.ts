const DEFAULT_BACKEND_URL = "http://localhost:8000"

/**
 * Backend origin for server-only code (server functions, API routes).
 * Reads from `process.env` and is never bundled for the browser.
 */
export const BACKEND_URL =
  (typeof process !== "undefined" ? process.env.BACKEND_URL : undefined) ??
  DEFAULT_BACKEND_URL

/**
 * Backend origin for browser code. Must come from a Vite `VITE_`-prefixed
 * variable so it is statically inlined into the client bundle at build time.
 */
export const PUBLIC_BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? DEFAULT_BACKEND_URL
