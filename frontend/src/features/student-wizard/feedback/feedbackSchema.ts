import { z } from "zod";

export const FEEDBACK_MESSAGE_MIN = 10;
export const FEEDBACK_MESSAGE_MAX = 4000;

export const SCREENSHOT_MAX_BYTES = 5 * 1024 * 1024; // 5 MB
export const SCREENSHOT_ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp"] as const;
export const SCREENSHOT_ACCEPT_ATTR = SCREENSHOT_ACCEPTED_TYPES.join(",");

export const feedbackDescriptionSchema = z
  .string()
  .trim()
  .min(
    FEEDBACK_MESSAGE_MIN,
    `Please describe the issue in at least ${FEEDBACK_MESSAGE_MIN} characters.`,
  )
  .max(FEEDBACK_MESSAGE_MAX, `Please keep your message under ${FEEDBACK_MESSAGE_MAX} characters.`);

export const screenshotFileSchema = z
  .instanceof(File, { message: "Choose an image file." })
  .refine((f) => (SCREENSHOT_ACCEPTED_TYPES as readonly string[]).includes(f.type), {
    message: "Screenshot must be a PNG, JPEG, or WebP image.",
  })
  .refine((f) => f.size <= SCREENSHOT_MAX_BYTES, {
    message: `Screenshot must be ${SCREENSHOT_MAX_BYTES / (1024 * 1024)} MB or smaller.`,
  });

export function validateDescription(value: string): string | null {
  const result = feedbackDescriptionSchema.safeParse(value);
  return result.success ? null : (result.error.issues[0]?.message ?? "Invalid message.");
}

export function validateScreenshot(file: File): string | null {
  const result = screenshotFileSchema.safeParse(file);
  return result.success ? null : (result.error.issues[0]?.message ?? "Invalid file.");
}
