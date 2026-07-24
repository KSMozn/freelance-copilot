import {
  AsYouType,
  getCountries,
  getCountryCallingCode,
  getExampleNumber,
  isSupportedCountry,
  isValidPhoneNumber,
  parsePhoneNumberFromString,
  validatePhoneNumberLength,
  type CountryCode,
} from "libphonenumber-js";
import examples from "libphonenumber-js/examples.mobile.json";

export type { CountryCode };

export interface CountryOption {
  iso: CountryCode;
  name: string;
  callingCode: string;
  flag: string;
}

export interface PhoneValue {
  country: CountryCode;
  callingCode: string;
  nationalNumber: string;
  internationalNumber: string;
  e164: string;
  isValid: boolean;
  stored: string;
}

export type PhoneValidity =
  | { ok: true }
  | {
      ok: false;
      reason: "required" | "too_short" | "too_long" | "invalid";
      message: string;
    };

export const digitsOnly = (value: string): string => value.replace(/[^\d]/g, "");

export function flagEmoji(iso: string): string {
  const code = iso.toUpperCase();
  if (!/^[A-Z]{2}$/.test(code)) return "\u{1F3F3}"; // white flag fallback
  const base = 0x1f1e6; // Regional Indicator Symbol Letter A
  return String.fromCodePoint(base + (code.charCodeAt(0) - 65), base + (code.charCodeAt(1) - 65));
}

function safeRegionName(displayNames: Intl.DisplayNames | undefined, iso: string): string {
  try {
    return displayNames?.of(iso) ?? iso;
  } catch {
    return iso;
  }
}

const optionsCache = new Map<string, CountryOption[]>();

export function getCountryOptions(locale?: string): CountryOption[] {
  const key = locale ?? "default";
  const cached = optionsCache.get(key);
  if (cached) return cached;

  let displayNames: Intl.DisplayNames | undefined;
  try {
    displayNames = new Intl.DisplayNames(locale ? [locale] : undefined, {
      type: "region",
    });
  } catch {
    displayNames = undefined;
  }

  const options = getCountries()
    .map<CountryOption>((iso) => ({
      iso,
      name: safeRegionName(displayNames, iso),
      callingCode: getCountryCallingCode(iso),
      flag: flagEmoji(iso),
    }))
    .sort((a, b) => a.name.localeCompare(b.name, locale));

  optionsCache.set(key, options);
  return options;
}
export function getCountryName(iso: CountryCode, locale?: string): string {
  return getCountryOptions(locale).find((o) => o.iso === iso)?.name ?? iso;
}

export function countryFromLocation(
  value: string | null | undefined,
  locale?: string,
): CountryCode | undefined {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return undefined;
  const byName = getCountryOptions(locale).find(
    (o) => o.name.toLowerCase() === trimmed.toLowerCase(),
  );
  if (byName) return byName.iso;
  const upper = trimmed.toUpperCase();
  return isSupportedCountry(upper) ? (upper as CountryCode) : undefined;
}

export function countryFromPhone(stored: string | null | undefined): CountryCode | undefined {
  const trimmed = (stored ?? "").trim();
  if (!trimmed) return undefined;
  return parsePhoneNumberFromString(trimmed)?.country;
}

export function matchesCountryQuery(option: CountryOption, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const bare = q.replace(/^\+/, "");
  return (
    option.name.toLowerCase().includes(q) ||
    option.iso.toLowerCase().includes(q) ||
    (bare.length > 0 && option.callingCode.includes(bare))
  );
}

function regionFromLocale(explicit?: string): CountryCode | undefined {
  const tags = explicit
    ? [explicit]
    : typeof navigator !== "undefined"
      ? [...(navigator.languages ?? []), navigator.language].filter(Boolean)
      : [];
  for (const tag of tags) {
    try {
      const region = new Intl.Locale(tag).maximize().region;
      if (region && isSupportedCountry(region)) return region as CountryCode;
    } catch {
      // Skip malformed tags.
    }
  }
  return undefined;
}

export function detectDefaultCountry(
  saved: string | null | undefined,
  fallback: CountryCode = "US",
  locale?: string,
): CountryCode {
  if (saved) {
    const parsed = parsePhoneNumberFromString(saved.trim());
    if (parsed?.country) return parsed.country;
  }
  return regionFromLocale(locale) ?? fallback;
}

export function parseStoredPhone(
  stored: string | null | undefined,
  fallbackCountry: CountryCode,
): { country: CountryCode; national: string } {
  const trimmed = (stored ?? "").trim();
  if (!trimmed) return { country: fallbackCountry, national: "" };

  const parsed = parsePhoneNumberFromString(trimmed);
  if (parsed) {
    return {
      country: parsed.country ?? fallbackCountry,
      national: digitsOnly(parsed.formatNational()),
    };
  }

  const asYouType = new AsYouType(fallbackCountry);
  asYouType.input(trimmed);
  const partial = asYouType.getNumber();
  return {
    country: partial?.country ?? asYouType.country ?? fallbackCountry,
    national: partial?.nationalNumber ?? digitsOnly(trimmed),
  };
}

export function formatNational(country: CountryCode, input: string): string {
  return new AsYouType(country).input(digitsOnly(input));
}

export function parseInternationalInput(
  raw: string,
  fallbackCountry: CountryCode,
): { country: CountryCode; national: string } | null {
  const trimmed = raw.trim();
  const asYouType = new AsYouType(fallbackCountry);
  asYouType.input(trimmed);
  const partial = asYouType.getNumber();
  const country =
    asYouType.country ?? partial?.country ?? parsePhoneNumberFromString(trimmed)?.country;
  if (!country) return null;
  const parsed = partial ?? parsePhoneNumberFromString(trimmed);
  return { country, national: parsed ? digitsOnly(parsed.formatNational()) : "" };
}

export function describePhone(country: CountryCode, nationalInput: string): PhoneValue {
  const callingCode = getCountryCallingCode(country);
  const digits = digitsOnly(nationalInput);

  if (!digits) {
    return {
      country,
      callingCode,
      nationalNumber: "",
      internationalNumber: "",
      e164: "",
      isValid: false,
      stored: "",
    };
  }

  const parsed = parsePhoneNumberFromString(digits, country);
  if (parsed) {
    const valid = parsed.isValid();
    return {
      country: parsed.country ?? country,
      callingCode,
      nationalNumber: parsed.nationalNumber,
      internationalNumber: parsed.formatInternational(),
      e164: valid ? parsed.number : "",
      isValid: valid,
      stored: parsed.number, // canonical E.164, round-trips even when not yet valid
    };
  }

  return {
    country,
    callingCode,
    nationalNumber: digits,
    internationalNumber: `+${callingCode} ${formatNational(country, digits)}`.trim(),
    e164: "",
    isValid: false,
    stored: `+${callingCode}${digits}`,
  };
}

export function validatePhone(
  country: CountryCode,
  nationalInput: string,
  required: boolean,
): PhoneValidity {
  const digits = digitsOnly(nationalInput);
  if (!digits) {
    return required
      ? { ok: false, reason: "required", message: "Please enter a phone number." }
      : { ok: true };
  }

  const lengthIssue = validatePhoneNumberLength(digits, country);
  if (lengthIssue === "TOO_SHORT" || lengthIssue === "INVALID_LENGTH") {
    return { ok: false, reason: "too_short", message: "Phone number is too short." };
  }
  if (lengthIssue === "TOO_LONG") {
    return { ok: false, reason: "too_long", message: "Phone number is too long." };
  }
  if (isValidPhoneNumber(digits, country)) {
    return { ok: true };
  }
  return {
    ok: false,
    reason: "invalid",
    message: "This phone number is not valid for the selected country.",
  };
}

export function getExamplePlaceholder(country: CountryCode): string {
  try {
    return getExampleNumber(country, examples)?.formatNational() ?? "";
  } catch {
    return "";
  }
}
