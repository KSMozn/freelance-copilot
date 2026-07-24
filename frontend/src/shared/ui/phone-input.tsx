import { useEffect, useId, useRef, useState } from "react";

import { Check } from "lucide-react";

import {
  describePhone,
  detectDefaultCountry,
  digitsOnly,
  formatNational,
  getExamplePlaceholder,
  parseInternationalInput,
  parseStoredPhone,
  validatePhone,
  type CountryCode,
  type PhoneValue,
} from "@/shared/lib/phone";
import { cn } from "@/shared/lib/utils";
import { CountrySelect } from "@/shared/ui/country-select";

interface PhoneInputProps {
  value: string;
  onChange: (stored: string, meta: PhoneValue) => void;
  country?: CountryCode;
  defaultCountry?: CountryCode;
  fallbackCountry?: CountryCode;
  onValidityChange?: (valid: boolean) => void;
  error?: string;
  showErrorsWhen?: "touched" | "always";
  required?: boolean;
  disabled?: boolean;
  readOnly?: boolean;
  autoFocus?: boolean;
  id?: string;
  name?: string;
  placeholder?: string;
  locale?: string;
  "aria-label"?: string;
  className?: string;
}

export function PhoneInput({
  value,
  onChange,
  country: countryProp,
  defaultCountry,
  fallbackCountry = "US",
  onValidityChange,
  error,
  showErrorsWhen = "touched",
  required = false,
  disabled = false,
  readOnly = false,
  autoFocus = false,
  id,
  name,
  placeholder,
  locale,
  "aria-label": ariaLabel,
  className,
}: PhoneInputProps) {
  const reactId = useId();
  const baseId = id ?? reactId;
  const errorId = `${baseId}-error`;

  const numberRef = useRef<HTMLInputElement>(null);
  const lastEmitted = useRef<string | null>(null);

  const [internalCountry, setInternalCountry] = useState<CountryCode>(() => {
    const seed = parseStoredPhone(
      value,
      defaultCountry ?? detectDefaultCountry(value, fallbackCountry, locale),
    );
    return seed.country;
  });
  const country = countryProp ?? internalCountry;

  const [national, setNational] = useState<string>(() => {
    const seed = parseStoredPhone(
      value,
      defaultCountry ?? detectDefaultCountry(value, fallbackCountry, locale),
    );
    return formatNational(countryProp ?? seed.country, seed.national);
  });
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (value === lastEmitted.current) return;
    const seed = parseStoredPhone(value, defaultCountry ?? country);
    setInternalCountry(seed.country);
    setNational(formatNational(countryProp ?? seed.country, seed.national));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const prevCountry = useRef(country);
  useEffect(() => {
    if (prevCountry.current === country) return;
    prevCountry.current = country;
    setInternalCountry(country);
    setNational((prev) => formatNational(country, digitsOnly(prev)));
  }, [country]);

  const validity = validatePhone(country, national, required);

  // Report validity to the parent whenever the effective answer changes.
  useEffect(() => {
    onValidityChange?.(validity.ok);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [validity.ok]);

  function emit(nextCountry: CountryCode, nationalDigits: string) {
    const meta = describePhone(nextCountry, nationalDigits);
    lastEmitted.current = meta.stored;
    onChange(meta.stored, meta);
  }

  function handleCountryChange(iso: CountryCode) {
    const digits = digitsOnly(national);
    setInternalCountry(iso);
    setNational(formatNational(iso, digits));
    emit(iso, digits);
    numberRef.current?.focus();
  }

  function handleNationalChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;

    if (raw.trimStart().startsWith("+")) {
      const parsed = parseInternationalInput(raw, country);
      if (parsed) {
        setInternalCountry(parsed.country);
        setNational(formatNational(parsed.country, parsed.national));
        emit(parsed.country, parsed.national);
      } else {
        setNational(raw.trimStart());
      }
      return;
    }

    let digits = digitsOnly(raw);
    const prevDigits = digitsOnly(national);
    if (raw.length < national.length && digits === prevDigits && digits.length > 0) {
      digits = digits.slice(0, -1);
    }
    setNational(formatNational(country, digits));
    emit(country, digits);
  }

  const showError = (touched || showErrorsWhen === "always") && !readOnly && !validity.ok;
  const message = error ?? (showError ? (validity.ok ? undefined : validity.message) : undefined);
  const hasError = Boolean(message);
  const showSuccess =
    !hasError && touched && !readOnly && validity.ok && digitsOnly(national).length > 0;

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex">
        <CountrySelect
          value={country}
          onChange={handleCountryChange}
          variant="compact"
          disabled={disabled || readOnly}
          locale={locale}
          aria-label="Country calling code"
          triggerClassName={cn("rounded-r-none border-r-0", hasError && "border-destructive")}
        />
        <div className="relative flex-1">
          <input
            ref={numberRef}
            id={baseId}
            name={name}
            type="tel"
            inputMode="tel"
            autoComplete="tel-national"
            autoFocus={autoFocus}
            disabled={disabled}
            readOnly={readOnly}
            required={required}
            aria-label={ariaLabel ?? "Phone number"}
            aria-invalid={hasError || undefined}
            aria-describedby={hasError ? errorId : undefined}
            value={national}
            placeholder={placeholder ?? getExamplePlaceholder(country) ?? undefined}
            onChange={handleNationalChange}
            onBlur={() => setTouched(true)}
            className={cn(
              "flex h-10 w-full rounded-md rounded-l-none border border-input bg-background px-3 py-2 pr-9 text-sm",
              "ring-offset-background placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "read-only:cursor-default disabled:cursor-not-allowed disabled:opacity-50",
              hasError && "border-destructive focus-visible:ring-destructive",
            )}
          />
          {showSuccess && (
            <Check
              aria-hidden
              className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-500"
            />
          )}
        </div>
      </div>
      {message && (
        <p id={errorId} role="alert" className="text-xs text-destructive">
          {message}
        </p>
      )}
    </div>
  );
}
PhoneInput.displayName = "PhoneInput";
