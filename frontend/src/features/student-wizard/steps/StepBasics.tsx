import { useEffect, useMemo, useState } from "react";

import { useAuthStore } from "@/features/auth/authStore";
import { useCoachEmail } from "@/features/student-wizard/coaching/coachingApi";
import { CoachWarnings } from "@/features/student-wizard/coaching/CoachWarnings";
import type {
  CoachSuggestion,
  CoachWarning,
} from "@/features/student-wizard/coaching/coachingTypes";
import { DateOfBirthPicker } from "@/features/student-wizard/DateOfBirthPicker";
import { useStudentProfile, useUpdateStudentProfile } from "@/features/student-wizard/studentApi";
import type { StudentProfileUpdate } from "@/features/student-wizard/studentTypes";
import { useAutoSave } from "@/shared/hooks/useAutoSave";
import {
  getCitiesForCountry,
  parseStoredLocation,
  serializeLocation,
  validateLocation,
  type GeoCity,
  type LocationValue,
} from "@/shared/lib/geo";
import { countryFromPhone, getCountryName, type CountryCode } from "@/shared/lib/phone";
import { Button } from "@/shared/ui/button";
import { CitySelect } from "@/shared/ui/city-select";
import { CountrySelect } from "@/shared/ui/country-select";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PhoneInput } from "@/shared/ui/phone-input";

import { validateEmail } from "./basicsSchema";

function splitName(full: string): { first: string; last: string } {
  const [first = "", ...rest] = full.trim().split(/\s+/).filter(Boolean);
  return { first, last: rest.join(" ") };
}

function joinName(first: string, last: string): string {
  return [first.trim(), last.trim()].filter(Boolean).join(" ");
}

export function StepBasics({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();
  const coachEmail = useCoachEmail();
  const authUser = useAuthStore((s) => s.user);

  const initialName = splitName(profile?.full_name ?? authUser?.full_name ?? "");
  const initialLocation = parseStoredLocation(profile?.location);
  const [firstName, setFirstName] = useState(initialName.first);
  const [lastName, setLastName] = useState(initialName.last);
  const [email, setEmail] = useState(profile?.professional_email ?? authUser?.email ?? "");
  const [phone, setPhone] = useState(profile?.phone ?? "");
  const [country, setCountry] = useState<CountryCode | "">(initialLocation.countryCode);
  const [cityName, setCityName] = useState(initialLocation.cityName);
  const [city, setCity] = useState<GeoCity | null>(null);
  const [cities, setCities] = useState<GeoCity[] | null>(null);
  const [locationTouched, setLocationTouched] = useState(false);
  const [dob, setDob] = useState<string | null>(profile?.date_of_birth ?? null);
  const [emailWarnings, setEmailWarnings] = useState<CoachWarning[]>([]);
  const [emailSuggestions, setEmailSuggestions] = useState<CoachSuggestion[]>([]);
  const [emailConfirmed, setEmailConfirmed] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);

  useEffect(() => {
    if (!profile) return;
    const seeded = splitName(profile.full_name || authUser?.full_name || "");
    const loc = parseStoredLocation(profile.location);
    setFirstName((current) => current || seeded.first);
    setLastName((current) => current || seeded.last);
    setEmail((current) => current || profile.professional_email || authUser?.email || "");
    setPhone((current) => current || profile.phone || "");
    setCountry((current) => current || loc.countryCode);
    setCityName((current) => current || loc.cityName);
    setDob((current) => current || profile.date_of_birth || null);
  }, [profile?.user_id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!country) {
      setCities(null);
      return;
    }
    let cancelled = false;
    void getCitiesForCountry(country).then((list) => {
      if (cancelled) return;
      setCities(list);
      setCity((current) => {
        if (current && current.country === country) return current;
        if (!cityName) return null;
        const match = list.find((c) => c.name.toLowerCase() === cityName.trim().toLowerCase());
        return match ?? { name: cityName, country };
      });
    });
    return () => {
      cancelled = true;
    };
  }, [country]); // eslint-disable-line react-hooks/exhaustive-deps

  const fullName = joinName(firstName, lastName);

  const locationValue: LocationValue = useMemo(() => {
    let cityValue: GeoCity | null = null;
    if (country && cityName) {
      cityValue =
        city && city.country === country && city.name === cityName
          ? city
          : { name: cityName, country };
    }
    return {
      country: country ? { code: country, name: getCountryName(country) } : null,
      city: cityValue,
    };
  }, [country, cityName, city]);
  const serializedLocation = serializeLocation(locationValue);
  const locationValidity = validateLocation(locationValue, cities, { required: true });
  const locationError = locationValidity.ok ? null : locationValidity;
  const countryError = locationTouched && locationError?.field === "country";
  const cityError =
    locationTouched && (locationError?.field === "city" || locationError?.field === "mismatch");

  useAutoSave(
    { firstName, lastName, email, phone, location: serializedLocation, dob },
    async ({ firstName, lastName, email, phone, location, dob }) => {
      const payload: StudentProfileUpdate = {
        full_name: joinName(firstName, lastName) || null,
        professional_email: email || null,
        phone: phone || null,
        location,
        date_of_birth: dob,
      };
      await update.mutateAsync(payload);
    },
  );

  const phoneCountry = countryFromPhone(phone);
  const countryMismatch = Boolean(country && phoneCountry && phoneCountry !== country);
  const emailFormatError = validateEmail(email);

  function handleCountryChange(iso: CountryCode) {
    setCountry(iso);
    setCity(null);
    setCityName("");
  }

  function handleCountryClear() {
    setCountry("");
    setCity(null);
    setCityName("");
  }

  function handleCityChange(next: GeoCity | null) {
    setCity(next);
    setCityName(next?.name ?? "");
  }

  async function checkEmail(): Promise<CoachWarning[]> {
    if (!email.trim() || emailFormatError) return [];
    const res = await coachEmail.mutateAsync({ email, full_name: fullName });
    setEmailWarnings(res.warnings);
    setEmailSuggestions(res.suggestions);
    return res.warnings;
  }

  async function saveAndContinue() {
    if (emailFormatError) return;
    let warnings = emailWarnings;
    if (!emailConfirmed && warnings.length === 0 && email) {
      warnings = await checkEmail();
    }
    if (warnings.some((warning) => warning.severity === "block")) return;
    if (warnings.length > 0 && !emailConfirmed) return;
    if (countryMismatch) return;
    if (!locationValidity.ok) {
      setLocationTouched(true);
      return;
    }
    await update.mutateAsync({
      full_name: fullName || null,
      professional_email: email || null,
      phone: phone || null,
      location: serializedLocation,
      date_of_birth: dob,
    });
    await onSaved();
  }

  const hasBlocker = emailWarnings.some((w) => w.severity === "block");

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="b-firstname">First name</Label>
          <Input
            id="b-firstname"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Jane"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="b-lastname">Last name</Label>
          <Input
            id="b-lastname"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Student"
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="b-email">Email shown on your CV</Label>
        <Input
          id="b-email"
          type="email"
          value={email}
          aria-invalid={emailTouched && emailFormatError ? true : undefined}
          aria-describedby={emailTouched && emailFormatError ? "b-email-error" : undefined}
          onChange={(e) => {
            setEmail(e.target.value);
            setEmailConfirmed(false);
            setEmailWarnings([]);
            setEmailSuggestions([]);
          }}
          onBlur={() => {
            setEmailTouched(true);
            void checkEmail();
          }}
          placeholder="jane.student@school.edu"
        />
        {emailTouched && emailFormatError && (
          <p id="b-email-error" role="alert" className="text-xs text-destructive">
            {emailFormatError}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Pre-filled with your sign-in email
          {authUser?.email ? ` (${authUser.email})` : ""}. Edit if you'd rather use a school
          address.
        </p>
        <CoachWarnings
          warnings={emailWarnings}
          suggestions={emailSuggestions}
          onApplySuggestion={(v) => {
            setEmail(v);
            setEmailWarnings([]);
            setEmailSuggestions([]);
          }}
        />
        {emailWarnings.length > 0 && !hasBlocker && (
          <label className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={emailConfirmed}
              onChange={(e) => setEmailConfirmed(e.target.checked)}
            />
            I know, keep this email anyway.
          </label>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="b-phone">Phone</Label>
          <PhoneInput
            id="b-phone"
            value={phone}
            onChange={(stored) => setPhone(stored)}
            fallbackCountry="SA"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="b-country">Country</Label>
          <CountrySelect
            id="b-country"
            value={country}
            onChange={handleCountryChange}
            onClear={handleCountryClear}
            clearable
            invalid={countryError}
            showCallingCode={false}
            placeholder="Select country"
          />
          {countryError && locationError && (
            <p id="b-country-error" role="alert" className="text-xs text-destructive">
              {locationError.message}
            </p>
          )}
        </div>
      </div>
      {countryMismatch && phoneCountry && (
        <p
          role="alert"
          className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-destructive"
        >
          <span>
            Your phone number is a {getCountryName(phoneCountry)} number, but your country is
            {country ? getCountryName(country) : ""}.
          </span>
          <button
            type="button"
            className="font-medium underline underline-offset-2 hover:no-underline"
            onClick={() => handleCountryChange(phoneCountry)}
          >
            Change country to {getCountryName(phoneCountry)}
          </button>
        </p>
      )}
      <div className="space-y-2">
        <Label htmlFor="b-city">City</Label>
        <CitySelect
          id="b-city"
          country={country}
          value={cityName}
          onChange={handleCityChange}
          invalid={cityError}
        />
        {cityError && locationError ? (
          <p id="b-city-error" role="alert" className="text-xs text-destructive">
            {locationError.message}
          </p>
        ) : (
          !country && (
            <p className="text-xs text-muted-foreground">Select a country to choose your city.</p>
          )
        )}
      </div>
      <div className="space-y-2">
        <Label>Date of birth</Label>
        <DateOfBirthPicker value={dob} onChange={setDob} />
        <p className="text-xs text-muted-foreground">
          Shown in the CV header next to your contact details.
        </p>
      </div>
      <div>
        <Button
          onClick={() => void saveAndContinue()}
          disabled={
            update.isPending ||
            hasBlocker ||
            countryMismatch ||
            (emailWarnings.length > 0 && !emailConfirmed)
          }
        >
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}
