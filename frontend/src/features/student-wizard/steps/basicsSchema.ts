import { z } from "zod";

export const emailSchema = z.email();

export function validateEmail(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return emailSchema.safeParse(trimmed).success ? null : "Please enter a valid email address.";
}
