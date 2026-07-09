/**
 * Extract a human-readable message from an API error response.
 *
 * FastAPI returns `{ detail: string }` for handled errors, but 422
 * validation failures carry `{ detail: [{ loc, msg, type, ... }, ...] }` —
 * an ARRAY of objects. Rendering that array directly (e.g. via
 * `toast.error(detail)`) crashes React ("Objects are not valid as a React
 * child"), which is exactly what happened when an invalid email hit
 * /auth/request-code. Always funnel API errors through this helper.
 */
export function getApiErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((item) => (item && typeof item === "object" ? (item as { msg?: unknown }).msg : null))
      .filter((m): m is string => typeof m === "string");
    if (msgs.length > 0) return msgs.join(" · ");
  }
  return fallback;
}
