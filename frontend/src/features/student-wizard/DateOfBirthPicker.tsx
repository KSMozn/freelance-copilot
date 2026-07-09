import { useEffect, useMemo, useState } from "react";

import { Select } from "@/shared/ui/select";

interface DateOfBirthPickerProps {
  // ISO date "YYYY-MM-DD" or null.
  value: string | null;
  onChange: (iso: string | null) => void;
  // Widest reasonable range for students. Newest year on top.
  minYearOffset?: number; // years ago the youngest picker option is
  maxYearOffset?: number; // years ago the oldest picker option is
}

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

function daysInMonth(year: number, monthOneBased: number): number {
  // JS Date trick: day 0 of next month = last day of this month.
  return new Date(year, monthOneBased, 0).getDate();
}

function parseIso(value: string | null): {
  day: string;
  month: string;
  year: string;
} {
  if (!value) return { day: "", month: "", year: "" };
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!m) return { day: "", month: "", year: "" };
  return { year: m[1], month: String(Number(m[2])), day: String(Number(m[3])) };
}

// Three-dropdown picker — no free text. Keeps partial selections in
// local state so the student can pick Day/Month/Year in any order without
// the picker forgetting earlier choices. Emits an ISO "YYYY-MM-DD" only
// when all three are set; emits null while incomplete.
export function DateOfBirthPicker({
  value,
  onChange,
  minYearOffset = 8,
  maxYearOffset = 80,
}: DateOfBirthPickerProps) {
  const currentYear = new Date().getFullYear();

  // Local state — seeded from `value` and re-seeded when a parent
  // switches to a different profile (value transitions in from outside).
  const [day, setDay] = useState<string>(() => parseIso(value).day);
  const [month, setMonth] = useState<string>(() => parseIso(value).month);
  const [year, setYear] = useState<string>(() => parseIso(value).year);

  // If the parent hands us a completed date we didn't know about (e.g.
  // profile arrived after mount), sync our local pickers. Ignore parent
  // clears while the student is mid-selection.
  useEffect(() => {
    const parsed = parseIso(value);
    if (parsed.day && parsed.month && parsed.year) {
      setDay(parsed.day);
      setMonth(parsed.month);
      setYear(parsed.year);
    }
  }, [value]);

  // Emit whenever ANY of the three change. Only commit an ISO string
  // upstream once all three are populated; otherwise emit null.
  useEffect(() => {
    if (!day || !month || !year) {
      onChange(null);
      return;
    }
    const y = Number(year);
    const m = Number(month);
    let d = Number(day);
    const cap = daysInMonth(y, m);
    if (d > cap) d = cap; // auto-clamp Feb 30 → Feb 28/29
    onChange(
      `${y.toString().padStart(4, "0")}-${m.toString().padStart(2, "0")}-${d
        .toString()
        .padStart(2, "0")}`,
    );
  }, [day, month, year]);  // eslint-disable-line react-hooks/exhaustive-deps

  const yearOptions = useMemo(() => {
    const from = currentYear - minYearOffset;
    const to = currentYear - maxYearOffset;
    const list: { value: string; label: string }[] = [{ value: "", label: "Year" }];
    for (let y = from; y >= to; y--) list.push({ value: String(y), label: String(y) });
    return list;
  }, [currentYear, minYearOffset, maxYearOffset]);

  const monthOptions = useMemo(
    () => [
      { value: "", label: "Month" },
      ...MONTHS.map((name, i) => ({ value: String(i + 1), label: name })),
    ],
    [],
  );

  const dayOptions = useMemo(() => {
    // If year + month set, cap at the real day count of that month.
    // Otherwise show 1..31; auto-clamp on emit handles the edge case.
    const y = year ? Number(year) : currentYear;
    const m = month ? Number(month) : 1;
    const cap = month ? daysInMonth(y, m) : 31;
    const list: { value: string; label: string }[] = [{ value: "", label: "Day" }];
    for (let d = 1; d <= cap; d++) list.push({ value: String(d), label: String(d) });
    return list;
  }, [year, month, currentYear]);

  return (
    <div className="grid grid-cols-3 gap-2">
      <Select
        value={day}
        onChange={(e) => setDay(e.target.value)}
        options={dayOptions}
        placeholder="Day"
      />
      <Select
        value={month}
        onChange={(e) => setMonth(e.target.value)}
        options={monthOptions}
        placeholder="Month"
      />
      <Select
        value={year}
        onChange={(e) => setYear(e.target.value)}
        options={yearOptions}
        placeholder="Year"
      />
    </div>
  );
}
