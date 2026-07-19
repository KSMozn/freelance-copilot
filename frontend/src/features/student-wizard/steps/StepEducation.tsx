import { useEffect, useState } from "react";

import { useStudentProfile, useUpdateStudentProfile } from "@/features/student-wizard/studentApi";
import {
  DEGREES,
  loadUniversities,
  MAJORS,
  UNIVERSITIES,
} from "@/features/student-wizard/studentSuggestions";
import { useAutoSave } from "@/shared/hooks/useAutoSave";
import { Button } from "@/shared/ui/button";
import { Combobox } from "@/shared/ui/combobox";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select } from "@/shared/ui/select";

export function StepEducation({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const update = useUpdateStudentProfile();

  const [university, setUniversity] = useState(profile?.college ?? "");
  const [department, setDepartment] = useState(profile?.department ?? "");
  const [degree, setDegree] = useState(profile?.degree ?? "");
  const [major, setMajor] = useState(profile?.major ?? "");
  const [startYear, setStartYear] = useState<string>(
    profile?.start_year ? String(profile.start_year) : "",
  );
  const [year, setYear] = useState<string>(
    profile?.graduation_year ? String(profile.graduation_year) : "",
  );

  const [uniOptions, setUniOptions] = useState<string[]>(UNIVERSITIES);
  const [uniLoaded, setUniLoaded] = useState(false);
  useEffect(() => {
    let cancelled = false;
    void loadUniversities().then((list) => {
      if (!cancelled) {
        setUniOptions(list);
        setUniLoaded(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!profile) return;
    setUniversity((cur) => cur || profile.college || "");
    setDepartment((cur) => cur || profile.department || "");
    setDegree((cur) => cur || profile.degree || "");
    setMajor((cur) => cur || profile.major || "");
    setStartYear((cur) => cur || (profile.start_year ? String(profile.start_year) : ""));
    setYear((cur) => cur || (profile.graduation_year ? String(profile.graduation_year) : ""));
  }, [profile?.user_id]); // eslint-disable-line react-hooks/exhaustive-deps

  useAutoSave(
    { university, department, degree, major, startYear, year },
    async ({ university, department, degree, major, startYear, year }) => {
      await update.mutateAsync({
        college: university || null,
        department: department || null,
        degree: degree || null,
        major: major || null,
        start_year: startYear ? Number(startYear) : null,
        graduation_year: year ? Number(year) : null,
      });
    },
  );

  async function saveAndContinue() {
    await update.mutateAsync({
      college: university || null,
      department: department || null,
      degree: degree || null,
      major: major || null,
      start_year: startYear ? Number(startYear) : null,
      graduation_year: year ? Number(year) : null,
    });
    await onSaved();
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>University</Label>
        <Combobox
          value={university}
          onChange={setUniversity}
          options={uniOptions}
          placeholder="Start typing…"
          maxResults={25}
        />
        {!uniLoaded && <p className="text-xs text-muted-foreground">Loading more suggestions…</p>}
      </div>
      <div className="space-y-2">
        <Label>Faculty / department (optional)</Label>
        <Input
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          placeholder="School of Engineering"
        />
      </div>
      <div className="space-y-2">
        <Label>Degree</Label>
        <Select
          value={degree}
          onChange={(e) => setDegree(e.target.value)}
          placeholder="Select a degree…"
          options={[{ value: "", label: "—" }, ...DEGREES.map((d) => ({ value: d, label: d }))]}
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Start year</Label>
          <Input
            inputMode="numeric"
            value={startYear}
            onChange={(e) => setStartYear(e.target.value.replace(/[^0-9]/g, ""))}
            placeholder="2023"
            maxLength={4}
          />
        </div>
        <div className="space-y-2">
          <Label>Graduation year</Label>
          <Input
            inputMode="numeric"
            value={year}
            onChange={(e) => setYear(e.target.value.replace(/[^0-9]/g, ""))}
            placeholder="2027"
            maxLength={4}
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label>Major</Label>
        <Combobox
          value={major}
          onChange={setMajor}
          options={MAJORS}
          placeholder="Computer Science"
        />
      </div>
      <div>
        <Button onClick={() => void saveAndContinue()} disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save & continue"}
        </Button>
      </div>
    </div>
  );
}
