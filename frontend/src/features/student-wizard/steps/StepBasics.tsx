import { useEffect, useState } from "react";

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
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

export function StepBasics({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();
  const coachEmail = useCoachEmail();
  const authUser = useAuthStore((s) => s.user);

  const [fullName, setFullName] = useState(profile?.full_name ?? authUser?.full_name ?? "");
  const [email, setEmail] = useState(profile?.professional_email ?? authUser?.email ?? "");
  const [phone, setPhone] = useState(profile?.phone ?? "");
  const [location, setLocation] = useState(profile?.location ?? "");
  const [dob, setDob] = useState<string | null>(profile?.date_of_birth ?? null);
  const [emailWarnings, setEmailWarnings] = useState<CoachWarning[]>([]);
  const [emailSuggestions, setEmailSuggestions] = useState<CoachSuggestion[]>([]);
  const [emailConfirmed, setEmailConfirmed] = useState(false);

  useEffect(() => {
    if (!profile) return;
    setFullName((current) => current || profile.full_name || authUser?.full_name || "");
    setEmail((current) => current || profile.professional_email || authUser?.email || "");
    setPhone((current) => current || profile.phone || "");
    setLocation((current) => current || profile.location || "");
    setDob((current) => current || profile.date_of_birth || null);
  }, [profile?.user_id]); // eslint-disable-line react-hooks/exhaustive-deps

  useAutoSave(
    { fullName, email, phone, location, dob },
    async ({ fullName, email, phone, location, dob }) => {
      const payload: StudentProfileUpdate = {
        full_name: fullName || null,
        professional_email: email || null,
        phone: phone || null,
        location: location || null,
        date_of_birth: dob,
      };
      try {
        await update.mutateAsync(payload);
      } catch {
        // Auto-save failures are silent; explicit Save & continue surfaces them.
      }
    },
  );

  async function checkEmail() {
    if (!email.trim()) return;
    const res = await coachEmail.mutateAsync({ email, full_name: fullName });
    setEmailWarnings(res.warnings);
    setEmailSuggestions(res.suggestions);
  }

  async function saveAndContinue() {
    if (!emailConfirmed && emailWarnings.length === 0 && email) await checkEmail();
    await update.mutateAsync({
      full_name: fullName || null,
      professional_email: email || null,
      phone: phone || null,
      location: location || null,
      date_of_birth: dob,
    });
    await onSaved();
  }

  const hasBlocker = emailWarnings.some((w) => w.severity === "block");

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="b-fullname">Full name</Label>
        <Input
          id="b-fullname"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Jane Student"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="b-email">Email shown on your CV</Label>
        <Input
          id="b-email"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setEmailConfirmed(false);
            setEmailWarnings([]);
            setEmailSuggestions([]);
          }}
          onBlur={() => void checkEmail()}
          placeholder="jane.student@school.edu"
        />
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
          <Input
            id="b-phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+966 5 …"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="b-loc">Location</Label>
          <Input
            id="b-loc"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Riyadh, SA"
          />
        </div>
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
          disabled={update.isPending || hasBlocker || (emailWarnings.length > 0 && !emailConfirmed)}
        >
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}
