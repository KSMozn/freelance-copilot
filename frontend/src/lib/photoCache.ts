import { api } from "@/app/apiClient";

// Cap the base64-encoded photo we cache in localStorage. The average
// student uses a headshot around 30-80 KB; anything much bigger than this
// suggests something odd (an unprocessed camera shot) — skip caching
// instead of hogging localStorage. Picker falls back to initials.
const MAX_DATA_URI_BYTES = 200 * 1024;

/**
 * Fetch the currently-signed-in student's profile photo and return it as
 * a `data:image/…;base64,…` URI. Returns null when:
 *   - the user hasn't uploaded a photo yet (404 from the endpoint);
 *   - the network call fails;
 *   - the encoded payload exceeds MAX_DATA_URI_BYTES.
 *
 * Requires the caller to already be authenticated — the endpoint is JWT
 * gated. Meant to be fired from within the wizard (post-login).
 */
export async function fetchPhotoDataUri(): Promise<string | null> {
  try {
    const res = await api.get("/students/profile/photo", {
      responseType: "blob",
      // Suppress the global toast on a 404 — no photo yet is normal.
      validateStatus: (status) => status < 500,
    });
    if (res.status === 404 || !(res.data instanceof Blob) || res.data.size === 0) {
      return null;
    }
    const dataUri = await blobToDataUri(res.data);
    if (dataUri.length > MAX_DATA_URI_BYTES) return null;
    return dataUri;
  } catch {
    return null;
  }
}

function blobToDataUri(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}
